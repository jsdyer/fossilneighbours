# Fossil Neighbours

[Explore the fossil collections](https://coolcode.ca/fossilneighbours/)

<!-- coolcode:guide -->
Start at Coal Mine Point in the Joggins Formation and search for Hylonomus to see how several reported names resolve to one accepted taxon. Switch to Haslam on Vancouver Island to compare its much younger collections with Canadian collections whose age ranges overlap.
<!-- /coolcode:guide -->

## Reading the records

The formation view counts PBDB occurrence IDs, distinct collection IDs, and distinct nonzero accepted taxon IDs separately. One occurrence represents a published identification at a collection. A collection can contain several records of the same taxon, and an accepted taxon can be at genus, family or another rank. Identifications without an accepted taxon ID remain searchable and do not enter the accepted-taxon count. The database reflects the literature entered to date and sampling effort varies.

Choose a collection to read its occurrence records and source papers. Ages are the older and younger bounds assigned by the Paleobiology Database in millions of years before present. Overlap does not establish that two finds lived at the same moment. The environment filter requires identical, nonempty PBDB environment labels. “Marine indet.” and other broad labels retain their original meaning.

## Coverage and sources

The formation presets include Canadian PBDB collections explicitly assigned to Joggins in Nova Scotia and Haslam in British Columbia. For every focal collection, the refresh searches all Canadian collections overlapping its age range. Collections from a different or unnamed formation qualify when their numerical age intervals overlap for a positive duration. The tool retains up to six age peers and, separately, up to six peers with the same recorded environment. It ranks by the sum of absolute differences between the two older and two younger bounds, breaking ties by collection ID. The local snapshot includes all occurrence records returned for the selected collection IDs. The Joggins and Haslam formations have different geological ages.

Source data come from the [Paleobiology Database and its contributors](https://paleobiodb.org/), through version 1.2 of the [PBDB Data Service](https://paleobiodb.org/data1.2/). Each displayed record links to its PBDB identifier, with DOI links provided where available. [Peters & McClennen (2016)](https://doi.org/10.1017/pab.2015.39) describe the data service. See the [Joggins coal map](https://coolcode.ca/coalbelow/) for mine workings and seams. Searches and selections run on the device and are never stored. External links open the referenced sites.

## Build and refresh

Use Python 3.12 or later. Run `python3 scripts/refresh.py` to fetch source data. Run `python3 scripts/build.py` for an offline build from the checked-in snapshot. Scheduled monthly and manually dispatched refresh jobs retrieve and validate fresh data before deployment. The displayed retrieval date records that successful fetch. Failed refreshes leave the previously published deployment available.

Run `node --test tests/*.test.mjs` and `python3 -m unittest discover -s tests -v`. Run `python3 tests/browser_smoke.py` with Playwright Chromium installed, or set `CHROMIUM_PATH` to a compatible Chromium binary.
