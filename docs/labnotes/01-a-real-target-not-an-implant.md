# A real target, not an implant

Status: ready to post
Suggested image: `assets/banner.png`

HyperMix has reached a boundary that every simulation-based benchmark eventually
faces.

The project has tested engineered spectral targets under low signal, spectral
mismatch, physical distortions, target variability, non-Gaussian backgrounds,
and probability calibration. In those tests, the learned methods did not
robustly outperform a carefully calibrated spatial matched filter.

That is the honest result, and it changed the direction of the project. Building
a larger network without a new causal hypothesis would not answer the central
question. The more important limitation is that the current benchmark places a
digital target into a real hyperspectral background. The background is real,
but the biological signal was not physically present when the image was taken.

The next phase removes that limitation.

I have started validating HyperMix on the public bioHSI data from Chemla and
colleagues. These experiments imaged engineered bacterial reporters from the
air. The first scene selected for analysis contains bacteriochlorophyll a
reporters measured from 54 meters.

Before running a detector, I created a versioned data manifest and a resumable
downloader. Every completed file must match both the published size and MD5
checksum. The archive can also be tested and inventoried without extracting its
contents.

This may sound like infrastructure rather than science. In an open benchmark,
it is part of the science. A result is only useful if another researcher can
identify the exact file, verify it, and repeat the analysis.

There is no real-target detection result in this update. The progress is that
the transition from implanted targets to a physically measured reporter is now
underway and auditable.

Code and roadmap: https://github.com/JVLegend/HyperMix

What evidence would you want to see before accepting an algorithmic result on a
real hyperspectral biosignature?
