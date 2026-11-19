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
