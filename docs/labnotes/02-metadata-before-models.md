# Metadata before models

Status: ready to post
Suggested image: a crop of the 54 m scene or its ENVI header

The first complete bioHSI scene is now local and verified.

The 54-meter archive contains a 908,587,680-byte ENVI cube with 682 samples,
1,220 lines, and 273 spectral bands. The bands cover 398.411 to 1,002.430 nm.
The data are float32, band-sequential, and little-endian.

Those details matter because the older HyperMix ENVI loader was designed for a
different task. It applied a global min-max normalization and returned only an
array. That is convenient for a benchmark preview, but unsafe for measured
radiometric data because it discards the wavelengths, declared units, comments,
and original scale.

The real scene also contains a subtle trap: exactly 18.00% of its pixels are
zero in every sampled band. They are not dark measurements. They are fill pixels
introduced by geo-orthorectification outside the imaged footprint. Treating them
as background would bias the covariance, and using them as the global minimum
would distort every spectrum.

I therefore added a new metadata-preserving ENVI reader. It maps the large
binary file into memory without loading the entire cube, preserves the recorded
values and wavelengths, validates the expected binary size, and explicitly
identifies all-band fill pixels.

There is another honest ambiguity. A header comment declares radiance units,
while the product description and observed range are consistent with a
reflectance-corrected product. HyperMix does not silently choose one
interpretation. The ambiguity is stored with the data and will remain visible in
the analysis.

The test suite now exercises every ENVI interleave, byte order, offsets,
truncation, wavelengths, comments, and fill masks using synthetic files. The
large research cube is not required to run the tests.

No model has been evaluated on the target regions yet. Metadata came first so
that later comparisons cannot quietly redefine what the measurements mean.

Repository: https://github.com/JVLegend/HyperMix
