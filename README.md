# Fossil Neighbours

[Explore the fossil collections](https://coolcode.ca/fossilneighbours/)

<!-- coolcode:guide -->
Start with the Coal Mine Point fossil profile to see the original identifications and accepted names. Follow a collection with overlapping age bounds or with matching accepted PBDB taxon IDs. Switch to Haslam on Vancouver Island to compare its much younger collections with Canadian collections whose age ranges overlap.
<!-- /coolcode:guide -->

## Reading the records

The formation view counts PBDB occurrence IDs, distinct collection IDs, and distinct nonzero accepted taxon IDs separately. One occurrence represents a published identification at a collection. A collection can contain several records of the same taxon, and an accepted taxon can be at genus, family or another rank. Identifications without an accepted taxon ID remain searchable and do not enter the accepted-taxon count. The database reflects the literature entered to date and sampling effort varies.

Choose a collection to read its occurrence records and source papers. Select “Whole focal formation” to search all its collections by identification or by an age that falls inside a recorded interval, including the bounds. Ages are the older and younger bounds assigned by the Paleobiology Database in millions of years before present. Overlap does not establish that two finds lived at the same moment. The environment filter requires identical, nonempty PBDB environment labels. “Marine indet.” and other broad labels retain their original meaning.

## Fossil profiles

The [profile directory](https://coolcode.ca/fossilneighbours/records/) includes each focal formation and every collection in the published snapshot. Collection URLs use their stable PBDB collection IDs. Each page lists reported fossils, accepted names, source papers, and selected collections with overlapping age bounds. A reverse link on an age neighbour opens the focal collection that led to it. Up to three additional collections share the most distinct nonzero accepted taxon IDs in this edition, with ties resolved by collection name and ID. The comparison counts database identifications across all ranks. A shared name alone does not establish a shared formation, environment or age.

The offline build regenerates the profile directory and native sitemap from the same source snapshot as the interactive search. On the fifth of each month at 07:27 UTC the refresh workflow is scheduled to fetch the PBDB data. Every published profile displays the successful retrieval date and opens the appropriate collection or formation in the explorer.

## Coverage and sources

The formation presets include Canadian PBDB collections explicitly assigned to Joggins in Nova Scotia and Haslam in British Columbia. For every focal collection, the refresh searches all Canadian collections overlapping its age range. Collections from a different or unnamed formation qualify when their numerical age intervals overlap for a positive duration. The tool retains up to six age peers and, separately, up to six peers with the same recorded environment. It ranks by the sum of absolute differences between the two older and two younger bounds, breaking ties by collection ID. The local snapshot includes all occurrence records returned for the selected collection IDs. The Joggins and Haslam formations have different geological ages.

Source data come from the [Paleobiology Database and its contributors](https://paleobiodb.org/), through version 1.2 of the [PBDB Data Service](https://paleobiodb.org/data1.2/). Each displayed record links to its PBDB identifier, with DOI links provided where available. [Peters & McClennen (2016)](https://doi.org/10.1017/pab.2015.39) describe the data service. See the [Joggins coal map](https://coolcode.ca/coalbelow/) for mine workings and seams. Searches and selections run on the device and are never stored. External links open the referenced sites.

## Build and refresh

Use Python 3.12 or later. Run `python3 scripts/refresh.py` to fetch source data. Run `python3 scripts/build.py` for an offline build from the checked-in snapshot. Scheduled monthly and manually dispatched refresh jobs retrieve and validate fresh data before deployment. The displayed retrieval date records that successful fetch. Failed refreshes leave the previously published deployment available.

Run `node --test tests/*.test.mjs` and `python3 -m unittest discover -s tests -v`. Run `python3 tests/browser_smoke.py` with Playwright Chromium installed, or set `CHROMIUM_PATH` to a compatible Chromium binary.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
