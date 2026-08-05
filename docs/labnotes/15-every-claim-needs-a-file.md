# Every claim now has a file, a command, and a checksum

HyperMix has accumulated several experiments, but a long list of result files
is not yet a publication package. A reader should be able to trace every major
statement back to the exact command and artifact that supports it.

I have now added a machine-readable evidence manifest. It covers eight major
claims across background learning, calibrated uncertainty, band sparsity,
target transfer, held-out targets, detection limits, calibrated abundance, and
the blocked real-target reproduction. Sixteen result files are fixed by their
SHA-256 checksums.

The verifier uses only the Python standard library:

```bash
python scripts/verify_evidence_manifest.py
```

It fails closed when a file is missing or changed, when claim identifiers are
duplicated, or when an artifact path tries to leave the repository. This is an
integrity check, not a substitute for rerunning the experiments. The manifest
also records the full generation command and the limitation attached to every
claim.

The most important entry is marked `blocked`. The candidate regions for Figure
4g did not reproduce the published regional scores, so HyperMix still does not
compare detectors on that biological target. A checksum cannot solve missing
geometry, and a visually plausible region cannot replace author-validated
coordinates.

This publication package therefore preserves the same conclusion as the
benchmark itself: no learned method has robustly beaten the calibrated spatial
matched filter in the completed tests. The contribution is the open audit
trail, including negative and inconclusive results.

The next external step is small and concrete. Another person can clone the
repository, run one verification command, and report the commit and output.
The next scientific step remains recovering the manual Figure 4g rectangles or
an independently validated mapping from those rectangles to the public cube.
