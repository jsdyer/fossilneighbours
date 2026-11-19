"""Refresh public, geographically bounded PBDB collection and occurrence records."""
from datetime import datetime, timezone
from itertools import batched
import gzip
import json
from pathlib import Path
from time import sleep
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://paleobiodb.org/data1.2/"
FORMATIONS = {"Joggins": "Nova Scotia", "Haslam": "British Columbia"}
PEER_LIMIT = 6


def records(route, **params):
    query = urlencode(dict(params, vocab="pbdb", limit="all"))
    request = Request(f"{API}{route}/list.json?{query}", headers={"User-Agent": "CoolCode-FossilNeighbours/1.0 (+https://coolcode.ca/fossilneighbours/)"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=110) as response:
                payload = json.load(response)
            if payload.get("errors") or payload.get("warnings"):
                raise ValueError(str(payload))
            return payload["records"]
        except OSError:
            if attempt == 2:
                raise
            sleep(3 * (attempt + 1))


def collection(row):
    return dict(id=int(row["collection_no"]), name=row["collection_name"],
                formation=row.get("formation", ""), province=row.get("state", ""),
                young=float(row["min_ma"]), old=float(row["max_ma"]),
                interval=" – ".join(dict.fromkeys(x for x in (row["early_interval"], row.get("late_interval")) if x)),
                env=row.get("environment", ""), ref=int(row["reference_no"]))


def overlaps(left, right):
    return min(left["old"], right["old"]) > max(left["young"], right["young"])


def neighbours(focus, candidates):
    choices = [c for c in candidates if c["formation"] != focus["formation"] and overlaps(c, focus)]
    choices.sort(key=lambda c: (abs(c["old"] - focus["old"]) + abs(c["young"] - focus["young"]), c["id"]))
    same = [c for c in choices if focus["env"] and c["env"] == focus["env"]]
    return {"age": [c["id"] for c in choices[:PEER_LIMIT]], "environment": [c["id"] for c in same[:PEER_LIMIT]]}


def make_snapshot():
    all_collections, presets = {}, {}
    for formation, province in FORMATIONS.items():
        base = {"cc": "CA", "show": "loc,strat,env"}
        local = [collection(r) for r in records("colls", formation=formation, **base) if r.get("state") == province and r.get("formation") == formation]
        if not local:
            raise ValueError(f"No collections in {formation}")
        peer_rows = records("colls", min_ma=min(c["young"] for c in local), max_ma=max(c["old"] for c in local), timerule="overlap", **base)
        candidates = [collection(r) for r in peer_rows]
        by_id = {c["id"]: c for c in candidates}
        for c in local:
            c["peers"] = neighbours(c, candidates)
            for group in c["peers"].values():
                all_collections.update((i, by_id[i]) for i in group)
        all_collections.update((c["id"], c) for c in local)
        presets[formation] = [c["id"] for c in local]
    occurrences = {}
    for batch in batched(sorted(all_collections), 70):
        for row in records("occs", coll_id=",".join(map(str, batch))):
            item = dict(id=int(row["occurrence_no"]), col=int(row["collection_no"]), name=row["identified_name"],
                        accepted=row.get("accepted_name", ""), taxon=int(row.get("accepted_no") or 0),
                        rank=row.get("accepted_rank", ""), ref=int(row["reference_no"]))
            occurrences[item["id"]] = item
    ids = {r["ref"] for r in (*all_collections.values(), *occurrences.values())}
    refs = {}
    for batch in batched(sorted(ids), 100):
        for r in records("refs", id=",".join(map(str, batch))):
            author = r.get("author1last", "")
            if r.get("otherauthors"):
                author += " et al."
            elif r.get("author2last"):
                author += " & " + r["author2last"]
            refs[int(r["reference_no"])] = dict(author=author, year=r.get("pubyr", ""), title=r.get("reftitle") or r.get("pubtitle") or "Reference record", doi=r.get("doi", ""))
    if set(refs) != ids or any(i["col"] not in all_collections for i in occurrences.values()):
        raise ValueError("Incomplete PBDB cross-references")
    for group in presets.values():
        if not any(r["col"] in group for r in occurrences.values()) or not any(all_collections[c]["peers"]["age"] for c in group):
            raise ValueError("Missing focal occurrences or age peers")
    return dict(presets=presets, collections=list(all_collections.values()), occurrences=list(occurrences.values()), references=refs)


def main():
    data = make_snapshot()
    digest = dict(retrieved=datetime.now(timezone.utc).date().isoformat(), count=len(data["occurrences"]), collections=len(data["collections"]), papers=len(data["references"]))
    out = ROOT / "web/data"
    out.mkdir(exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
    (out / "records.json.gz").write_bytes(gzip.compress(raw, mtime=0))
    (out / "index.json").write_text(json.dumps(digest, indent=2) + "\n")
    print(digest)


if __name__ == "__main__":
    main()
