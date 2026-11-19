import {matching, summarize, age} from "./model.mjs";

const el = id => document.getElementById(id);
const element = (tag, text) => {
  const node = document.createElement(tag);
  node.textContent = text;
  return node;
};
function link(label, url) {
  const a = element("a", label);
  a.href = url;
  return a;
}
const recordURL = (kind, id) => {
  const route = {Collection:"colls", Taxon:"taxa", Reference:"refs"}[kind];
  return `https://paleobiodb.org/data1.2/${route}/single.json?vocab=pbdb&id=${id}`;
};
async function get(file) {
  const r = await fetch("./data/" + file);
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}

async function start() {
  const [data, index] = await Promise.all([get("records.json"), get("index.json")]);
  const collections = new Map(data.collections.map(c => [c.id, c]));
  let active;
  const formation = el("formation"), focus = el("collection"), env = el("environment");
  function reference(id) {
    const ref = data.references[id], holder = element("span", "");
    holder.append(link([ref.author, ref.year].filter(Boolean).join(" ") || "PBDB reference",
      recordURL("Reference", id)), " · " + ref.title);
    if (ref.doi && /^10\.\d{4,9}\//.test(ref.doi)) holder.append(" · ", link("DOI", "https://doi.org/" + ref.doi));
    return holder;
  }
  function renderRecords() {
    const c = collections.get(active);
    el("examining").replaceChildren(link(c.name, recordURL("Collection", c.id)), " · " + (c.formation || "Unnamed formation") + " · " + age(c) + " · " + (c.env || "Environment unrecorded"));
    const rows = matching(data.occurrences, [c.id], el("search").value).sort((a, b) => a.name.localeCompare(b.name));
    el("record-count").textContent = rows.length + " matching occurrence " + (rows.length === 1 ? "record" : "records");
    const items = rows.map(row => {
      const item = element("article", ""), name = element("h3", row.name);
      const accepted = element("p", row.taxon ? "Accepted as " : "Accepted taxon ID unavailable");
      if (row.taxon) accepted.append(link(row.accepted, recordURL("Taxon", row.taxon)), " · " + row.rank);
      const source = element("p", ""); source.append(reference(row.ref));
      item.append(name, accepted, source, link("Occurrence " + row.id, "https://paleobiodb.org/data1.2/occs/single.json?vocab=pbdb&id=" + row.id));
      return item;
    });
    el("records").replaceChildren(...(items.length ? items : [element("p", "No matching identification in this collection.")]));
  }
  function choose(id) {
    active = id;
    el("return").hidden = active === Number(focus.value);
    for (const button of el("peers").querySelectorAll("button")) {
      button.setAttribute("aria-pressed", String(Number(button.value) === active));
    }
    renderRecords();
  }
  function renderFocus() {
    const c = collections.get(Number(focus.value));
    el("focus-name").textContent = c.name;
    el("focus-context").textContent = [c.interval, age(c), c.env || "Environment unrecorded"].join(" · ");
    el("focus-ref").replaceChildren(link("Collection " + c.id, recordURL("Collection", c.id)), " · ", reference(c.ref));
    const peers = c.peers[env.checked ? "environment" : "age"];
    el("peers").replaceChildren(...peers.map(id => {
      const p = collections.get(id), b = element("button", "");
      b.value = id;
      b.append(element("strong", p.name), element("small", [p.formation || "Unnamed formation", p.province || "Canada", age(p), p.env || "Environment unrecorded"].join(" · ")));
      b.addEventListener("click", () => choose(id));
      return b;
    }));
    if (!peers.length) el("peers").append(element("p", "No other Canadian collection in this search has an overlapping age and the same recorded environment."));
    choose(c.id);
  }
  function renderFormation() {
    const ids = data.presets[formation.value], totals = summarize(data.occurrences, ids);
    el("formation-title").textContent = formation.value + " Formation";
    el("province").textContent = collections.get(ids[0]).province;
    el("totals").textContent = `${totals.collections} collections · ${totals.occurrences} occurrence records · ${totals.taxa} accepted taxa`;
    focus.replaceChildren(...ids.map(id => new Option(collections.get(id).name + " · #" + id, id)));
    el("search").value = "";
    renderFocus();
  }
  const requested = new URLSearchParams(location.search).get("formation");
  if (Object.hasOwn(data.presets, requested)) formation.value = requested;
  formation.addEventListener("change", renderFormation);
  focus.addEventListener("change", () => { el("search").value = ""; renderFocus(); });
  env.addEventListener("change", renderFocus);
  el("search").addEventListener("input", renderRecords);
  el("return").addEventListener("click", () => choose(Number(focus.value)));
  el("stamp").textContent = `PBDB data retrieved ${index.retrieved} · ${index.collections} collections including age neighbours · ${index.count} occurrence records`;
  renderFormation();
}
start().catch(() => el("totals").textContent = "The collection snapshot could not be loaded. Reload to try again.");
