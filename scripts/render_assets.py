"""Render editable vector branding and charts from actual invariant-study output."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".skillloom/mpl-cache"))


def render():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    brand = ROOT / "assets/brand"
    figures = ROOT / "assets/figures"
    brand.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    # Original, editable code-native icon. Not a trace of the generated card.
    icon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="Skill Loom icon">
<rect width="256" height="256" rx="54" fill="#F3F0E8"/>
<path d="M64 50v106c0 29 22 50 50 50h68" fill="none" stroke="#172632" stroke-width="29" stroke-linecap="square"/>
<path d="M50 94h106c28 0 50 22 50 50v52" fill="none" stroke="#147D7A" stroke-width="29" stroke-linecap="square"/>
<path d="M108 50v66c0 17 13 30 30 30h68" fill="none" stroke="#DC593A" stroke-width="29" stroke-linecap="square"/>
<path d="M64 124v34" fill="none" stroke="#172632" stroke-width="29"/>
</svg>'''
    (brand / "icon.svg").write_text(icon, encoding="utf-8")
    values = json.loads((ROOT / "research/results/invariants.json").read_text())['summary']
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.4), gridspec_kw={"width_ratios": [1.45, 1]})
    fig.patch.set_facecolor("#F3F0E8")
    panels = [(["unchecked-copy", "static-only", "guarded"], ["Unchecked copy", "Static check + copy", "Reviewed transaction"], 8, "A  File-change contracts"),
              (["declaration-only", "bound-receipt"], ["Declared pass only", "Bound receipt"], 4, "B  Evidence contracts")]
    for axis, (keys, labels, maximum, title) in zip(axes, panels):
        axis.set_facecolor("#F3F0E8")
        counts = [values[key]["satisfied"] for key in keys]
        axis.barh(labels, counts, color=["#A7B1B5"] * (len(keys)-1) + ["#147D7A"], height=.54)
        axis.invert_yaxis()
        for index, value in enumerate(counts):
            axis.text(value + .12, index, f"{value}/{maximum}", va="center", color="#172632", weight="bold")
        axis.set_xlim(0, maximum + 1.3)
        axis.set_xticks(range(0, maximum + 1, 2))
        axis.set_xlabel("Contracts satisfied (count)")
        axis.set_title(title, loc="left", pad=20, weight="bold")
        axis.spines['left'].set_visible(False)
        axis.tick_params(axis='y', length=0)
    fig.suptitle("Do maintenance safeguards meet their stated contracts?", x=.035, ha="left", y=.98, fontsize=17, weight="bold", color="#172632")
    fig.text(.035, .045, "12 selected deterministic scenarios · simple reference comparators · no LLM accuracy or token-saving claim", fontsize=9, color="#52606A")
    fig.tight_layout(rect=(0,.09,1,.88), w_pad=4)
    for extension in ("png", "svg", "pdf"):
        fig.savefig(figures / f"invariant-study.{extension}", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    return {"figure": "assets/figures/invariant-study", "source": "research/results/invariants.json", "icon": "assets/brand/icon.svg"}


if __name__ == "__main__":
    print(json.dumps(render(), indent=2))
