#!/usr/bin/env python3
"""Draw retained exact queue/allocation coordinates; no validation campaign is run."""
import argparse
import csv
import json
import shutil
from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path, delimiter=","):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def canvas(width, height, box, fontsize=8):
    """Canvas and axis geometry in PDF points, measured in the original PDF."""
    fig = plt.figure(figsize=(width / 72, height / 72))
    left, bottom, axis_width, axis_height = box
    ax = fig.add_axes([left / width, bottom / height,
                       axis_width / width, axis_height / height])
    ax.tick_params(direction="in", length=2.5, width=.4, pad=3,
                   labelsize=fontsize)
    for spine in ax.spines.values():
        spine.set_linewidth(.4)
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, name, output, paper_figures):
    output.mkdir(parents=True, exist_ok=True)
    target = output / (name + ".pdf")
    fig.savefig(target, format="pdf", metadata={"Creator": None,
                                               "Producer": None,
                                               "CreationDate": None,
                                               "ModDate": None})
    plt.close(fig)
    if paper_figures is not None:
        paper_figures.mkdir(parents=True, exist_ok=True)
        if target.resolve() != (paper_figures / target.name).resolve():
            shutil.copyfile(target, paper_figures / target.name)
    print(json.dumps({"asset": target.name,
                      "size_bp": [round(v * 72, 5) for v in fig.get_size_inches()]}))


def configure_fonts():
    # Discover Windows fonts without a machine-specific absolute path.
    import os
    windows_fonts = Path(os.environ.get("WINDIR", "")) / "Fonts"
    for name in ("times.ttf", "timesi.ttf", "timesbd.ttf"):
        path = windows_fonts / name
        if path.is_file():
            font_manager.fontManager.addfont(path)
    for family in ("Times New Roman", "Liberation Serif", "STIXGeneral"):
        try:
            path = font_manager.findfont(
                font_manager.FontProperties(family=family),
                fallback_to_default=False)
            break
        except ValueError:
            continue
    else:
        raise RuntimeError("Install a Times-family font.")
    plt.rcParams.update({
        "font.family": family, "font.size": 8,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "pdf.use14corefonts": False, "text.usetex": False,
        "mathtext.fontset": "custom", "mathtext.rm": family,
        "mathtext.it": family + ":italic", "mathtext.bf": family + ":bold",
        "mathtext.fallback": None, "axes.unicode_minus": True,
        "axes.labelpad": 5, "legend.fontsize": 8,
    })
    print(json.dumps({"font_family": family, "font_file": path}))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "results/derived")
    parser.add_argument("--output", type=Path, default=ROOT / "figures")
    parser.add_argument("--paper-figures", type=Path)
    args = parser.parse_args()
    configure_fonts()
    allocation = read_rows(args.data / "allocation.csv")
    values = {key: [float(Fraction(row[key])) for row in allocation]
              for key in allocation[0]}
    for row in allocation:
        x = Fraction(row["rate0"])
        if (Fraction(row["decreasing_cut"]) != 10 - 2*x
                or Fraction(row["increasing_cut"]) != 6 + 2*x
                or Fraction(row["pool"]) != max(11-4*x, 10-2*x, 6+2*x)):
            raise ValueError("Allocation CSV differs from the exact running-instance cuts.")
    fig, ax = canvas(245, 161, (30.96, 27, 206.23003, 96.90349))
    ax.plot(values["rate0"], values["pool"], color="black", linewidth=1,
            label="Exact robust pool")
    ax.plot(values["rate0"], values["decreasing_cut"], color="black",
            linewidth=.6, linestyle=(0, (3, 2)), label=r"Cut $10-2x$")
    ax.plot(values["rate0"], values["increasing_cut"], color="black",
            linewidth=.7, linestyle=":", label=r"Cut $6+2x$")
    ax.plot([1], [8], "o", color="black", markersize=4, clip_on=True)
    ax.text(1.04, 7.55, r"$(1,8)$", va="top", ha="left", fontsize=8)
    ax.set(xlim=(.25, 1.5), ylim=(6, 10), xticks=[.25, .5, 1, 1.5],
           yticks=[6, 7, 8, 9, 10], xlabel=r"Tenant 0 reservation $x$",
           ylabel="Pool capacity (units)")
    ax.set_xticklabels(["0.25", "0.5", "1", "1.5"])
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.025),
              frameon=False, borderaxespad=0, handlelength=2,
              labelspacing=.22, borderpad=0)
    save(fig, "allocation", args.output, args.paper_figures)
    corners = read_rows(args.data / "corners.csv")
    if any(int(row["endpoint_peak"]) != 1
           or int(row["exact_peak"]) != int(row["bursts"]) for row in corners):
        raise ValueError("Corner control no longer matches the retained proposition.")
    fig, ax = canvas(244, 121, (31.55, 26, 206.22397, 91.23283))
    xs = [int(row["bursts"]) for row in corners]
    ax.plot(xs, [int(row["exact_peak"]) for row in corners], color="black",
            linewidth=.6, marker="o", markersize=2.4,
            label="Exact window bound")
    ax.plot(xs, [int(row["endpoint_peak"]) for row in corners], color="black",
            linewidth=.6, linestyle=(0, (3, 2)), marker="s", markersize=2.4,
            label="All endpoint corners")
    ax.set(xlim=(2, 10), ylim=(0, 11), xticks=[2, 4, 6, 8, 10],
           yticks=[0, 2, 4, 6, 8, 10], xlabel=r"Number of bursts $m$",
           ylabel="Peak queue (units)")
    ax.legend(loc="upper left", frameon=False, borderpad=.2,
              labelspacing=.25, handlelength=2)
    save(fig, "corners", args.output, args.paper_figures)
    print(json.dumps({"allocation_rows": len(allocation), "corner_rows": len(corners)}))


if __name__ == "__main__":
    main()
