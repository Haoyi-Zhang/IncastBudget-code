# Vector figure reproduction

Figure generation is optional post-processing of retained results, not an experiment or part of certificate checking. It needs Python 3.10+, Matplotlib, and FontTools (a Matplotlib dependency).

```sh
python -m pip install matplotlib fonttools
python scripts/plot_figures.py --output /tmp/incast-plots
```

Run from the repository root. The command writes `allocation.pdf` and `corners.pdf` to `/tmp/incast-plots`; choose a fresh external directory to preserve retained figures. Without `--output`, the default is `figures/` relative to the repository root, not `artifact/figures/` in a standalone checkout. To copy identical PDFs into a full project's sibling paper, add `--paper-figures ../paper/figures`. A paper-only package can compile its shipped figure PDFs without Python.

The producer reads `results/derived/allocation.csv` and `corners.csv`. `export_results.py` remains the owner of these exact decimal CSVs; `--data` can select a newly exported directory. It checks the three active running-instance cuts and the endpoint-corner control without rerunning the validation campaign.

The text family is Times New Roman (the IEEE body family). On Windows the producer discovers `times.ttf`, `timesi.ttf`, and `timesbd.ttf` under the system Fonts directory. Elsewhere it tries installed Times New Roman, then the metrics-compatible Liberation Serif, then bundled STIXGeneral as a documented Times-style fallback. Install Times New Roman when exact family matching is required; no proprietary font file is redistributed.

PDF text is embedded with `pdf.fonttype=42`; `text.usetex` and unembedded PDF core fonts are disabled. Curves, markers, axes, and text remain vector objects. The canvas and axis rectangles are explicit PDF-point dimensions measured from the current manuscript plots; saving does not crop or rasterize them. Captions and float placement remain in the TeX source.
