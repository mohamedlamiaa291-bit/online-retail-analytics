"""Chapter 3 - Geography & Products | needs sales_clean.csv from 01_cleaning.py
Neutral palette for now; swap PALETTE when the portfolio theme is chosen."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
SRC = OUT / "sales_clean.csv"
PALETTE = {"y2010": "#94A3B8", "y2011": "#0D9488", "accent": "#F59E0B", "text": "#0F172A"}

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#CBD5E1", "axes.labelcolor": PALETTE["text"],
                     "xtick.color": PALETTE["text"], "ytick.color": PALETTE["text"]})

s = pd.read_csv(SRC, usecols=["Invoice", "StockCode", "Description", "Quantity", "TotalAmount",
                              "Country", "Customer ID", "IsOutlier"])
total = s.TotalAmount.sum()

# ---------- Geography ----------
g = s.groupby("Country").agg(rev=("TotalAmount", "sum"), orders=("Invoice", "nunique"),
                             customers=("Customer ID", "nunique")).reset_index()
g["share"] = g.rev / total
g["aov"] = g.rev / g.orders
uk = g[g.Country == "United Kingdom"].iloc[0]
top = g[g.Country != "United Kingdom"].nlargest(10, "rev").iloc[::-1]

fig, ax = plt.subplots(figsize=(10, 5.6))
bars = ax.barh(top.Country, top.rev / 1e3, color=PALETTE["y2011"], height=0.62)
for b, (_, r) in zip(bars, top.iterrows()):
    ax.text(b.get_width() + 8, b.get_y() + b.get_height() / 2,
            f"£{r.rev/1e3:,.0f}K  ·  {int(r.customers)} customers  ·  AOV £{r.aov:,.0f}",
            va="center", fontsize=9, color=PALETTE["text"])
ax.set_xlim(0, top.rev.max() / 1e3 * 1.85); ax.set_xlabel("Revenue (£K)")
ax.set_title(f"Beyond the UK ({uk.share:.1%} of revenue): Ireland and the Netherlands lead",
             loc="left", fontsize=13, fontweight="bold", color=PALETTE["text"])
ax.grid(axis="x", alpha=0.25)
fig.tight_layout(); fig.savefig(f"{OUT}/ch3_countries.png", dpi=200); plt.close(fig)

# ---------- Products (extreme lines excluded; they were cancelled afterwards) ----------
p = s[~s.IsOutlier].groupby("StockCode").agg(desc=("Description", lambda x: x.mode()[0]),
                                            rev=("TotalAmount", "sum"), units=("Quantity", "sum"),
                                            orders=("Invoice", "nunique")).reset_index()
t10 = p.nlargest(10, "rev").iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.barh(t10.desc.str.title().str.slice(0, 34), t10.rev / 1e3, color=PALETTE["y2011"], height=0.62)
for i, (_, r) in enumerate(t10.iterrows()):
    ax.text(r.rev / 1e3 + 4, i, f"£{r.rev/1e3:,.0f}K  ·  {int(r.orders):,} orders", va="center", fontsize=9, color=PALETTE["text"])
ax.set_xlim(0, t10.rev.max() / 1e3 * 1.4); ax.set_xlabel("Revenue (£K)")
ax.set_title("Top 10 products by revenue", loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
ax.grid(axis="x", alpha=0.25)
fig.tight_layout(); fig.savefig(f"{OUT}/ch3_top_products.png", dpi=200); plt.close(fig)

# ---------- Pareto ----------
r = p.rev.sort_values(ascending=False).to_numpy()
cum = np.cumsum(r) / r.sum(); x = np.arange(1, len(r) + 1) / len(r) * 100
share10 = cum[int(len(r) * 0.10) - 1]
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.plot(x, cum * 100, color=PALETTE["y2011"], lw=2.8)
ax.fill_between(x, cum * 100, color=PALETTE["y2011"], alpha=0.08)
ax.scatter([10], [share10 * 100], color=PALETTE["accent"], s=70, zorder=5)
ax.annotate(f"Top 10% of products\n= {share10:.0%} of revenue", (10, share10 * 100), xytext=(28, share10 * 100 - 22),
            fontsize=11, color=PALETTE["text"], arrowprops=dict(arrowstyle="-", color="#94A3B8"))
ax.set_xlabel("% of products (ranked by revenue)"); ax.set_ylabel("Cumulative % of revenue")
ax.set_xlim(0, 100); ax.set_ylim(0, 102); ax.grid(alpha=0.25)
ax.set_title("A small share of products drives most revenue", loc="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(); fig.savefig(f"{OUT}/ch3_pareto.png", dpi=200); plt.close(fig)

uk_df = s[s.Country == "United Kingdom"]; nuk_df = s[s.Country != "United Kingdom"]
print(f"UK share of revenue: {uk.share:.1%} | countries: {len(g)}")
print(f"AOV UK £{uk_df.TotalAmount.sum()/uk_df.Invoice.nunique():,.0f} vs non-UK £{nuk_df.TotalAmount.sum()/nuk_df.Invoice.nunique():,.0f}")
print(f"Top 10% of products = {share10:.1%} of revenue | products: {len(p):,}")
