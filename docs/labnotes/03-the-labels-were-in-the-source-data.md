# The labels were missing from the archive, but not from the public record

Status: ready to post
Suggested image: the nine rows from Source Data sheet 4G

Inspecting the real 54-meter archive changed the HyperMix plan.

The authors' analysis notebook refers to two concentration CSV files and a
reference spectrum. None of those files are present inside the 54-meter ZIP.
The parameter file contains absolute paths from the original analysis computer,
so the image alone does not tell us which container received which induction
level.

At first, this looked like a hard external blocker. Running a detector anyway
would have been easy, but scientifically meaningless: without independently
defined labels, any region definition could drift toward whichever method
looked best.

The missing mapping was recoverable from another public source. The Source Data
workbook published with the Nature Biotechnology article contains a sheet named
4G. It reports exactly nine concentrations and nine published mean
classification scores. The concentrations are 250, 100, 50, 25, 10, 5, 1, 0.1,
and 0 micromolar. The archive also contains nine candidate regions in its first
sample. At this stage, matching counts made a correspondence plausible, but did
not prove that these were the manually selected boxes used in Figure 4.

The independent YF10 pellet absorbance spectrum is also present in the authors'
versioned code release and was already preserved in the HyperMix spectral
library.

This means a reproduction gate can be attempted without inventing labels or
extracting a target signature from the test scene. The provenance is frozen in
a small protocol file containing the source URL, worksheet range, checksum,
concentrations, and candidate region coordinates.

Four additional rectangles in the parameter file still do not have an
independent identity. They are excluded from the primary analysis rather than
being guessed.

The lesson from this stage is simple: “missing from one archive” is not the same
as “safe to infer.” Provenance work recovered the labels without consulting any
detector output, while leaving the geometry as a hypothesis to test.

Repository: https://github.com/JVLegend/HyperMix
