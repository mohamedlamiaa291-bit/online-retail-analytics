"""PDF report | needs the chart PNGs from scripts 02-06 and cover_fresh.png from 08_cover.py (all in output/)
One chart per page with key takeaways. Wording avoids claims the data cannot prove."""
from pathlib import Path
import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
W, H = 1456, 819
TEAL, BG, TX, MU, GR = HexColor("#0D9488"), HexColor("#F1F5F9"), HexColor("#0F172A"), HexColor("#64748B"), HexColor("#E2E8F0")
FOOT = "Online Retail Analytics  |  Dec 2009 - Dec 2011"

h_style = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=15, textColor=TEAL, leading=20, spaceAfter=10)
b_style = ParagraphStyle("b", fontName="Helvetica", fontSize=19, textColor=TX, leading=27, leftIndent=14, bulletIndent=0, spaceAfter=12)
t_style = ParagraphStyle("t", fontName="Helvetica", fontSize=17, textColor=TX, leading=23)
th_style = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=17, textColor=white, leading=23)
n_style = ParagraphStyle("n", fontName="Helvetica", fontSize=18, textColor=TX, leading=26, spaceAfter=12)

# (title, chapter, image, takeaways)
PAGES = [
    ("Sales: revenue peaks every November", "Chapter 2", "ch2_revenue_yoy.png", [
        "Sep-Nov is ~40% of Jan-Nov revenue in both years.",
        "Feb and Apr are the weakest months: good moments for promotions.",
        "Dec 2011 is incomplete (data ends 9 Dec) and excluded."]),
    ("Sales: bigger baskets, not more orders", "Chapter 2", "ch2_orders_vs_aov.png", [
        "Jan-Nov 2011 vs 2010: revenue +3.0%.",
        "Orders -3.7%, average order value +7.0% (GBP 476 to 509).",
        "Growth came from larger orders, not from more orders."]),
    ("Geography: beyond the UK", "Chapter 3", "ch3_countries.png", [
        "UK = 85.5% of revenue; 43 countries in total.",
        "Export orders average GBP 853 vs GBP 464 in the UK: larger orders, consistent with wholesale buyers (not verifiable in the data).",
        "Ireland: GBP 623K from only 3 customers, a concentration risk."]),
    ("Products: top sellers", "Chapter 3", "ch3_top_products.png", [
        "Regency Cakestand 3 Tier leads revenue (GBP 331K).",
        "White Hanging Heart T-Light Holder has the most orders (5,365).",
        "Top 10% of products bring 62% of revenue."]),
    ("Behaviour: when customers buy", "Chapter 4", "ch4_heatmap.png", [
        "Tuesday to Thursday around midday is the peak.",
        "Thursday is the strongest day (20.7%); Sunday orders are the smallest (GBP 370).",
        "Saturday is effectively closed."]),
    ("Behaviour: busiest hours", "Chapter 4", "ch4_hourly.png", [
        "10:00-16:00 brings 75% of revenue.",
        "Peak hour is 12:00 (14.4%).",
        "A business-hours pattern is consistent with trade buyers (a hypothesis, customer type is not in the data)."]),
    ("Customers: RFM segments", "Chapter 5", "ch5_segments.png", [
        "Champions: 25% of customers, 70% of revenue.",
        "At Risk: 826 customers, GBP 1.4M past revenue: the best win-back target.",
        "Value is net of each customer's cancellations."]),
    ("Customers: revenue concentration", "Chapter 5", "ch5_concentration.png", [
        "Top 20% of customers = 77% of revenue.",
        "Top 1% (about 58 customers) = 31%.",
        "27% of customers bought only once."]),
    ("Retention: do new customers come back?", "Chapter 6", "ch6_cohort_heatmap.png", [
        "About 20% return in month 1.",
        "Customers return in season: strong Sep-Nov months.",
        "Like-for-like (same calendar cohorts), 2011 is a little better in month 1 (22.7% vs 20.1%) but behind by month 3 (21.8% vs 25.2%): no clear improvement."]),
    ("Retention: the month-12 rebound", "Chapter 6", "ch6_retention_curve.png", [
        "Retention fades to ~14% by month 9, then rebounds to ~18% at month 12.",
        "The curve averages the 11 cohorts of Jan-Nov 2010, all observed for 12 months, so the cohort mix is constant.",
        "The bump comes mostly from Sep-Nov 2010 cohorts (+13, +6 and +10 points vs month 11): customers returning in the next peak season.",
        "Dec 2009 cohort excluded: it includes existing customers."]),
    ("Acquisition: new customers per month", "Chapter 6", "ch6_new_customers.png", [
        "Sep-Nov new customers: 940 in 2010 vs 600 in 2011 (-36%).",
        "Part of this is a data-start effect: 2010 'new' customers include some who were active before Dec 2009.",
        "Treat the size of the drop with caution; track acquisition over a longer history."]),
]


def frame(c, title, right, n, sub=None):
    c.setFillColor(BG); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(TEAL); c.rect(0, H - 98, W, 98, stroke=0, fill=1)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 31); c.drawString(46, H - 62, title)
    if sub:
        c.setFont("Helvetica", 17); c.drawString(46, H - 88, sub)
    c.setFont("Helvetica", 18); c.drawRightString(W - 46, H - 58, right)
    c.setFillColor(MU); c.setFont("Helvetica", 13)
    c.drawString(46, 26, FOOT); c.drawRightString(W - 46, 26, str(n))


def card(c, x, y, w, h):
    c.setFillColor(white); c.setStrokeColor(GR); c.roundRect(x, y, w, h, 22, stroke=1, fill=1)


def para_block(c, items, x, y_top, w, style, bullet=True):
    y = y_top
    for it in items:
        p = Paragraph(it, style, bulletText="\u2022" if bullet else None)
        _, ph = p.wrap(w, 1000); y -= ph; p.drawOn(c, x, y); y -= style.spaceAfter
    return y


def chart_page(c, n, title, chap, img, takeaways):
    frame(c, title, chap, n)
    card(c, 36, 52, 970, 649); card(c, 1032, 52, 388, 649)
    ir = ImageReader(str(OUT / img)); iw, ih = ir.getSize()
    s = min((970 - 40) / iw, (649 - 40) / ih); dw, dh = iw * s, ih * s
    c.drawImage(ir, 36 + (970 - dw) / 2, 52 + (649 - dh) / 2, dw, dh, mask="auto")
    para_block(c, ["KEY TAKEAWAYS"], 1058, 701 - 28, 340, h_style, bullet=False)
    para_block(c, takeaways, 1058, 701 - 66, 340, b_style)


def table_page(c, n, title, chap, sub, rows, widths, col_names, x, y_top):
    data = [[Paragraph(h, th_style) for h in col_names]] + [[Paragraph(str(v), t_style) for v in r] for r in rows]
    t = Table(data, colWidths=widths)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, BG]), ("LINEBELOW", (0, 0), (-1, -1), 0.5, GR),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    tw, th = t.wrap(sum(widths), 1000); t.drawOn(c, x, y_top - th)
    return y_top - th


c = canvas.Canvas(str(OUT / "Online_Retail_Dashboard.pdf"), pagesize=(W, H))
c.setTitle("Online Retail Analytics"); c.setAuthor("Online Retail II analysis")

# 1) cover
cover = ImageReader(str(OUT / "cover_fresh.png")); c.drawImage(cover, 0, 0, W, H); c.showPage()

# 2) executive summary
frame(c, "Executive summary", "", 2, sub="7 insights and what to do about them")
rows = [
    ("Sep-Nov brings ~40% of Jan-Nov sales; November alone ~16%", "Prepare stock and campaigns from August"),
    ("2011 revenue +3% via larger baskets (+7%) while orders fell 3.7%", "Grow order count with re-engagement offers"),
    ("Top 20% of customers = 77% of revenue; top 1% = 31%", "Protect Champions with a loyalty programme"),
    ("826 'At Risk' customers (GBP 1.4M past revenue) went quiet", "Run a win-back campaign"),
    ("Only ~20% of new customers return in month 1; Sep-Nov new customers -36% (partly a data-start effect)",
     "Add a second-purchase incentive; track acquisition over a longer history"),
    ("Ireland earns GBP 623K from only 3 customers", "Reduce concentration; grow Germany and France"),
    ("Party items are bought together: paper cups + plates (lift 27x), Red Retrospot bowl + cup (16x), napkins + plates (11x)", "Bundle and cross-sell"),
]
table_page(c, 2, "", "", "", rows, [820, 520], ["Insight", "Recommendation"], 46, H - 140)
c.showPage()

# 3..) chart pages
n = 3
for title, chap, img, tk in PAGES:
    chart_page(c, n, title, chap, img, tk); c.showPage(); n += 1

# basket + forecast
frame(c, "Market basket and forecast", "Chapter 7", n)
rules = pd.read_csv(OUT / "basket_rules.csv")
pairs = [(f"{r.item_a} + {r.item_b}", f"{r.lift:.0f}x") for r in rules[~rules.variant_pair].head(8).itertuples()]
para_block(c, ["Items bought together (top lift, colour/design variants of one product excluded)"], 46, H - 130, 800, h_style, bullet=False)
table_page(c, n, "", "", "", pairs, [790, 90], ["Pair", "Lift"], 46, H - 165)
para_block(c, ["Revenue forecast (GBP K)"], 990, H - 130, 400, h_style, bullet=False)
fc = [(r.month, round(r.forecast_gbp / 1000)) for r in pd.read_csv(OUT / "forecast.csv").itertuples()]
y = table_page(c, n, "", "", "", fc, [200, 150], ["Month", "Forecast"], 990, H - 165)
para_block(c, ["Seasonal model: same month last year x growth 1.025. Backtest on Jan-Nov 2011: 9.3% error for plain "
               "seasonal-naive (8.8% when scaled by the test period's own growth, which is optimistic) vs 28.1% for a "
               "3-month moving average, a weak baseline for seasonal data. With only two years of data this is a "
               "baseline, not a precise prediction."], 990, y - 20, 420, ParagraphStyle("f", parent=t_style, fontSize=15, leading=21), bullet=False)
c.showPage(); n += 1

# method notes
frame(c, "Method notes", "How the data was handled", n)
notes = [
    "<b>Cleaning:</b> 1,021,288 rows split into completed (1,003,214 real products) and cancelled lines (17,915). Gift vouchers and DCGS items removed.",
    "<b>Missing Customer ID:</b> 227,123 rows (13% of revenue) are used for sales analysis but excluded from RFM and cohorts.",
    "<b>Extreme orders:</b> 37 flagged lines. The two largest (GBP 168K and GBP 77K) were cancelled afterwards, so product rankings exclude them and RFM uses net value.",
    "<b>Incomplete month:</b> Dec 2011 ends on the 9th and is excluded from comparisons, cohorts and the forecast.",
    "<b>Dec 2009 cohort</b> includes customers active before the data starts, so it is excluded from retention averages. 2010 cohorts are affected to a smaller degree, so the 2010 vs 2011 drop in new customers is partly a data-start effect.",
    "<b>Retention curve:</b> averages the 11 cohorts Jan-Nov 2010 (all observed for 12 months). The month-12 bump is led by Sep-Nov cohorts; calling it an annual, seasonal repeat is an interpretation.",
    "<b>Market basket:</b> pairs that share two or more content words (colour, size, counts removed) are treated as variants of one product and excluded. This text rule is imperfect.",
    "<b>Customer type</b> (trade vs retail) is not in the data; statements about wholesale buyers are hypotheses.",
    "<b>Tools:</b> Python, pandas, matplotlib, reportlab. Dataset: Online Retail II (UCI).",
]
card(c, 36, 52, W - 72, 649)
para_block(c, notes, 70, 701 - 36, W - 140, n_style, bullet=False)
c.showPage()
c.save()
print("Saved", OUT / "Online_Retail_Dashboard.pdf")
