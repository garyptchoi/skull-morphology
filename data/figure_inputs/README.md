# Figure inputs and sources

This folder contains the four additional inputs used in Fig. 1 and Fig. S1. The photograph comes from the reference cited in the manuscript. The meshes come from the Harvard Dataverse archives linked by Gary P. T. Choi's [publication list](https://garyptchoi.github.io/publications.html).

| File | Used for | Source |
| :--- | :--- | :--- |
| `photo/C.pallidus.jpg` | Fig. 1(a), photograph of *Camarhynchus pallidus* | Wikimedia Commons; Julien Renoult, CC BY 4.0 |
| `raw_meshes/P2.InornataA.stl` | Fig. 1(b), original scan-derived surface of *Pinaroloxias inornata* | Al-Mosleh et al. (2021), original full-skull mesh |
| `prior_remeshing/C.PallidusA.stl` | Fig. S1, earlier-remeshing comparison for *Camarhynchus pallidus* | Mosleh et al. (2023), full-skull watertight mesh |
| `prior_remeshing/C.flaveolaA.stl` | Fig. S1, earlier-remeshing comparison for *Coereba flaveola* | Mosleh et al. (2023), full-skull watertight mesh |

All four files are included. Their contents are unchanged from the source files. The original photograph is kept as a JPEG; `5_figures/figure.py` reads `C.pallidus.jpg` and applies the existing crop when drawing the panel.

## Photograph credit

Julien Renoult, *Woodpecker Finch (Camarhynchus pallidus)*, 27 March 2017. [Wikimedia Commons file page](https://commons.wikimedia.org/wiki/File:Camarhynchus_pallidus_12789263.jpg), originally published on [iNaturalist](https://www.inaturalist.org/photos/12789263). Licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).

The stored photo is unmodified. Fig. 1(a) crops it. When reusing that panel, retain the photographer's credit, source and licence link, and state that the photo is cropped.

## Mesh sources

**Original full skull:** [Al-Mosleh et al. (2021), Code and Data, version 2.0](https://doi.org/10.7910/DVN/IHODX1). The source path is `Meshes/Full Skulls STL/P2.InornataA.stl`, [Dataverse file 5193531](https://dataverse.harvard.edu/api/access/datafile/5193531). This is a scan-derived STL surface, not a CT image stack. It contains 323,627 triangles; the figure script reduces the displayed geometry without changing the stored file.

**Earlier remeshing:** [Mosleh et al. (2023), Bird Beaks, version 1.0](https://doi.org/10.7910/DVN/UQQ6EZ). Both files were extracted from `Meshes - Darwins finches.zip`, [Dataverse file 6947348](https://dataverse.harvard.edu/api/access/datafile/6947348):

- `Meshes/Darwins Finches/Full Skulls Watertight/C.PallidusA.stl` (2,926 triangles).
- `Meshes/DF Relatives/Full Skulls Watertight/C.flaveolaA.stl` (2,622 triangles).

Both Dataverse records release the data under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Cite the associated studies when using these meshes:

- Al-Mosleh, S., Choi, G. P. T., Abzhanov, A. and Mahadevan, L. (2021). [Geometry and dynamics link form, function, and evolution of finch beaks](https://doi.org/10.1073/pnas.2105957118). *PNAS*, 118(46), e2105957118.
- Mosleh, S., Choi, G. P. T., Musser, G. M., James, H. F., Abzhanov, A. and Mahadevan, L. (2023). [Beak morphometry and morphogenesis across avian radiations](https://doi.org/10.1098/rspb.2023.0420). *Proceedings of the Royal Society B*, 290, 20230420.

## Checks and use

The photograph matches Wikimedia's published SHA-1 checksum. The raw mesh matches Dataverse's published MD5 checksum. The two files extracted from the ZIP pass its CRC-32 checks. File sizes, SHA-256 checksums and source paths are recorded in [sources.json](https://github.com/kaikwanlau/skull-morphology/blob/main/data/figure_inputs/sources.json).

The fitting and statistical analyses continue to use the prepared meshes elsewhere in `data/`. These three figure meshes represent earlier processing stages and do not add specimens to the analysis cohorts.

To draw the affected figures:

```bash
python 5_figures/figure.py --only 1,S1
```

The command also prepares or loads the figure script's measurement cache. If an input is removed, the script leaves its panel as a labelled blank. Restoring these inputs resolves the four missing panels; it does not by itself verify every numerical result or guarantee identical rendering across software versions.
