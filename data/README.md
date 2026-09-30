# Data

This folder contains the prepared skull meshes and measurement workbooks. The scripts locate
them through `paths.py` in the repository root.

| Folder or file | Contents |
|---|---|
| `DF_and_their_relatives/` | 100 remeshed skulls of Darwin's finches and their relatives |
| `Honeycreepers_watertight/` | 42 skulls of Hawaiian honeycreepers (SI Section S4) |
| `HC_Relatives_watertight/` | 9 skulls of their cardueline relatives (SI Section S4) |
| `Peromyscus/` | 2 rodent skulls |
| `Human_cranium/` | 4 human crania |
| `Dataset.xlsx` | all measurements of the 100 finch specimens |
| `Dataset_training.xlsx` | the 50 training specimens of Eq. (8) |
| `Dataset_other_taxa.xlsx` | 53 per-specimen records for SI Section S4: 51 birds and 2 rodents |
| `figure_inputs/` | inputs used only by `5_figures/figure.py` |

The scripts only read from this folder; their results go into `output/` next to each script.

The [figure-input folder](https://github.com/kaikwanlau/skull-morphology/tree/main/data/figure_inputs) also includes the referenced photograph, one original scan-derived STL and two earlier-remeshed skulls. Their source links and reuse terms are listed there; they do not add specimens to the analysis cohorts above.

## Use in the study

The **100 skulls of Darwin’s finches and their relatives** form the main dataset for the skull measurements and statistical analyses.

The **51 additional bird skulls** (42 Hawaiian honeycreepers and 9 cardueline relatives) were analysed with the finch fitting settings. In Supporting Information Section S4, 38 of the 51 orbital fits meet both quality criteria: at least 40 inliers and an RMS residual no greater than 10% of the fitted radius. The other 13 are flagged for review. Every fit was also inspected visually.

The **two rodent skulls and four human crania** are exploratory examples used to examine the method’s scope and limitations:

- In the rodents, the fitted spheres lie outside the orbits. Orbital measurement fields are therefore blank in the released workbook and generated measurement files, with an explanatory status. Specimen identities, skull dimensions and mesh topology are retained.
- In the human crania, the search band was changed to 10–50% of skull length and the radius range to 2–60 mm. The fitted spheres lie in the orbits, but none of the four fits meets both S4 quality criteria.

These are groups of specimens; all the supplied surface meshes use the STL format. Their inclusion does not imply that the method gives reliable orbital measurements for every specimen or taxon.

For the rodent diagnostic figures, principal-axis alignment uses all vertices of the supplied mesh. The largest connected component is then retained for fitting. The spheres illustrate the method's limitation and are not exported as orbital measurements. Use `6_verification/verify_all.py` to reproduce the avian S4 measurements and the two-rodent inventory.

## Sources and scope

The bird scans were acquired and processed in the work of Tokita et al. (2017), Al-Mosleh et al. (2021) and Mosleh et al. (2023), and were remeshed for this study. The honeycreeper and cardueline collections come from the Tokita et al. dataset. See the accompanying paper for the specimen lists and preparation method.

The two rodent examples are *Peromyscus gossypinus* and *P. simulus* from the openVertebrate project. The four human examples are drawn from TotalSegmentator (s1397), the Arothron example skull, BodyParts3D and a NiiVue sample head CT. Their preparation and fitting settings are described in the paper.

| Reference | Source described |
| :--- | :--- |
| Tokita et al. (2017), *Cranial shape evolution in adaptive radiations of birds: comparative morphometrics of Darwin’s finches and Hawaiian honeycreepers* | Bird cranial scans |
| Al-Mosleh et al. (2021), *Geometry and dynamics link form, function, and evolution of finch beaks* | Earlier finch processing |
| Mosleh et al. (2023), *Beak morphometry and morphogenesis across avian radiations* | Earlier avian processing |
| openVertebrate; TotalSegmentator; Arothron; BodyParts3D; NiiVue sample images | Additional mammalian examples |

Preserve the original source attributions and check the terms attached to each source dataset before redistribution. The code’s Apache 2.0 license should not be treated as a new license grant for all third-party scans. The source article and Supporting Information contain the fuller provenance references.

## Using the tables

The statistics scripts read the released workbooks in this folder. The fitting scripts write new workbooks under their output folders; those do not automatically replace the released tables. Keep your own inputs in a separate folder and retain the measurement version used in an analysis.

Specimen names retain their original spelling and capitalization. Measurement tables omit remeshing-parameter columns. Remeshing input settings and run logs remain part of the remeshing workflow; the paper's SI specimen tables provide the finch preprocessing information. See the paper’s specimen lists for taxonomic details.
