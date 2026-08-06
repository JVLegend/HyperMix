# The table is code

Copying a result into a manuscript creates a quiet failure mode. The experiment
can change while the number in the paper stays frozen.

HyperMix now builds its main results table directly from eight versioned JSON
files. The same standard-library command updates a delimited block in the
internal manuscript, writes a vector contrast figure, and records SHA-256 hashes
for every source file. CI runs the builder in check mode and fails if any of the
four synchronized outputs drift.

The figure makes one additional constraint explicit. AUC, Pd, NLL, ECE, MAE,
and interval width are not interchangeable effect sizes. Each row therefore has
its own scale. The visual supports only two comparisons: which direction the
effect points and whether its confidence interval crosses zero.

That distinction matters here. Most completed learned-versus-classical
contrasts point toward the classical baseline. The abundance MAE interval
crosses zero. The blocked bioHSI reproduction remains a blocked row rather than
being omitted from the table.

Automation does not make the scientific interpretation automatic. It makes a
specific class of transcription error visible before publication.
