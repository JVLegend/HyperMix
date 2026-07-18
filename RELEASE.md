# Releasing HyperMix

Steps that need your accounts (I prepared everything; these need your credentials).

## 1. Publish to PyPI

The package already builds cleanly (`python -m build` → `dist/`). To publish:

```bash
cd ~/Documents/GitHub/HyperMix
. .venv-train/bin/activate          # or any env with build + twine
pip install -U build twine
rm -rf dist && python -m build      # rebuild sdist + wheel for the current version
twine check dist/*                  # validates metadata (no upload)
twine upload dist/*                 # asks for your PyPI token
```

- Get a token at https://pypi.org/manage/account/token/ (scope: entire account,
  or project-scoped after the first upload).
- Username is `__token__`, password is the token (starts with `pypi-`).
- Tip: test first on TestPyPI with `twine upload -r testpypi dist/*`.
- After publishing, `pip install hypermix` works for anyone.

## 2. Mint a DOI on Zenodo

`.zenodo.json` and `CITATION.cff` are already in the repo, so Zenodo will pick up
the metadata automatically.

1. Sign in at https://zenodo.org with your GitHub account.
2. Go to https://zenodo.org/account/settings/github/ and flip the switch **ON**
   for the `JVLegend/HyperMix` repository.
3. On GitHub, cut a new release (e.g. tag `v0.4.0`). Zenodo archives it and
   issues a DOI automatically.
4. Copy the DOI badge Zenodo gives you into `README.md` (top, next to the other
   badges) and update the "Cite" section.

## 3. After the DOI exists

Add to the README badges:

```md
[![DOI](https://zenodo.org/badge/DOI/<your-doi>.svg)](https://doi.org/<your-doi>)
```

That closes Milestone 3 (open dataset + benchmark + package + DOI).
