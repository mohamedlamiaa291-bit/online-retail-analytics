"""Chapter 2 - Sales Overview | needs sales_clean.csv from 01_cleaning.py
Neutral palette for now; swap PALETTE when the portfolio theme is chosen."""
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
SRC = OUT / "sales_clean.csv"
PALETTE = {"y2010": "#94A3B8", "y2011": "#0D9488", "accent": "#F59E0B", "text": "#0F172A"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#CBD5E1", "axes.labelcolor": PALETTE["text"],
                     "xtick.color": PALETTE["text"], "ytick.color": PALETTE["text"]})

s = pd.read_csv(SRC, usecols=["Invoice", "TotalAmount", "Year", "Month", "YearMonth", "IsPartialMonth"])
s = s[~s.IsPartialMonth]  # Dec 2011 is incomplete (data ends 9 Dec)

m = s.groupby(["Year", "Month"]).agg(rev=("TotalAmount", "sum"), orders=("Invoice", "nunique")).reset_index()
m["aov"] = m.rev / m.orders

# ---- Chart 1: revenue 2010 vs 2011 (Jan-Nov comparable) ----
fig, ax = plt.subplots(figsize=(10, 5.2))
for yr, col in ((2010, PALETTE["y2010"]), (2011, PALETTE["y2011"])):
    d = m[(m.Year == yr) & (m.Month <= 11)]
    ax.plot(d.Month, d.rev / 1e6, marker="o", lw=2.6, color=col, label=str(yr))
ax.axvspan(8.6, 11.4, color=PALETTE["accent"], alpha=0.12)
ax.text(10, 0.42, "Sep-Nov peak season\n~40% of Jan-Nov sales", ha="center", fontsize=10, color=PALETTE["text"])
ax.set_xticks(range(1, 12)); ax.set_xticklabels(MONTHS[:11])
ax.set_ylabel("Revenue (£M)"); ax.set_ylim(0.3, 1.6)
ax.set_title("Revenue peaks every November, both years", loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
ax.legend(frameon=False); ax.grid(axis="y", alpha=0.25)
fig.tight_layout(); fig.savefig(f"{OUT}/ch2_revenue_yoy.png", dpi=200); plt.close(fig)

# ---- Chart 2: orders vs average order value (Jan-Nov) ----
j = m[m.Month <= 11].groupby("Year").agg(rev=("rev", "sum"), orders=("orders", "sum"))
j["aov"] = j.rev / j.orders
fig, axes = plt.subplots(1, 3, figsize=(10, 3.8))
for ax, (col, title, fmt) in zip(axes, (("rev", "Revenue (£M)", lambda v: f"{v/1e6:.2f}"),
                                         ("orders", "Orders", lambda v: f"{v:,.0f}"),
                                         ("aov", "Avg order value (£)", lambda v: f"{v:,.0f}"))):
    ax.bar(["2010", "2011"], j[col], color=[PALETTE["y2010"], PALETTE["y2011"]], width=0.55)
    for i, v in enumerate(j[col]):
        ax.text(i, v, fmt(v), ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_title(title, fontsize=11, color=PALETTE["text"]); ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_ylim(0, j[col].max() * 1.18)
fig.suptitle("2011 grew through bigger baskets, not more orders (Jan-Nov)", x=0.02, ha="left", fontsize=13, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch2_orders_vs_aov.png", dpi=200); plt.close(fig)

# ---- Chart 3: monthly average order value over time ----
m["date"] = pd.to_datetime(dict(year=m.Year, month=m.Month, day=1))
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(m.date, m.aov, color=PALETTE["y2011"], lw=2.4)
ax.fill_between(m.date, m.aov, m.aov.min() * 0.9, color=PALETTE["y2011"], alpha=0.08)
ax.set_ylabel("£ per order"); ax.set_ylim(m.aov.min() * 0.9, m.aov.max() * 1.08)
ax.set_title("Average order value is trending up", loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
ax.grid(axis="y", alpha=0.25)
fig.tight_layout(); fig.savefig(f"{OUT}/ch2_aov_trend.png", dpi=200); plt.close(fig)

print(j.round(0))
print("Revenue YoY (Jan-Nov):", f"{j.rev[2011]/j.rev[2010]-1:+.1%}",
      "| Orders:", f"{j.orders[2011]/j.orders[2010]-1:+.1%}",
      "| AOV:", f"{j.aov[2011]/j.aov[2010]-1:+.1%}")
