"""Chapter 7 - Market Basket + Forecast | needs sales_clean.csv, rfm_customers.csv, cohort_retention.csv
Also dumps dashboard_data.json used by the dashboard."""
import json
import re
import numpy as np
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"          # all generated files go here
OUT.mkdir(exist_ok=True)
s = pd.read_csv(f"{OUT}/sales_clean.csv", usecols=["Invoice", "StockCode", "Description", "InvoiceDate", "Quantity",
                "TotalAmount", "Country", "Year", "Month", "YearMonth", "DayOfWeek", "Hour", "IsOutlier", "IsPartialMonth"])
clean = s[~s.IsOutlier]

# ---------------- Market basket (top 250 products, pairs with support >= 1%) ----------------
top = clean.groupby("StockCode").Invoice.nunique().nlargest(250).index
b = clean[clean.StockCode.isin(top)].drop_duplicates(["Invoice", "StockCode"])
X = pd.crosstab(b.Invoice, b.StockCode).clip(upper=1).astype("float32")
n = len(X); co = X.T.values @ X.values; cnt = np.diag(co); codes = X.columns
name = clean.groupby("StockCode").Description.agg(lambda x: x.mode()[0])
rows = []
for i in range(len(codes)):
    for j in range(i + 1, len(codes)):
        sup = co[i, j] / n
        if sup >= 0.01:
            rows.append((name[codes[i]].title(), name[codes[j]].title(), sup, co[i, j] / cnt[i], co[i, j] / cnt[j],
                         sup / (cnt[i] / n * cnt[j] / n)))
rules = pd.DataFrame(rows, columns=["item_a", "item_b", "support", "conf_a_to_b", "conf_b_to_a", "lift"]) \
    .sort_values("lift", ascending=False)
# Many top pairs are just colour/design/size variants of one product. Heuristic: two items are "variants" when their
# descriptions share >= 2 content words (colour, size, counts removed), unless the only words that differ are two different
# plural nouns (e.g. Paper Cups + Paper Plates = a bundle, not a variant). It is a text rule, so it is imperfect.
COLOURS = set("red blue pink green white black yellow orange purple ivory cream silver gold grey gray brown turquoise lilac "
              "lavender mint multi multicolour large small medium mini big natural".split())
GENERIC = {"set", "of", "piece", "pack", "pk", "and", "in", "with", "a", "the"}
def _toks(d): return [w for w in re.sub(r"[^a-z0-9/ ]", " ", d.lower()).split()
                      if w not in COLOURS and w not in GENERIC and not re.fullmatch(r"s?/?\d+", w)]
def _plural(w): return len(w) > 3 and w.endswith("s")
def _is_variant(a, b):
    ta, tb = _toks(a), _toks(b)
    if len(set(ta) & set(tb)) < 2: return False
    da, db = set(ta) - set(tb), set(tb) - set(ta)   # words that differ
    return not (len(da) == 1 and len(db) == 1 and _plural(*da) and _plural(*db))
rules["variant_pair"] = [_is_variant(a, b) for a, b in zip(rules.item_a, rules.item_b)]
cross = rules[~rules.variant_pair]
rules.round(4).to_csv(f"{OUT}/basket_rules.csv", index=False)
print("Baskets:", n, "| pairs with support>=1%:", len(rules), "| variant pairs:", int(rules.variant_pair.sum()),
      "| cross-product pairs:", len(cross)); print(cross.head(6).round(3).to_string(index=False))

# ---------------- Forecast: seasonal naive x growth, with backtest ----------------
m = s[~s.IsPartialMonth].groupby("YearMonth").TotalAmount.sum()
m.index = pd.PeriodIndex(m.index, freq="M")
growth_hist = m["2010-12":"2011-11"].sum() / m["2009-12":"2010-11"].sum()
# backtest: predict Jan-Nov 2011 from Jan-Nov 2010 (no growth) vs with the true-ahead growth of the prior period
g_bt = m["2010-01":"2010-11"].sum() / m["2009-12":"2010-10"].sum()  # naive trend proxy (~1.0)
act = m["2011-01":"2011-11"]; naive = m["2010-01":"2010-11"].values
mape_naive = float(np.mean(np.abs(act.values - naive) / act.values) * 100)
ma3 = m.shift(1).rolling(3).mean()["2011-01":"2011-11"]
mape_ma = float(np.mean(np.abs(act.values - ma3.values) / act.values) * 100)
# NOTE: sm uses the 2011/2010 ratio of the TEST period itself, so mape_adj is optimistic (look-ahead).
# The honest figure is mape_naive (plain seasonal-naive). The 3-month moving average is a weak baseline for seasonal data.
sm = m["2011-01":"2011-11"].sum() / m["2010-01":"2010-11"].sum()
mape_adj = float(np.mean(np.abs(act.values - naive * sm) / act.values) * 100)
fc = {str(p + 12): float(m[p] * growth_hist) for p in pd.period_range("2010-12", "2011-05", freq="M")}
# sanity check on Dec 2011 using the first 9 days (extreme lines excluded)
d = clean[clean.Month == 12].copy(); d["day"] = pd.to_datetime(d.InvoiceDate).dt.day
d9 = d[d.day <= 9].groupby("Year").TotalAmount.sum()
print(f"Backtest MAPE Jan-Nov 2011  moving-avg3: {mape_ma:.1f}% | seasonal-naive: {mape_naive:.1f}% | seasonal-naive x growth: {mape_adj:.1f}%")
print("Growth factor (Dec10-Nov11 vs Dec09-Nov10):", round(growth_hist, 3))
print("Forecast:", {k: round(v) for k, v in fc.items()})
print("Dec 1-9 revenue by year:", d9.round(0).to_dict())
pd.DataFrame({"month": list(fc), "forecast_gbp": [round(v) for v in fc.values()]}).to_csv(f"{OUT}/forecast.csv", index=False)

# ---------------- Dashboard data ----------------
cl = s[~s.IsPartialMonth]
mm = cl.groupby(["Year", "Month"]).TotalAmount.sum().unstack(0)
rfm = pd.read_csv(f"{OUT}/rfm_customers.csv"); seg = rfm.groupby("Segment").agg(n=("Monetary", "size"), rev=("Monetary", "sum"))
ret = pd.read_csv(f"{OUT}/cohort_retention.csv", index_col=0)
curve = ret.loc["2010-01":"2010-11"][[str(k) for k in range(1, 13)]].mean()  # same cohorts at every month
hm = clean[clean.DayOfWeek.isin(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]) & clean.Hour.between(8, 17)] \
    .pivot_table(index="DayOfWeek", columns="Hour", values="TotalAmount", aggfunc="sum") \
    .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]).fillna(0) / 1e3
pr = clean.groupby("StockCode").agg(d=("Description", lambda x: x.mode()[0]), r=("TotalAmount", "sum")).nlargest(8, "r")
ct = s[s.Country != "United Kingdom"].groupby("Country").TotalAmount.sum().nlargest(6)
data = {
    "m10": [round(mm[2010].get(k, 0) / 1e3) for k in range(1, 12)], "m11": [round(mm[2011].get(k, 0) / 1e3) for k in range(1, 12)],
    "fc": [round(v / 1e3) for v in fc.values()],
    "seg": {k: [int(v.n), round(v.rev / 1e3)] for k, v in seg.iterrows()},
    "ret": [round(v, 1) for v in curve.values],
    "hm": [[round(v) for v in r] for r in hm.values.tolist()],
    "prod": [[r.d.title()[:28], round(r.r / 1e3)] for r in pr.itertuples()],
    "ctry": [[k, round(v / 1e3)] for k, v in ct.items()],
    "pairs": [[r.item_a[:26], r.item_b[:26], round(r.lift, 1)] for r in cross.head(5).itertuples()],
    "mape": [round(mape_ma, 1), round(mape_naive, 1), round(mape_adj, 1)],
}
json.dump(data, open(f"{OUT}/dashboard_data.json", "w"), separators=(",", ":"))
print(len(json.dumps(data)), "bytes of dashboard data")
