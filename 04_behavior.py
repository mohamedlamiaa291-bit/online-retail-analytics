"""Chapter 4 - Behavior (when do customers buy?) | needs sales_clean.csv from 01_cleaning.py
Neutral palette for now; swap PALETTE when the portfolio theme is chosen."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
SRC = OUT / "sales_clean.csv"
PALETTE = {"y2010": "#94A3B8", "y2011": "#0D9488", "accent": "#F59E0B", "text": "#0F172A", "low": "#F0FDFA"}
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]  # Saturday: 1 trading day only

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#CBD5E1", "axes.labelcolor": PALETTE["text"],
                     "xtick.color": PALETTE["text"], "ytick.color": PALETTE["text"]})

s = pd.read_csv(SRC, usecols=["Invoice", "TotalAmount", "DayOfWeek", "Hour", "IsOutlier"])
s = s[~s.IsOutlier]  # extreme lines would distort which hour looks "busy"

# ---- Chart 1: heatmap weekday x hour ----
hm = s[s.DayOfWeek.isin(DAYS) & s.Hour.between(7, 20)].pivot_table(
    index="DayOfWeek", columns="Hour", values="TotalAmount", aggfunc="sum").reindex(DAYS).fillna(0)
cmap = LinearSegmentedColormap.from_list("theme", [PALETTE["low"], PALETTE["y2011"]])
fig, ax = plt.subplots(figsize=(11, 4.6))
im = ax.imshow(hm / 1e3, cmap=cmap, aspect="auto")
ax.set_xticks(range(len(hm.columns))); ax.set_xticklabels([f"{h}:00" for h in hm.columns], fontsize=9)
ax.set_yticks(range(len(DAYS))); ax.set_yticklabels(DAYS)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
for i in range(hm.shape[0]):
    for j in range(hm.shape[1]):
        v = hm.iloc[i, j] / 1e3
        if v >= 150:
            ax.text(j, i, f"{v:,.0f}", ha="center", va="center", fontsize=8.5,
                    color="white" if v > 330 else PALETTE["text"])
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02); cb.set_label("Revenue (£K)"); cb.outline.set_visible(False)
ax.set_title("Midday on Tue-Thu is when the money comes in", loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch4_heatmap.png", dpi=200); plt.close(fig)

# ---- Chart 2: revenue share + avg order value by weekday ----
d = s.groupby("DayOfWeek").agg(rev=("TotalAmount", "sum"), orders=("Invoice", "nunique")).reindex(DAYS)
d["share"] = d.rev / d.rev.sum(); d["aov"] = d.rev / d.orders
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
cols = [PALETTE["accent"] if k == d.share.idxmax() else PALETTE["y2011"] for k in d.index]
axes[0].bar([k[:3] for k in d.index], d.share * 100, color=cols, width=0.6)
for i, v in enumerate(d.share * 100): axes[0].text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=9.5, fontweight="bold")
axes[0].set_title("Share of revenue by day", fontsize=11, loc="left"); axes[0].set_yticks([]); axes[0].spines["left"].set_visible(False)
axes[0].set_ylim(0, d.share.max() * 100 * 1.2)
cols2 = [PALETTE["accent"] if k == "Sunday" else PALETTE["y2010"] for k in d.index]
axes[1].bar([k[:3] for k in d.index], d.aov, color=cols2, width=0.6)
for i, v in enumerate(d.aov): axes[1].text(i, v + 6, f"£{v:,.0f}", ha="center", fontsize=9.5, fontweight="bold")
axes[1].set_title("Average order value by day", fontsize=11, loc="left"); axes[1].set_yticks([]); axes[1].spines["left"].set_visible(False)
axes[1].set_ylim(0, d.aov.max() * 1.2)
fig.suptitle("Thursday sells the most; Sunday orders are the smallest", x=0.02, ha="left", fontsize=13, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch4_weekday.png", dpi=200); plt.close(fig)

# ---- Chart 3: revenue share by hour ----
h = s[s.Hour.between(7, 20)].groupby("Hour").TotalAmount.sum()
h = h / h.sum() * 100
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.bar(h.index, h.values, color=[PALETTE["accent"] if k == h.idxmax() else PALETTE["y2011"] for k in h.index], width=0.7)
ax.set_xticks(h.index); ax.set_xticklabels([f"{k}:00" for k in h.index], fontsize=9)
ax.set_ylabel("% of revenue"); ax.grid(axis="y", alpha=0.25)
core = h.loc[10:15].sum()
ax.set_title(f"10:00-16:00 brings {core:.0f}% of revenue, with a peak at {h.idxmax()}:00",
             loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch4_hourly.png", dpi=200); plt.close(fig)

print(d.round(3)); print(f"Core hours 10-16: {core:.1f}% | peak hour: {h.idxmax()}:00 ({h.max():.1f}%)")
