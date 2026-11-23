"""Chapter 5 - RFM Segmentation | needs customers_clean.csv and cancelled.csv from 01_cleaning.py
Monetary value is NET of each customer's cancellations (this also neutralises the two giant
orders that were cancelled afterwards). Neutral palette for now; swap PALETTE for the final theme."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
PALETTE = {"text": "#0F172A", "grid": "#CBD5E1"}
SEG_COLORS = {"Champions": "#0F766E", "Loyal": "#5EEAD4", "Promising": "#86EFAC",
              "Needs Attention": "#FCD34D", "At Risk": "#F59E0B", "Lost": "#94A3B8"}
ORDER = list(SEG_COLORS)

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": PALETTE["grid"], "axes.labelcolor": PALETTE["text"],
                     "xtick.color": PALETTE["text"], "ytick.color": PALETTE["text"]})

c = pd.read_csv(f"{OUT}/customers_clean.csv", usecols=["Invoice", "InvoiceDate", "TotalAmount", "Customer ID"],
                parse_dates=["InvoiceDate"])
x = pd.read_csv(f"{OUT}/cancelled.csv", usecols=["TotalAmount", "Customer ID"]).dropna(subset=["Customer ID"])

snapshot = c.InvoiceDate.max().normalize() + pd.Timedelta(days=1)  # 2011-12-10
r = c.groupby("Customer ID").agg(last=("InvoiceDate", "max"), Frequency=("Invoice", "nunique"),
                                 gross=("TotalAmount", "sum"))
r["Recency"] = (snapshot - r["last"]).dt.days
r["Monetary"] = r.gross + x.groupby("Customer ID").TotalAmount.sum().reindex(r.index).fillna(0)
r = r[r.Monetary > 0].copy()  # drop customers whose cancellations wiped out their purchases

# 1-5 scores (quintiles); rank(first) breaks the many ties in Frequency
r["R"] = pd.qcut(r.Recency, 5, labels=[5, 4, 3, 2, 1]).astype(int)
r["F"] = pd.qcut(r.Frequency.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
r["M"] = pd.qcut(r.Monetary.rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(a):
    if a.R >= 4 and a.F >= 4: return "Champions"
    if a.R >= 3 and a.F >= 3: return "Loyal"
    if a.R >= 4 and a.F <= 2: return "Promising"
    if a.R == 3 and a.F <= 2: return "Needs Attention"
    if a.R <= 2 and a.F >= 3: return "At Risk"
    return "Lost"


r["Segment"] = r.apply(segment, axis=1)
r.reset_index()[["Customer ID", "Recency", "Frequency", "Monetary", "R", "F", "M", "Segment"]].round(2) \
    .to_csv(f"{OUT}/rfm_customers.csv", index=False)

g = r.groupby("Segment").agg(customers=("Monetary", "size"), revenue=("Monetary", "sum"),
                             med_recency=("Recency", "median"), med_orders=("Frequency", "median"),
                             med_value=("Monetary", "median")).reindex(ORDER)
g["cust_share"] = g.customers / g.customers.sum() * 100
g["rev_share"] = g.revenue / g.revenue.sum() * 100

# ---- Chart 1: share of customers vs share of revenue ----
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
for ax, col, title in zip(axes, ("cust_share", "rev_share"), ("% of customers", "% of revenue")):
    ax.barh(ORDER, g[col], color=[SEG_COLORS[k] for k in ORDER], height=0.62)
    for i, v in enumerate(g[col]): ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=10, fontweight="bold")
    ax.set_title(title, loc="left", fontsize=11); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
    ax.set_xlim(0, 85)
axes[0].invert_yaxis()
fig.suptitle(f"Champions are {g.cust_share['Champions']:.0f}% of customers but {g.rev_share['Champions']:.0f}% of revenue",
             x=0.02, ha="left", fontsize=13, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch5_segments.png", dpi=200); plt.close(fig)

# ---- Chart 2: recency vs frequency map ----
fig, ax = plt.subplots(figsize=(9.5, 5.6))
for k in ORDER[::-1]:
    d = r[r.Segment == k]
    ax.scatter(d.Recency, d.Frequency, s=np.clip(d.Monetary / 120, 6, 160), color=SEG_COLORS[k], alpha=0.55,
               label=k, edgecolor="white", linewidth=0.3)
ax.set_yscale("log"); ax.set_xlabel("Days since last purchase"); ax.set_ylabel("Number of orders (log scale)")
ax.grid(alpha=0.25)
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13), fontsize=9, markerscale=0.8)
fig.tight_layout(); fig.savefig(f"{OUT}/ch5_rfm_map.png", dpi=200); plt.close(fig)

# ---- Chart 3: customer concentration ----
m = r.Monetary.sort_values(ascending=False).to_numpy()
cum = np.cumsum(m) / m.sum() * 100; xs = np.arange(1, len(m) + 1) / len(m) * 100
top1, top20 = cum[int(len(m) * 0.01) - 1], cum[int(len(m) * 0.20) - 1]
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.plot(xs, cum, color="#0F766E", lw=2.8); ax.fill_between(xs, cum, color="#0F766E", alpha=0.08)
for px, py, dy in ((1, top1, 8), (20, top20, -18)):
    ax.scatter([px], [py], color="#F59E0B", s=70, zorder=5)
    ax.annotate(f"Top {px}% of customers\n= {py:.0f}% of revenue", (px, py), xytext=(px + 14, py + dy),
                fontsize=11, color=PALETTE["text"], arrowprops=dict(arrowstyle="-", color="#94A3B8"))
ax.set_xlabel("% of customers (ranked by value)"); ax.set_ylabel("Cumulative % of revenue")
ax.set_xlim(0, 100); ax.set_ylim(0, 102); ax.grid(alpha=0.25)
ax.set_title("Revenue depends on a small group of customers", loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch5_concentration.png", dpi=200); plt.close(fig)

print(g.round(1).to_string())
print(f"\nTop 1% = {top1:.0f}% | Top 20% = {top20:.0f}% | one-time buyers: {(r.Frequency == 1).mean():.0%} | scored customers: {len(r):,}")
