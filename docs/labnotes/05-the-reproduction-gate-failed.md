# The reproduction gate failed, and that is the result

Status: ready to post
Suggested image: `assets/biohsi_54m_reproduction.png`

HyperMix did not move on to compare detectors on the 54-meter bioHSI scene.

Before looking at the nine candidate regions, I defined a reproduction gate for
the published hierarchical K-means plus UCLS method. The reproduced regional
scores had to reach both a mean absolute error no greater than 0.01 and a
Pearson correlation of at least 0.99 against the paper's Source Data.

The gate failed by a wide margin.

The HyperMix implementation produced an MAE of 0.156 and Pearson correlation of
0.376. The mismatch was too large to dismiss as a library version or rounding
difference.

I then ran the authors' tagged source implementation directly on the same cube
and candidate boxes. That independent diagnostic also failed, with an MAE of
0.158 and Pearson correlation of 0.145. Importantly, the full source-code score
map reached 0.398, so the method did produce values on the published scale. The
candidate boxes simply did not recover the published regional means.

This localizes the problem. The paper's Figure 4 notebook loads a file named
`manually_defined_rectangle_coordinates.json`, created by interactive clicks on
the full scene. That file is absent from both the 54-meter data archive and the
tagged code release. The archive contains a different parameter file with
cropped, rotated regions. Their visual plausibility and matching count were not
enough to establish that they were the same boxes.

The correct response is not to slide boxes around until the correlation looks
good. HyperMix has paused the real-target comparison. No matched filter, RX,
matched subspace, or learned detector result will be reported on these regions
unless an independent coordinate bridge is recovered.

This is exactly why the gate existed. A failed reproduction prevented a
plausible but unsupported geometry from becoming a benchmark result.

Code, raw regional scores, and diagnosis:
https://github.com/JVLegend/HyperMix
