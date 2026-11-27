export function matching(records, collectionIds, term = "") {
  const ids = new Set(collectionIds);
  const query = term.toLowerCase().trim();
  return records.filter(row => ids.has(row.col) &&
    (row.name.toLowerCase().includes(query) || row.accepted.toLowerCase().includes(query)));
}

export function summarize(records, collectionIds) {
  const rows = matching(records, collectionIds);
  return {collections: new Set(collectionIds).size, occurrences: rows.length,
    taxa: new Set(rows.map(r => r.taxon).filter(Boolean)).size};
}

export function age(row) {
  return row.old === row.young ? `${row.old} Ma` : `${row.old}–${row.young} Ma`;
}

export function containsAge(collection, ageValue) {
  if (ageValue === "") return true;
  const target = Number(ageValue);
  return Number.isFinite(target) && collection.young <= target && target <= collection.old;
}

export function initialSelection(data, params) {
  const requested = params.get("formation");
  const formation = Object.hasOwn(data.presets, requested) ? requested :
    Object.hasOwn(data.presets, "Joggins") ? "Joggins" : Object.keys(data.presets)[0];
  const ids = data.presets[formation];
  const wanted = Number(params.get("collection"));
  const collection = ids.includes(wanted) ? wanted : ids.includes(28069) ? 28069 : ids[0];
  const peers = data.collections.find(row => row.id === collection).peers;
  const peer = Number(params.get("peer"));
  const environment = !peers.age.includes(peer) && peers.environment.includes(peer);
  return {formation, collection, peer: (environment || peers.age.includes(peer)) ? peer : null,
    environment, scope: params.get("scope") === "formation" ? "formation" : "collection",
    identification: params.get("identification") || ""};
}
