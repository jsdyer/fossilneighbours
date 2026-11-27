"""Publish the source-linked pages for one saved PBDB edition."""
from collections import Counter, defaultdict
from html import escape
import re
from urllib.parse import urlencode
from xml.etree import ElementTree as ET


def e(text):
    return escape(str(text), quote=True)


def link(path, label):
    return f'<a href="{e(path)}">{e(label)}</a>'


def pbdb(kind, identifier):
    return f"https://paleobiodb.org/data1.2/{kind}/single.json?vocab=pbdb&id={int(identifier)}"


def age(older, younger):
    return f"{older:g} Ma" if older == younger else f"{older:g}–{younger:g} Ma"


def collection_path(identifier):
    return f"records/collections/{int(identifier)}/"


def formation_path(name):
    slug = re.sub("[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError(f"Empty formation slug for {name!r}")
    return "records/formations/" + slug + "/"


def count(n, singular, plural=None):
    return f"{n:,} {singular if n == 1 else plural or singular + 's'}"


class Edition:
    def __init__(self, data):
        self.rows = defaultdict(list)
        self.collections = {c["id"]: c for c in data["collections"]}
        self.refs = data["references"]
        self.presets = data["presets"]
        if len({formation_path(name) for name in self.presets}) != len(self.presets):
            raise ValueError("Formation page paths must be distinct")
        self.focal = {}
        self.parents = defaultdict(list)
        for formation, ids in self.presets.items():
            for cid in ids:
                self.focal[cid] = formation
                peers = self.collections[cid]["peers"]
                for peer in sorted(set(peers["age"]) | set(peers["environment"])):
                    self.parents[peer].append(cid)
        self.names = {}
        for row in sorted(data["occurrences"], key=lambda r: (r["name"].casefold(),r["id"])):
            self.rows[row["col"]].append(row)
            if row["taxon"]:
                self.names[row["taxon"]] = row["accepted"]
        self.taxa = {cid: {r["taxon"] for r in self.rows[cid] if r["taxon"]} for cid in self.collections}

    def selection(self, cid):
        if cid in self.focal:
            return {"formation": self.focal[cid], "collection": cid}
        parent = self.parents[cid][0]
        return {"formation": self.focal[parent], "collection": parent, "peer": cid}

    def source(self, refid):
        ref = self.refs[str(refid)]
        authors = " ".join(str(ref[k]) for k in ("author", "year") if ref.get(k))
        result = link(pbdb("refs", refid), authors or f"PBDB reference {refid}") + ". " + e(ref["title"])
        if re.match(r"^10\.\d{4,9}/", ref.get("doi", "")):
            result += " · " + link("https://doi.org/" + ref["doi"], "Publisher DOI")
        return result

    def links_to_collections(self, ids, root):
        cells = []
        for cid in sorted(ids, key=lambda cid: (self.collections[cid]["name"].casefold(), cid)):
            c = self.collections[cid]
            item = link(root + collection_path(cid), c["name"])
            context = " · ".join([f"PBDB {cid}", c["province"] or "Canada", age(c["old"],c["young"]), count(len(self.rows[cid]), "occurrence")])
            cells.append(f'<li>{item}<small>{e(context)}</small></li>')
        return '<ul class="profile-list">' + "".join(cells) + "</ul>"

    def formation(self, name, ids, root):
        places = [self.collections[cid] for cid in ids]
        rows = [r for cid in ids for r in self.rows[cid]]
        accepted = Counter(r["taxon"] for r in rows if r["taxon"])
        location = ", ".join(sorted({c["province"] for c in places if c["province"]}))
        bounds = age(max(c["old"] for c in places), min(c["young"] for c in places))
        title = f"{name} Formation fossil collections in {location or 'Canada'}"
        desc = (f"{count(len(ids),'collection')} assigned to {name} contain {count(len(rows),'occurrence record')} "
                f"and {count(len(accepted),'accepted taxon','accepted taxa')}. Their recorded age bounds span {bounds}.")
        opening = link(root + "?" + urlencode({"formation": name, "scope": "formation"}) + "#record-heading", f"Search the {name} occurrence records")
        body = [f'<p class="profile-intro">{e(desc)}</p><p>{opening}</p>']
        if accepted:
            names = sorted(accepted,key=lambda tid: (-accepted[tid], self.names[tid],tid))[:8]
            body.append("<h2>Frequently recorded fossil names</h2><p>Each count is the number of occurrence records assigned to the accepted PBDB taxon across these collections. Names can represent several different ranks.</p><ul>")
            for tid in names:
                body.append("<li>"+link(pbdb("taxa",tid),self.names[tid])+" · "+count(accepted[tid],"occurrence")+"</li>")
            body.append("</ul>")
        body.append("<h2>Collections in this formation</h2>"+ self.links_to_collections(ids,root))
        if name == "Joggins":
            body.append('<p>For local geological context, '+link("https://coolcode.ca/coalbelow/","explore the Joggins coal seams and historic workings in Coal Below")+'.</p>')
        return title,desc,"".join(body)

    def neighbours(self, cid, root):
        c = self.collections[cid]
        if cid in self.focal:
            neighbours = c["peers"]
            other_ids = list(dict.fromkeys(neighbours["age"] + neighbours["environment"]))
        else:
            other_ids = self.parents[cid]
        if not other_ids:
            return "<p>The snapshot contains no selected age neighbour for this collection.</p>"
        items = []
        for other_id in other_ids:
            other = self.collections[other_id]
            older, younger = min(c["old"], other["old"]), max(c["young"], other["young"])
            if older <= younger:
                raise ValueError(f"Non-overlapping peer collections {cid}, {other_id}")
            details = f"Overlap {age(older, younger)}"
            if c["env"] and c["env"] == other["env"]:
                details += " · Same PBDB environment: " + c["env"]
            items.append("<li>"+link(root+collection_path(other_id),other["name"])+"<small>"+e(details)+"</small></li>")
        return '<p>These Canadian collections from other or unnamed formations share a positive portion of the recorded age interval. The fossils may come from different times within it.</p><ul class="profile-list">'+"".join(items)+"</ul>"

    def shared_taxa(self, cid, root):
        shared = [(self.taxa[cid] & taxa, other) for other,taxa in self.taxa.items() if cid != other and self.taxa[cid] & taxa]
        if not shared:
            return ""
        shared.sort(key=lambda item: (-len(item[0]), self.collections[item[1]]["name"].casefold(), item[1]))
        body = ['<h2 id="shared">Collections sharing fossil names</h2><p>Up to three other collections in this snapshot with the most accepted PBDB taxon IDs in common. A shared name does not establish a shared age.</p><ul>']
        for taxa,other in shared[:3]:
            names = sorted(taxa,key=lambda tid: self.names[tid])
            examples = ", ".join(link(pbdb("taxa",tid),self.names[tid]) for tid in names[:3])
            body.append("<li>"+link(root+collection_path(other),self.collections[other]["name"])+f" · {count(len(taxa),'shared taxon','shared taxa')}, including "+examples+"</li>")
        return "".join(body)+"</ul>"

    def collection(self, cid, root):
        c = self.collections[cid]
        rows = self.rows[cid]
        title = f"{c['name']} · PBDB fossil collection {cid}"
        bounds = age(c["old"],c["young"])
        place = ", ".join(x for x in [c["formation"] + " Formation" if c["formation"] else "", c["province"] or "Canada"] if x)
        desc = (f"{c['name']} (PBDB {cid}), {place}. The collection spans {bounds} and has "
                f"{count(len(rows),'occurrence record')} with {count(len(self.taxa[cid]),'accepted taxon','accepted taxa')} in this PBDB edition.")
        profile = link(root + "?" + urlencode(self.selection(cid)) + "#record-heading", "Explore this collection’s occurrence records")
        summary = f"{place} · {bounds}. The snapshot includes {count(len(rows),'occurrence record')} with {count(len(self.taxa[cid]),'accepted taxon','accepted taxa')}."
        body = [f'<p class="profile-intro">{e(summary)}</p><p>{profile}</p>']
        detail = " · ".join([c["interval"],f"Environment: {c['env'] or 'unrecorded'}", f"PBDB {cid}"])
        body.append(f"<p>{e(detail)}. "+link(pbdb("colls",cid),"PBDB collection record")+".</p>")
        if cid in self.focal:
            name = self.focal[cid]
            body.append("<p>"+link(root+formation_path(name), f"All {name} Formation collections")+"</p>")
        shared = self.shared_taxa(cid,root)
        jumps = [link("#fossils","Reported fossils"),link("#neighbours","Age neighbours")]
        if shared:
            jumps.append(link("#shared","Shared fossil names"))
        jumps.append(link("#literature","Source literature"))
        body.append('<p class="profile-jumps">' + " · ".join(jumps) + "</p>")
        body.append('<h2 id="fossils">Reported fossils and accepted names</h2>')
        if rows:
            body.append("<p>The reported identification and the current accepted PBDB name may differ. Each line links to an occurrence and its cited source.</p><ul class='occurrences'>")
            for row in rows:
                accepted = link(pbdb("taxa",row["taxon"]),row["accepted"]) if row["taxon"] else "Accepted taxon ID unrecorded"
                rank = " ("+e(row["rank"])+")" if row["rank"] else ""
                citation = link("#ref-"+str(row["ref"]), f"Source {row['ref']}")
                body.append("<li><strong>"+link(pbdb("occs",row["id"]),row["name"])+"</strong><br>Accepted identification: "+accepted+rank+" · "+citation+"</li>")
            body.append("</ul>")
        else:
            body.append("<p>No occurrence records were returned for this collection in the published snapshot.</p>")
        body.append('<h2 id="neighbours">Collections with overlapping ages</h2>'+self.neighbours(cid,root))
        body.append(shared)
        body.append('<h2 id="literature">Source literature</h2><ul>')
        for rid in dict.fromkeys([c["ref"],*(r["ref"] for r in rows)]):
            body.append(f'<li id="ref-{int(rid)}">{self.source(rid)}</li>')
        body.append("</ul>")
        return title,desc,"".join(body)

    def directory(self):
        desc = (f"Browse {count(len(self.presets),'focal formation')} and {count(len(self.collections),'Canadian fossil collection')} "
                "from the Paleobiology Database, including selected collections with overlapping age intervals.")
        body=[f'<p class="profile-intro">{e(desc)}</p><h2>Start with a formation</h2><ul>']
        for name,ids in self.presets.items():
            body.append("<li>"+link("../"+formation_path(name), name+" Formation")+" · "+count(len(ids),"focal collection")+"</li>")
        body.append("</ul>")
        for name,ids in self.presets.items():
            body.append("<h2>"+e(name)+" Formation collections</h2>"+self.links_to_collections(ids,"../"))
        peers = [cid for cid in self.collections if cid not in self.focal]
        body.append("<h2>Selected Canadian age neighbours</h2>"+self.links_to_collections(peers,"../"))
        return "Canadian fossil collection and formation profiles",desc,"".join(body)


def publish_profiles(stage, data, index, tool):
    edition = Edition(data)
    if index["collections"] != len(edition.collections) or index["count"] != len(data["occurrences"]) or index["papers"] != len(edition.refs):
        raise ValueError("PBDB index and occurrence archive counts differ")
    base = "https://coolcode.ca" + tool["url"]
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    def save(path, result):
        title,description,body = result
        root = "../" * path.count("/")
        out = stage/path/"index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        canonical = base + path
        meta = f'<meta name="description" content="{e(description)}"><link rel="canonical" href="{e(canonical)}">'
        nav = link(root, "Fossil Neighbours") + link(root+"records/", "All fossil profiles")
        date = e(index["retrieved"])
        html = f'''<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · Fossil Neighbours</title>{meta}<link rel="stylesheet" href="{root}style.css">
<script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head><body data-tool="fossilneighbours" class="profile">
<a class="skip" href="#main">Skip to record</a><header><nav aria-label="Fossil Neighbours">{nav}</nav></header>
<main id="main"><h1>{e(title)}</h1>{body}
<footer><p>PBDB data retrieved {date}. Ages are in millions of years before present (Ma). These counts describe records in the published snapshot. Sampling and publication effort vary. The monthly source check is scheduled for the fifth at 07:27 UTC.</p>
{link("https://paleobiodb.org/","Paleobiology Database and contributors")} · {link(root+"records/","All fossil profiles")} · {link("https://coolcode.ca/","CoolCode.ca")}</footer></main></body></html>'''
        out.write_text(html, encoding="utf-8")
        ET.SubElement(ET.SubElement(sitemap, "url"), "loc").text = canonical

    save("records/", edition.directory())
    for name, ids in edition.presets.items():
        save(formation_path(name), edition.formation(name,ids,"../../../"))
    for cid in sorted(edition.collections):
        save(collection_path(cid), edition.collection(cid,"../../../"))
    ET.ElementTree(sitemap).write(stage/"sitemap.xml",encoding="utf-8",xml_declaration=True)
    # PBDB 28069 is the documented Coal Mine Point example. Keep the invitation
    # valid even if a future refresh drops that record or changes its identifications.
    example = 28069 if 28069 in edition.focal else next(iter(edition.focal))
    c = edition.collections[example]
    name = "Coal Mine Point" if c["name"].startswith("Coal Mine Point") else c["name"]
    invitation = link("./"+collection_path(example),f"Explore the fossils at {name}")
    years = age(c["old"],c["young"]).removesuffix(" Ma")
    context = f"{count(len(edition.rows[example]),'occurrence record')} · {years} million years ago · {edition.focal[example]} Formation"
    example_query = ""
    if any("hylonomus" in (r["name"]+" "+r["accepted"]).casefold() for r in edition.rows[example]):
        params = {**edition.selection(example), "identification": "Hylonomus"}
        example_query = " · "+link("?"+urlencode(params)+"#record-heading","Find Hylonomus in this collection")
    return f'<p class="example-name">{invitation}</p><p>{e(context)}</p><p>{link("./records/","Browse all fossil profiles")}{example_query}</p>'
