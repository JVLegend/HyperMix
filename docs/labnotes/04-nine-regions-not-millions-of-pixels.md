# Nine regions, not millions of pixels

Status: ready to post
Suggested image: `assets/biohsi_54m_rois.png`

The candidate 54-meter evaluation geometry and its statistical rules were
frozen before the first reproduction attempt.

The published experiment contributes nine labeled containers. Each container
occupies only a few pixels in the hyperspectral image. It would be tempting to
treat every pixel inside and outside those boxes as an independent observation,
producing a very large sample size and narrow confidence intervals.

That would be wrong.

Pixels from the same container share the same biological preparation, spatial
environment, illumination, and imaging process. They are correlated
measurements of one region. HyperMix will therefore calculate one mean score per
container. The statistical sample size for the primary comparison is nine, not
the number of image pixels.

The nine induction levels range from 0 to 250 micromolar. Following the authors'
public notebook, concentrations of 5 micromolar or more are treated as positive
for the regional ROC analysis. This gives six positive and three negative
regions. Pixel-level Pd@FAR is explicitly excluded because the publication does
not provide a defensible pixel-level biological mask.

The primary metric will be region-level AUC. Secondary analyses will report the
association with concentration and the full table of all nine scores. With one
region per concentration, bootstrap intervals cannot be described as biological
population uncertainty. Any resampling will be labeled only as a sensitivity
analysis.

I also generated a visual audit showing every rectangle in both scene
coordinates and the cropped, rotated coordinate system stored in the data
parameters. No detector score was used to place or move a box. The audit checks
the transformation, not whether these are the separate manual boxes used in the
paper's Figure 4 notebook.

The next step is to reproduce the original hierarchical K-means plus UCLS
method. Only if that gate is crossed will the matched filter, RX, matched
subspace, and learned detector be compared.

There is still no result about which method wins on the real target. The point
of this update is that the rules are now recorded before the race begins.

Repository: https://github.com/JVLegend/HyperMix
