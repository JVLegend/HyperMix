# The one missing artifact that would unblock the real-target test

Status: ready to post
Suggested image: `assets/biohsi_54m_rois.png`

The current HyperMix blocker is unusually precise.

The 54-meter hyperspectral cube is public and checksum-verified. The independent
YF10 pellet absorbance spectrum is public. The Source Data workbook provides the
nine induction concentrations and the nine published mean classification
scores. The original classifier code is public and executable.

What is missing is the coordinate bridge.

The Figure 4 notebook expects
`manually_defined_rectangle_coordinates.json`, containing top-left and
bottom-right corners selected on the complete scene. That file is not in the
data archive or code release. The two concentration files referenced by the
notebook, `plates_col1_labels.csv` and `plates_col2_labels.csv`, are also absent.

Any one of the following could unblock a defensible test:

1. the exact manual rectangle JSON used for Figure 4g;
2. an authors' output directory containing that JSON and its score map;
3. a documented deterministic transform proving that the archive's local boxes
   are the notebook's full-scene boxes;
4. full-scene coordinates printed in a methods supplement or repository issue.

Until one of those appears, the published Source Data can validate scores but
cannot tell us where to average them. Searching a score map for boxes that match
the table would leak the evaluation target into the region definition.

This is a small missing file with a large scientific consequence. If you know
where this artifact is archived, please point me to it. HyperMix will hash it,
rerun the frozen reproduction gate, and publish the result either way.

Repository: https://github.com/JVLegend/HyperMix
