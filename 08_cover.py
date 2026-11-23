"""Portfolio cover images, one per theme."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
THEMES = {"midnight": dict(bg="#0F172A", card="#1E293B", tx="#F1F5F9", mu="#94A3B8", c1="#F5B942"),
          "rose": dict(bg="#FFF7F0", card="#FFFFFF", tx="#3B1D3A", mu="#8B6B8A", c1="#7C3AED"),
          "fresh": dict(bg="#F1F5F9", card="#FFFFFF", tx="#0F172A", mu="#64748B", c1="#0D9488")}
STATS = [("£19.6M", "revenue"), ("1.0M", "transactions"), ("5,832", "customers"), ("43", "countries")]
for name, t in THEMES.items():
    fig = plt.figure(figsize=(16, 9), facecolor=t["bg"]); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 16); ax.set_ylim(0, 9); ax.axis("off")
    ax.text(1, 7.4, "RETAIL ANALYTICS  ·  DEC 2009 – DEC 2011", color=t["c1"], fontsize=15, fontweight="bold")
    ax.text(1, 5.9, "From 1 million transactions", color=t["tx"], fontsize=44, fontweight="bold")
    ax.text(1, 4.8, "to business decisions", color=t["c1"], fontsize=44, fontweight="bold")
    ax.text(1, 3.9, "Sales seasonality · RFM segments · Cohort retention · Market basket · Forecast", color=t["mu"], fontsize=16)
    for i, (v, l) in enumerate(STATS):
        x = 1 + i * 3.6
        ax.add_patch(FancyBboxPatch((x, 1.1), 3.3, 1.9, boxstyle="round,pad=0.02,rounding_size=0.2", fc=t["card"], ec=t["mu"], lw=0.6, alpha=0.95))
        ax.text(x + 0.3, 2.1, v, color=t["c1"], fontsize=30, fontweight="bold"); ax.text(x + 0.3, 1.5, l, color=t["mu"], fontsize=14)
    fig.savefig(f"{OUT}/cover_{name}.png", dpi=120, facecolor=t["bg"]); plt.close(fig)
