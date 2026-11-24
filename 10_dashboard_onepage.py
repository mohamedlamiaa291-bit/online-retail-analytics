"""One-page dashboard (PDF) | needs the chart PNGs from scripts 02-06 and forecast.csv (all in output/)
Everything on a single page so charts can be compared at a glance. The multi-page report is 09_report_pdf.py."""
from pathlib import Path
import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
W, H = 2400, 1800
TEAL, BG, TX, MU, GR = HexColor("#0D9488"), HexColor("#F1F5F9"), HexColor("#0F172A"), HexColor("#64748B"), HexColor("#E2E8F0")
M = 36  # outer margin / gap

c = canvas.Canvas(str(OUT / "Online_Retail_Dashboard.pdf"), pagesize=(W, H))
c.setTitle("Online Retail Analytics - one-page dashboard")
c.setFillColor(BG); c.rect(0, 0, W, H, stroke=0, fill=1)

# ---- header with KPIs ----
HH = 150
c.setFillColor(TEAL); c.rect(0, H - HH, W, HH, stroke=0, fill=1)
c.setFillColor(white); c.setFont("Helvetica-Bold", 46); c.drawString(M + 10, H - 72, "Online Retail Analytics")
c.setFont("Helvetica", 24); c.drawString(M + 10, H - 112, "1M+ transactions  |  Dec 2009 - Dec 2011  |  Online Retail II")
kpis = [("\u00a319.6M", "completed revenue"), ("1.0M", "transactions"), ("5,832", "customers scored"),
        ("43", "countries"), ("77%", "revenue from top 20%")]
kx = 900
for v, l in kpis:
    c.setFont("Helvetica-Bold", 46); c.drawString(kx, H - 82, v)
    c.setFont("Helvetica", 19); c.drawString(kx, H - 116, l)
    kx += 290

# ---- chart grid: 3 columns x 3 rows ----
CHARTS = ["ch2_revenue_yoy.png", "ch2_orders_vs_aov.png", "ch5_segments.png", "ch5_concentration.png",
          "ch4_heatmap.png", "ch6_retention_curve.png", "ch6_new_customers.png", "ch3_top_products.png", "ch3_countries.png"]
BOTTOM = 330                                   # height reserved for the insights strip
top_y = H - HH - M
cell_w = (W - M * 4) / 3
cell_h = (top_y - BOTTOM - M * 3) / 3
for i, name in enumerate(CHARTS):
    col, row = i % 3, i // 3
    x = M + col * (cell_w + M); y = top_y - (row + 1) * cell_h - row * M
    c.setFillColor(white); c.setStrokeColor(GR); c.roundRect(x, y, cell_w, cell_h, 18, stroke=1, fill=1)
    ir = ImageReader(str(OUT / name)); iw, ih = ir.getSize()
    s = min((cell_w - 24) / iw, (cell_h - 24) / ih); dw, dh = iw * s, ih * s
    c.drawImage(ir, x + (cell_w - dw) / 2, y + (cell_h - dh) / 2, dw, dh, mask="auto")

# ---- bottom strip: insights + actions (left), forecast (right) ----
th = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=17, textColor=white, leading=21)
td = ParagraphStyle("td", fontName="Helvetica", fontSize=16, textColor=TX, leading=20)
rows = [
    ("Sep-Nov brings ~40% of Jan-Nov sales; November alone ~16%", "Prepare stock and campaigns from August"),
    ("2011 revenue +3% via larger baskets (+7%) while orders fell 3.7%", "Grow order count with re-engagement offers"),
    ("Top 20% of customers = 77% of revenue; top 1% = 31%", "Protect Champions with a loyalty programme"),
    ("826 'At Risk' customers (\u00a31.4M past revenue) went quiet", "Run a win-back campaign"),
    ("~20% of new customers return in month 1; Sep-Nov new customers -36% (partly a data-start effect)", "Second-purchase incentive; track acquisition over a longer history"),
    ("Ireland earns \u00a3623K from only 3 customers", "Reduce concentration; grow Germany and France"),
    ("Paper cups + plates bought together (lift 27x); also Retrospot bowl + cup (16x)", "Bundle and cross-sell"),
]
data = [[Paragraph("Insight", th), Paragraph("Recommendation", th)]] + [[Paragraph(a, td), Paragraph(b, td)] for a, b in rows]
tbl = Table(data, colWidths=[1050, 700])
tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, BG]),
                         ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                         ("LINEBELOW", (0, 0), (-1, -1), 0.4, GR)]))
_, h1 = tbl.wrap(1750, 1000); tbl.drawOn(c, M, M + BOTTOM - M - h1 + 18)

fc = pd.read_csv(OUT / "forecast.csv")
fdata = [[Paragraph("Month", th), Paragraph("Forecast (\u00a3K)", th)]] + \
        [[Paragraph(r.month, td), Paragraph(f"{round(r.forecast_gbp / 1000)}", td)] for r in fc.itertuples()]
ft = Table(fdata, colWidths=[160, 220])
ft.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, BG]),
                        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
fx = M * 2 + 1750
_, h2 = ft.wrap(380, 1000); ft.drawOn(c, fx, M + BOTTOM - M - h2 + 18)
note = Paragraph("Seasonal model (same month last year x 1.025). Backtest Jan-Nov 2011: 9.3% error "
                 "vs 28.1% for a 3-month moving average. A baseline, not a precise prediction.",
                 ParagraphStyle("n", fontName="Helvetica", fontSize=14, textColor=MU, leading=18))
_, hn = note.wrap(W - fx - M, 200); note.drawOn(c, fx, M + BOTTOM - M - h2 + 18 - hn - 10)

c.setFillColor(MU); c.setFont("Helvetica", 15)
c.drawString(M, 16, "Python, pandas, matplotlib. Dec 2011 excluded (incomplete month). Customer value is net of cancellations. Details: Online_Retail_Report.pdf")
c.showPage(); c.save()
print("Saved", OUT / "Online_Retail_Dashboard.pdf")
