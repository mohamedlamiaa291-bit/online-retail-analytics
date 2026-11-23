"""Chapter 6 - Cohort Retention | needs customers_clean.csv from 01_cleaning.py
Cohort = month of a customer's first purchase in the data; retention = % of the cohort buying again in month N.
Caveats handled: Dec 2011 is excluded (incomplete month) and the Dec 2009 cohort is flagged (*) because it
contains customers who were already active before the data starts, so it is not a true "new customer" cohort.
Same effect, smaller: 2010 cohorts also contain some pre-data customers, so the 2010 vs 2011 drop in new customers is partly a data-start artefact.
Neutral palette for now; swap PALETTE for the final theme."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
SRC = OUT / "customers_clean.csv"
PALETTE = {"main": "#0D9488", "accent": "#F59E0B", "grey": "#94A3B8", "text": "#0F172A", "low": "#F0FDFA"}

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#CBD5E1", "axes.labelcolor": PALETTE["text"],
                     "xtick.color": PALETTE["text"], "ytick.color": PALETTE["text"]})

c = pd.read_csv(SRC, usecols=["Customer ID", "InvoiceDate", "IsPartialMonth"], parse_dates=["InvoiceDate"])
c = c[~c.IsPartialMonth]
c["month"] = c.InvoiceDate.dt.to_period("M")
c = c.join(c.groupby("Customer ID").month.min().rename("cohort"), on="Customer ID")
c["k"] = (c.month - c.cohort).apply(lambda x: x.n)

t = c.groupby(["cohort", "k"])["Customer ID"].nunique().unstack()
size = t[0]
ret = t.div(size, axis=0) * 100
ret.round(1).assign(cohort_size=size).to_csv(f"{OUT}/cohort_retention.csv")

true_cohorts = ret.iloc[1:]  # everything except Dec 2009
avg = true_cohorts.mean()
full = ret.loc["2010-01":"2010-11"]  # cohorts observed for all 12 months: same cohort mix at every month of the curve

# ---- Chart 1: cohort heatmap (months 1-12) ----
cols = list(range(1, 13))
hm = ret[cols]
labels = [f"{p.strftime('%b %Y')}{'*' if str(p) == '2009-12' else ''}  ({int(size[p])})" for p in hm.index]
cmap = LinearSegmentedColormap.from_list("theme", [PALETTE["low"], PALETTE["main"]])
fig, ax = plt.subplots(figsize=(11, 8))
im = ax.imshow(np.ma.masked_invalid(hm.values), cmap=cmap, vmin=0, vmax=40, aspect="auto")
ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"M{k}" for k in cols])
ax.set_yticks(range(len(hm))); ax.set_yticklabels(labels, fontsize=9)
ax.xaxis.tick_top(); ax.tick_params(length=0)
for sp in ax.spines.values(): sp.set_visible(False)
for i in range(hm.shape[0]):
    for j in range(hm.shape[1]):
        v = hm.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8, color="white" if v > 24 else PALETTE["text"])
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.set_label("% of cohort buying again"); cb.outline.set_visible(False)
fig.text(0.01, 0.01, "* Dec 2009 includes customers who were already active before the data starts.  Cohort size in brackets.",
         fontsize=8.5, color="#64748B")
fig.suptitle("Cohort retention: how many new customers come back?", x=0.01, ha="left", fontsize=14, fontweight="bold", color=PALETTE["text"])
fig.tight_layout(rect=(0, 0.02, 1, 0.97)); fig.savefig(f"{OUT}/ch6_cohort_heatmap.png", dpi=200); plt.close(fig)

# ---- Chart 2: average retention curve ----
curve = full.mean().loc[1:12]
fig, ax = plt.subplots(figsize=(9.5, 4.8))
ax.plot(curve.index, curve.values, color=PALETTE["main"], lw=2.8, marker="o")
ax.fill_between(curve.index, curve.values, color=PALETTE["main"], alpha=0.08)
ax.scatter([12], [curve[12]], color=PALETTE["accent"], s=90, zorder=5)
ax.annotate(f"Month 12: {curve[12]:.0f}%\nannual repeat, led by Sep-Nov cohorts", (12, curve[12]), xytext=(7.2, curve[12] + 5.5),
            fontsize=10.5, color=PALETTE["text"], arrowprops=dict(arrowstyle="-", color=PALETTE["grey"]))
ax.set_xticks(curve.index); ax.set_xlabel("Months since first purchase"); ax.set_ylabel("% of cohort active")
ax.set_ylim(0, 30); ax.grid(alpha=0.25)
ax.set_title(f"About {curve[1]:.0f}% return in month 1, then it fades and rebounds at month 12",
             loc="left", fontsize=13, fontweight="bold", color=PALETTE["text"])
fig.text(0.01, 0.01, f"Average of the {len(full)} cohorts Jan-Nov 2010, each observed for all 12 months.", fontsize=8.5, color="#64748B")
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(f"{OUT}/ch6_retention_curve.png", dpi=200); plt.close(fig)

# ---- Chart 3: new customers per month ----
new = size.copy(); new.index = new.index.to_timestamp()
fig, ax = plt.subplots(figsize=(10.5, 4.6))
colors = [PALETTE["grey"] if i == 0 else PALETTE["main"] for i in range(len(new))]
ax.bar(new.index, new.values, width=22, color=colors)
ax.set_ylabel("New customers"); ax.grid(axis="y", alpha=0.25)
p10 = size.loc["2010-09":"2010-11"].sum(); p11 = size.loc["2011-09":"2011-11"].sum()
ax.set_title(f"Sep-Nov new customers fell {abs(p11/p10-1):.0%} year on year, partly a data-start effect",
             loc="left", fontsize=13, fontweight="bold", color=PALETTE["text"])
ax.annotate("Dec 2009*: includes customers\nalready active before the data starts", (new.index[0], new.iloc[0]),
            xytext=(new.index[0] + pd.Timedelta(days=40), new.iloc[0] * 0.93), va="top", fontsize=9, color="#64748B")
fig.text(0.01, 0.01, "Customers first seen in 2010 include some who were active before Dec 2009, so 2010 'new' customers are overstated vs 2011.",
         fontsize=8.5, color="#64748B")
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(f"{OUT}/ch6_new_customers.png", dpi=200); plt.close(fig)

print("Curve (Jan-Nov 2010 cohorts):", curve.loc[[1, 3, 6, 9, 12]].round(1).to_dict())
print("New customers Sep-Nov 2010:", int(p10), "| 2011:", int(p11), f"| change {p11/p10-1:+.0%}")
# like-for-like year comparison: same calendar cohorts in both years
for k, last in ((1, 10), (3, 8)):
    a = ret.loc["2010-01":f"2010-{last:02d}", k].mean(); b = ret.loc["2011-01":f"2011-{last:02d}", k].mean()
    print(f"Jan-{last} cohorts, month {k}: 2010 {a:.1f}% vs 2011 {b:.1f}%")
