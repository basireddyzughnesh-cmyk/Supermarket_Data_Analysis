"""
Supermarket Sales Analysis — PDF Report Generator
Run: python generate_report_pdf.py
Output: Supermarket_Sales_Report.pdf
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.textlabels import Label
from reportlab.platypus.flowables import Flowable

# ─── Colours ──────────────────────────────────────────────────────────────────
BLUE        = colors.HexColor("#3b82d4")
PURPLE      = colors.HexColor("#7c5cd8")
GREEN       = colors.HexColor("#10b981")
AMBER       = colors.HexColor("#f59e0b")
RED         = colors.HexColor("#ef4444")
CYAN        = colors.HexColor("#06b6d4")
LIME        = colors.HexColor("#84cc16")
ORANGE      = colors.HexColor("#f97316")
BG_LIGHT    = colors.HexColor("#f7f8fa")
BORDER      = colors.HexColor("#e5e7eb")
MUTED       = colors.HexColor("#57606a")
TEXT        = colors.HexColor("#1f2328")
WHITE       = colors.white
ACCENT_DARK = colors.HexColor("#1e3a5f")

PALETTE = [BLUE, PURPLE, GREEN, AMBER, RED, CYAN, LIME, ORANGE]

W, H = A4  # 595.27 x 841.89 pt

# ─── Styles ───────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, **kw):
    s = ParagraphStyle(name, **kw)
    return s

COVER_TITLE = style("CoverTitle", fontSize=28, fontName="Helvetica-Bold",
                    textColor=TEXT, alignment=TA_CENTER, spaceAfter=6)
COVER_SUB   = style("CoverSub",   fontSize=13, fontName="Helvetica",
                    textColor=MUTED, alignment=TA_CENTER, spaceAfter=4)
COVER_META  = style("CoverMeta",  fontSize=10, fontName="Helvetica",
                    textColor=MUTED, alignment=TA_CENTER, spaceAfter=3)

H1 = style("H1", fontSize=15, fontName="Helvetica-Bold", textColor=TEXT,
           spaceBefore=18, spaceAfter=8, borderPadding=(0,0,0,8),
           leftIndent=0)
H2 = style("H2", fontSize=12, fontName="Helvetica-Bold", textColor=TEXT,
           spaceBefore=12, spaceAfter=6)
BODY = style("Body", fontSize=10, fontName="Helvetica", textColor=TEXT,
             leading=16, spaceAfter=6, alignment=TA_JUSTIFY)
BODY_SMALL = style("BodySmall", fontSize=9, fontName="Helvetica",
                   textColor=MUTED, leading=14, spaceAfter=4)
CODE_STYLE = style("Code", fontSize=9, fontName="Courier",
                   textColor=ACCENT_DARK, backColor=colors.HexColor("#f0f6ff"),
                   borderPadding=4, spaceAfter=6)
FOOTER_S   = style("Footer", fontSize=8, fontName="Helvetica",
                   textColor=MUTED, alignment=TA_CENTER)
INSIGHT_S  = style("Insight", fontSize=9.5, fontName="Helvetica",
                   textColor=ACCENT_DARK, leading=15, spaceAfter=4,
                   leftIndent=8, rightIndent=8)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def h1(text):
    """Section heading with left colour bar drawn via a custom flowable."""
    return SectionHeading(text)

def p(text):
    return Paragraph(text, BODY)

def sp(h=6):
    return Spacer(1, h)

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6, spaceBefore=6)

def insight_box(text, bg="#f0f6ff", border="#bfdbfe", fg="#1e3a5f"):
    style_i = style(f"IB{hash(text)}", fontSize=9.5, fontName="Helvetica",
                    textColor=colors.HexColor(fg), leading=15,
                    spaceAfter=6, backColor=colors.HexColor(bg),
                    borderColor=colors.HexColor(border),
                    borderWidth=1, borderPadding=8, borderRadius=4)
    return Paragraph(text, style_i)

def code(text):
    return Paragraph(f"<font name='Courier'>{text}</font>", CODE_STYLE)

def table_style_base():
    return [
        ("BACKGROUND",  (0,0), (-1,0), BG_LIGHT),
        ("TEXTCOLOR",   (0,0), (-1,0), MUTED),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,0), 8),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",    (0,1), (-1,-1), 9),
        ("TEXTCOLOR",   (0,1), (-1,-1), TEXT),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, colors.HexColor("#fafbfc")]),
        ("GRID",        (0,0), (-1,-1), 0.4, BORDER),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING",(0,0), (-1,-1), 7),
        ("LINEBELOW",   (0,0), (-1,0), 1.2, BLUE),
    ]

class SectionHeading(Flowable):
    def __init__(self, text, section_num=""):
        super().__init__()
        self.text = text
        self.section_num = section_num
        self.width = W - 4*cm
        self.height = 26

    def draw(self):
        c = self.canv
        # Blue left bar
        c.setFillColor(BLUE)
        c.rect(0, 4, 3, 18, fill=1, stroke=0)
        # Text
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(10, 6, self.text)

class KPIRow(Flowable):
    """Row of KPI cards drawn as rectangles."""
    def __init__(self, items, width=None):
        super().__init__()
        self.items = items
        self.width = width or (W - 4*cm)
        self.height = 58

    def draw(self):
        c = self.canv
        n = len(self.items)
        card_w = (self.width - (n-1)*8) / n
        for i, (label, value, sub) in enumerate(self.items):
            x = i * (card_w + 8)
            # Card background
            c.setFillColor(BG_LIGHT)
            c.setStrokeColor(BORDER)
            c.roundRect(x, 0, card_w, self.height, 4, fill=1, stroke=1)
            # Label
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(MUTED)
            c.drawCentredString(x + card_w/2, 43, label.upper())
            # Value
            c.setFont("Helvetica-Bold", 15)
            c.setFillColor(TEXT)
            c.drawCentredString(x + card_w/2, 26, value)
            # Sub
            c.setFont("Helvetica", 7.5)
            c.setFillColor(BLUE)
            c.drawCentredString(x + card_w/2, 10, sub)

class HBarChart(Flowable):
    """Simple horizontal bar chart drawn natively."""
    def __init__(self, data, width=None, bar_height=14, gap=6, color_list=None):
        super().__init__()
        self.data = data          # list of (label, value, value_str)
        self.width = width or (W - 4*cm)
        self.bar_height = bar_height
        self.gap = gap
        self.colors = color_list or PALETTE
        n = len(data)
        self.height = n * (bar_height + gap) + gap

    def draw(self):
        c = self.canv
        max_val = max(v for _, v, _ in self.data) or 1
        label_w = 110
        val_w   = 80
        track_w = self.width - label_w - val_w - 12
        n = len(self.data)
        for i, (label, value, val_str) in enumerate(self.data):
            y = (n - 1 - i) * (self.bar_height + self.gap) + self.gap
            fill_w = (value / max_val) * track_w
            col = self.colors[i % len(self.colors)]
            # Track background
            c.setFillColor(colors.HexColor("#f0f0f0"))
            c.roundRect(label_w + 6, y, track_w, self.bar_height, 2, fill=1, stroke=0)
            # Fill bar
            c.setFillColor(col)
            if fill_w > 0:
                c.roundRect(label_w + 6, y, fill_w, self.bar_height, 2, fill=1, stroke=0)
            # Label
            c.setFont("Helvetica", 8)
            c.setFillColor(MUTED)
            c.drawRightString(label_w, y + self.bar_height/2 - 3, label)
            # Value text
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(TEXT)
            c.drawString(label_w + track_w + 14, y + self.bar_height/2 - 3, val_str)

class MiniPie(Flowable):
    """A simple pie chart drawn natively."""
    def __init__(self, slices, size=120):
        super().__init__()
        self.slices = slices   # list of (label, pct, color_hex)
        self.size = size
        self.width = size + 130
        self.height = size

    def draw(self):
        import math
        c = self.canv
        cx, cy = self.size/2, self.size/2
        r = self.size/2 - 6
        total = sum(p for _, p, _ in self.slices)
        angle = 90.0  # start at top
        for label, pct, col_hex in self.slices:
            sweep = 360 * pct / total
            c.setFillColor(colors.HexColor(col_hex))
            c.setStrokeColor(WHITE)
            c.setLineWidth(1)
            c.wedge(cx-r, cy-r, cx+r, cy+r, angle, sweep, fill=1, stroke=1)
            angle += sweep
        # Legend
        lx = self.size + 10
        ly = self.size - 12
        for label, pct, col_hex in self.slices:
            c.setFillColor(colors.HexColor(col_hex))
            c.roundRect(lx, ly, 9, 9, 2, fill=1, stroke=0)
            c.setFillColor(TEXT)
            c.setFont("Helvetica", 8)
            c.drawString(lx + 13, ly + 1, f"{label}  {pct:.1f}%")
            ly -= 16

# ─── Page template (header / footer) ─────────────────────────────────────────

def on_page(canvas, doc):
    canvas.saveState()
    # Top rule
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(1.5)
    canvas.line(2*cm, H - 1.5*cm, W - 2*cm, H - 1.5*cm)
    # Header text
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(BLUE)
    canvas.drawString(2*cm, H - 1.2*cm, "Supermarket Sales Analysis")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(W - 2*cm, H - 1.2*cm, "Data Analytics Project Report — 2026")
    # Footer rule
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.4*cm, W - 2*cm, 1.4*cm)
    # Footer text
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(W/2, 0.9*cm, f"Page {doc.page}  |  Made with IBM Bob")
    canvas.restoreState()

def on_first_page(canvas, doc):
    canvas.saveState()
    # Footer only on cover
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.line(2*cm, 1.4*cm, W - 2*cm, 1.4*cm)
    canvas.drawCentredString(W/2, 0.9*cm, "Made with IBM Bob  |  Supermarket Sales Analysis Report")
    canvas.restoreState()

# ─── Build content ────────────────────────────────────────────────────────────

def build_report(output_path=None):
    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent.parent
            / "reports"
            / "Supermarket_Sales_Report.pdf"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2*cm,
        title="Supermarket Sales Analysis Report",
        author="Data Analytics Project",
        subject="EDA and Business Intelligence Report",
    )

    story = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("🛒", style("Emoji", fontSize=42, alignment=TA_CENTER, spaceAfter=10)))
    story.append(Paragraph("Supermarket Sales Analysis", COVER_TITLE))
    story.append(Paragraph("Exploratory Data Analysis &amp; Business Intelligence Report", COVER_SUB))
    story.append(Spacer(1, 0.6*cm))

    meta_data = [
        ["Dataset", "supermarket_sales_500_rows.csv.xlsx", "Format", "Excel Open XML (.xlsx)"],
        ["Records", "497 transactions", "Period", "January 2026 – July 2026"],
        ["Cities", "Mumbai · Delhi · Bengaluru · Jaipur", "Branches", "A · B · C · D"],
        ["Tools", "Python · pandas · Streamlit · Plotly", "Report", "Data Analytics Project"],
    ]
    t = Table(meta_data, colWidths=[3*cm, 6.5*cm, 3*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTNAME",  (1,0), (1,-1), "Helvetica"),
        ("FONTNAME",  (3,0), (3,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), MUTED),
        ("TEXTCOLOR", (2,0), (2,-1), MUTED),
        ("TEXTCOLOR", (1,0), (1,-1), TEXT),
        ("TEXTCOLOR", (3,0), (3,-1), TEXT),
        ("BACKGROUND",(0,0), (-1,-1), BG_LIGHT),
        ("BOX",       (0,0), (-1,-1), 0.5, BORDER),
        ("INNERGRID", (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",(0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0), (-1,-1), 7),
    ]))
    story.append(t)

    story.append(Spacer(1, 1.2*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    story.append(Spacer(1, 0.4*cm))

    # Table of Contents
    story.append(Paragraph("<b>Table of Contents</b>", style("TOCHead", fontSize=11,
                            fontName="Helvetica-Bold", textColor=TEXT, spaceAfter=8)))
    toc_items = [
        ("1", "Project Overview"),
        ("2", "Dataset Description"),
        ("3", "Data Quality & Preprocessing"),
        ("4", "Key Performance Metrics"),
        ("5", "Sales by Category"),
        ("6", "Sales by City & Branch"),
        ("7", "Customer Segmentation"),
        ("8", "Payment Method Analysis"),
        ("9", "Monthly Sales Trend"),
        ("10", "Streamlit Dashboard"),
        ("11", "Business Recommendations"),
        ("12", "Conclusion"),
    ]
    toc_rows = [[f"{n}.", title, ""] for n, title in toc_items]
    toc_table = Table(toc_rows, colWidths=[0.8*cm, 10*cm, 3*cm])
    toc_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 9.5),
        ("TEXTCOLOR", (0,0), (0,-1), BLUE),
        ("TEXTCOLOR", (1,0), (1,-1), TEXT),
        ("TOPPADDING",(0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LINEBELOW", (0,-1), (-1,-1), 0.3, BORDER),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # ── 1. PROJECT OVERVIEW ─────────────────────────────────────────────────
    story.append(SectionHeading("1.  Project Overview"))
    story.append(sp(6))
    story.append(p(
        "This project performs a full end-to-end analysis of a supermarket chain operating "
        "across four major Indian cities. The goal is to transform raw transactional data into "
        "actionable business intelligence by following a structured pipeline: data loading → "
        "quality checks → feature engineering → aggregation → visualisation → strategic "
        "recommendations. The deliverables include a fully interactive <b>Streamlit dashboard</b> "
        "(<i>analysis.py</i>) with nine tabs, and this formal PDF report."
    ))

    obj_data = [
        ["#", "Objective", "Status"],
        ["1", "Load & identify the dataset's actual file format", "✅ Complete"],
        ["2", "Check for missing or incorrect values", "✅ Complete"],
        ["3", "Calculate Sales = Quantity × Unit Price", "✅ Complete"],
        ["4", "Group & summarise with totals, counts, averages", "✅ Complete"],
        ["5", "Create comparative charts", "✅ Complete"],
        ["6", "Derive business decisions; build Streamlit frontend", "✅ Complete"],
    ]
    t = Table(obj_data, colWidths=[0.8*cm, 11*cm, 3*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("TEXTCOLOR", (2,1), (2,-1), GREEN),
        ("FONTNAME",  (2,1), (2,-1), "Helvetica-Bold"),
        ("ALIGN",     (2,0), (2,-1), "CENTER"),
    ]))
    story.append(t)
    story.append(hr())

    # ── 2. DATASET DESCRIPTION ──────────────────────────────────────────────
    story.append(SectionHeading("2.  Dataset Description"))
    story.append(sp(6))
    story.append(p(
        "The dataset is stored in <b>supermarket_sales_500_rows.csv.xlsx</b>. "
        "Despite the <i>.csv</i> in the filename, the file is a binary <b>Excel Open XML (.xlsx)</b> "
        "package and must be loaded with <font name='Courier' color='#1e3a5f'>pandas.read_excel()</font>, "
        "not <font name='Courier' color='#dc2626'>read_csv()</font>."
    ))
    story.append(insight_box(
        "⚠️  File Format Note: Attempting pd.read_csv() on this file raises a UnicodeDecodeError "
        "because pandas tries to decode the raw ZIP-compressed XML bytes as plain text. "
        "Correct loader: pd.read_excel('...xlsx', sheet_name='Table 1')",
        bg="#fff8f0", border="#fcd9a8", fg="#7c3d12"
    ))
    story.append(sp(6))

    schema_data = [
        ["Column", "Type", "Description", "Sample Values"],
        ["Invoice ID", "Text", "Unique transaction identifier", "INV0001, INV0002…"],
        ["Date", "Date", "Transaction date (yyyy-mm-dd)", "2026-01-01 – 2026-07-01"],
        ["Branch", "Category", "Branch code (A–D)", "A, B, C, D"],
        ["City", "Category", "City of the branch", "Mumbai, Delhi, Bengaluru, Jaipur"],
        ["Customer Type", "Category", "Loyalty membership status", "Member, Normal"],
        ["Gender", "Category", "Customer gender", "Male, Female"],
        ["Product", "Text", "Product name", "Shampoo, Milk, Cheese…"],
        ["Category", "Category", "Product category", "Beverages, Dairy, Grocery…"],
        ["Quantity", "Integer", "Units purchased per transaction", "1 – 10"],
        ["Unit Price", "Float (₹)", "Price per unit", "₹27.67 – ₹236.71"],
        ["Payment", "Category", "Payment method used", "UPI, Card, Cash, Net Banking"],
        ["Rating", "Float", "Customer satisfaction (out of 5)", "3.0 – 5.0"],
        ["Sales", "Float (₹)", "Total transaction value", "₹42.14 – ₹2,114.82"],
    ]
    t = Table(schema_data, colWidths=[2.8*cm, 2.2*cm, 5.2*cm, 5.4*cm])
    t.setStyle(TableStyle(table_style_base()))
    story.append(t)
    story.append(hr())

    # ── 3. DATA QUALITY ──────────────────────────────────────────────────────
    story.append(SectionHeading("3.  Data Quality & Preprocessing"))
    story.append(sp(6))

    dq_data = [
        ["Check", "Result", "Action Taken"],
        ["Missing values", "0 missing across all columns", "None required"],
        ["Duplicate Invoice IDs", "None detected", "None required"],
        ["Negative Quantity values", "0 records", "None required"],
        ["Negative Unit Price", "0 records", "None required"],
        ["Rich-text column headers", "Detected (newlines in cells)", "Stripped to first line via .split('\\n')[0]"],
        ["Sales recalculation", "Recalculated from scratch", "Sales = Quantity × Unit Price applied"],
        ["Date parsing", "All 497 dates parsed successfully", "pd.to_datetime() with errors='coerce'"],
    ]
    t = Table(dq_data, colWidths=[4*cm, 5*cm, 6.6*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("TEXTCOLOR", (1,1), (1,3), GREEN),
        ("FONTNAME",  (1,1), (1,3), "Helvetica-Bold"),
    ]))
    story.append(t)
    story.append(sp(8))

    story.append(Paragraph("<b>Preprocessing Pipeline</b>", H2))
    prep_data = [
        ["Step", "Code / Method"],
        ["1. Load file", "pd.read_excel('...xlsx', sheet_name='Table 1')"],
        ["2. Clean column names", "[str(c).split('\\n')[0].strip() for c in df.columns]"],
        ["3. Drop empty rows", "df.dropna(how='all', inplace=True)"],
        ["4. Recalculate Sales", "df['Sales'] = df['Quantity'] * df['Unit Price']"],
        ["5. Extract Month", "df['Month'] = df['Date'].dt.to_period('M')"],
        ["6. Extract Day-of-Week", "df['DayOfWeek'] = df['Date'].dt.day_name()"],
    ]
    t = Table(prep_data, colWidths=[4*cm, 11.6*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("FONTNAME", (1,1), (1,-1), "Courier"),
        ("FONTSIZE", (1,1), (1,-1), 8.5),
        ("TEXTCOLOR",(1,1), (1,-1), ACCENT_DARK),
    ]))
    story.append(t)
    story.append(insight_box(
        "✅  Data Quality Summary: The dataset is clean — no missing values, no duplicates, "
        "no erroneous records. The primary preprocessing action was recalculating Sales from "
        "first principles (Quantity × Unit Price) to ensure analytical consistency throughout.",
        bg="#f0fdf4", border="#bbf7d0", fg="#14532d"
    ))
    story.append(hr())

    # ── 4. KEY METRICS ───────────────────────────────────────────────────────
    story.append(SectionHeading("4.  Key Performance Metrics"))
    story.append(sp(8))
    story.append(KPIRow([
        ("Total Revenue",       "₹2,43,409", "497 transactions"),
        ("Avg Transaction",     "₹489.76",   "per invoice"),
        ("Total Units Sold",    "2,752",      "avg 5.5 units/txn"),
    ]))
    story.append(sp(10))
    story.append(KPIRow([
        ("Avg Customer Rating", "4.00 ⭐",    "out of 5.0"),
        ("Product Categories",  "8",          "Beverages → Bakery"),
        ("Analysis Period",     "6 months",   "Jan – Jul 2026"),
    ]))
    story.append(hr())

    # ── 5. CATEGORY ──────────────────────────────────────────────────────────
    story.append(SectionHeading("5.  Sales by Category"))
    story.append(sp(6))

    cat_data = [
        ["Category", "Total Sales", "% of Revenue", "Rank"],
        ["Beverages",      "₹56,108", "23.1%", "🥇 1st"],
        ["Personal Care",  "₹45,944", "18.9%", "🥈 2nd"],
        ["Dairy",          "₹43,592", "17.9%", "🥉 3rd"],
        ["Grocery",        "₹39,869", "16.4%", "4th"],
        ["Fruits",         "₹23,263",  "9.6%", "5th"],
        ["Snacks",         "₹16,993",  "7.0%", "6th"],
        ["Vegetables",     "₹11,124",  "4.6%", "7th"],
        ["Bakery",          "₹6,516",  "2.7%", "8th"],
    ]
    t = Table(cat_data, colWidths=[4*cm, 4*cm, 3.5*cm, 4*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("TEXTCOLOR", (0,1), (0,3), TEXT),
        ("FONTNAME",  (0,1), (0,3), "Helvetica-Bold"),
        ("BACKGROUND",(0,1), (-1,1), colors.HexColor("#eff6ff")),
        ("BACKGROUND",(0,2), (-1,2), colors.HexColor("#f5f3ff")),
        ("BACKGROUND",(0,3), (-1,3), colors.HexColor("#f0fdf4")),
    ]))
    story.append(t)
    story.append(sp(8))

    story.append(HBarChart([
        ("Beverages",     56108,  "₹56,108 (23.1%)"),
        ("Personal Care", 45944,  "₹45,944 (18.9%)"),
        ("Dairy",         43592,  "₹43,592 (17.9%)"),
        ("Grocery",       39869,  "₹39,869 (16.4%)"),
        ("Fruits",        23263,  "₹23,263  (9.6%)"),
        ("Snacks",        16993,  "₹16,993  (7.0%)"),
        ("Vegetables",    11124,  "₹11,124  (4.6%)"),
        ("Bakery",         6516,  "₹6,516   (2.7%)"),
    ]))
    story.append(sp(8))
    story.append(insight_box(
        "📊  Finding: Beverages dominate with 23.1% of total revenue (₹56,108), followed by "
        "Personal Care (18.9%) and Dairy (17.9%). The top 3 categories together account for "
        "59.9% of all revenue. Bakery and Vegetables are the smallest contributors and represent "
        "potential growth opportunities through bundling and promotions."
    ))
    story.append(hr())

    # ── 6. CITY & BRANCH ──────────────────────────────────────────────────────
    story.append(SectionHeading("6.  Sales by City & Branch"))
    story.append(sp(6))

    city_data = [
        ["City", "Branch", "Total Sales", "% of Revenue", "Avg Sale"],
        ["Mumbai",    "C", "₹72,298", "29.7%", "₹484.55"],
        ["Delhi",     "B", "₹64,116", "26.3%", "₹494.74"],
        ["Bengaluru", "D", "₹55,468", "22.8%", "₹484.81"],
        ["Jaipur",    "A", "₹51,527", "21.2%", "₹494.49"],
    ]
    t = Table(city_data, colWidths=[3.2*cm, 2*cm, 3.5*cm, 3.5*cm, 3.4*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("BACKGROUND",(0,1),(-1,1), colors.HexColor("#eff6ff")),
        ("FONTNAME",  (0,1),(0,1), "Helvetica-Bold"),
    ]))
    story.append(t)
    story.append(sp(8))

    story.append(MiniPie([
        ("Mumbai",    29.7, "#3b82d4"),
        ("Delhi",     26.3, "#7c5cd8"),
        ("Bengaluru", 22.8, "#10b981"),
        ("Jaipur",    21.2, "#f59e0b"),
    ], size=140))
    story.append(sp(8))
    story.append(insight_box(
        "🏙️  Finding: Mumbai (Branch C) leads with ₹72,298 (29.7%). The revenue is remarkably "
        "balanced across all four cities — only an 8.5-point spread from top to bottom — suggesting "
        "a well-distributed network. Jaipur has the most headroom for growth initiatives."
    ))
    story.append(hr())

    # ── 7. CUSTOMER SEGMENTATION ──────────────────────────────────────────────
    story.append(SectionHeading("7.  Customer Segmentation"))
    story.append(sp(6))

    seg_data = [
        ["Segment", "Total Revenue", "Share", "Key Takeaway"],
        ["Member",  "₹1,42,781", "58.7%", "Higher avg spend; drives majority of revenue"],
        ["Normal",  "₹1,00,628", "41.3%", "Conversion target for loyalty programme"],
        ["Female",  "₹1,23,782", "50.9%", "Marginally higher revenue contributor"],
        ["Male",    "₹1,19,627", "49.1%", "Near-equal split — broad appeal"],
    ]
    t = Table(seg_data, colWidths=[3*cm, 3.5*cm, 2.5*cm, 6.6*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("BACKGROUND",(0,1),(-1,1), colors.HexColor("#eff6ff")),
        ("BACKGROUND",(0,3),(-1,3), colors.HexColor("#eff6ff")),
        ("FONTNAME",  (1,1),(1,4), "Helvetica-Bold"),
    ]))
    story.append(t)
    story.append(sp(6))
    story.append(insight_box(
        "👥  Finding: Members generate 58.7% of revenue and on average spend ~₹287 more per "
        "transaction than Normal customers. The gender split is nearly 50/50, confirming the "
        "supermarket has broad demographic appeal. The highest-ROI strategy is converting Normal "
        "customers into Members via a sign-up incentive."
    ))
    story.append(hr())

    # ── 8. PAYMENT ANALYSIS ───────────────────────────────────────────────────
    story.append(SectionHeading("8.  Payment Method Analysis"))
    story.append(sp(6))

    pay_data = [
        ["Payment Method", "Transactions", "Total Revenue", "% of Revenue", "Avg Sale"],
        ["UPI",          "126", "₹67,682", "27.8%", "₹537.16"],
        ["Net Banking",  "125", "₹64,593", "26.5%", "₹516.75"],
        ["Card",         "124", "₹57,094", "23.5%", "₹460.44"],
        ["Cash",         "122", "₹54,040", "22.2%", "₹442.95"],
    ]
    t = Table(pay_data, colWidths=[3.2*cm, 2.8*cm, 3.2*cm, 3.2*cm, 3.2*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("BACKGROUND",(0,1),(-1,1), colors.HexColor("#eff6ff")),
        ("FONTNAME",  (4,1),(4,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (4,1),(4,1),  BLUE),
    ]))
    story.append(t)
    story.append(sp(8))
    story.append(HBarChart([
        ("UPI",         67682, "₹67,682 (27.8%)"),
        ("Net Banking", 64593, "₹64,593 (26.5%)"),
        ("Card",        57094, "₹57,094 (23.5%)"),
        ("Cash",        54040, "₹54,040 (22.2%)"),
    ]))
    story.append(sp(6))
    story.append(insight_box(
        "💳  Finding: All four payment methods are almost perfectly balanced in transaction count "
        "(122–126 each), but UPI yields the highest average sale (₹537 vs ₹443 for Cash). "
        "This suggests UPI users are higher-value buyers. A UPI cashback reward or loyalty point "
        "incentive could further increase basket sizes and shift remaining cash transactions digital."
    ))
    story.append(hr())

    # ── 9. MONTHLY TREND ──────────────────────────────────────────────────────
    story.append(SectionHeading("9.  Monthly Sales Trend"))
    story.append(sp(6))

    monthly_data = [
        ["Month", "Total Sales", "% of Total", "Trend Note"],
        ["January 2026",   "₹43,416", "17.8%", "Strong start to the year"],
        ["February 2026",  "₹29,295", "12.0%", "Lowest full month — seasonal dip"],
        ["March 2026",     "₹37,306", "15.3%", "Recovery — approaching summer"],
        ["April 2026",     "₹52,570", "21.6%", "🏆 Peak month — highest revenue"],
        ["May 2026",       "₹42,542", "17.5%", "Post-peak moderate decline"],
        ["June 2026",      "₹34,813", "14.3%", "Continued seasonal decline"],
        ["July 2026",       "₹3,467",  "1.4%", "⚠️ Partial month (1 day of data)"],
    ]
    t = Table(monthly_data, colWidths=[3.5*cm, 3.2*cm, 2.5*cm, 6.4*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("BACKGROUND",(0,4),(-1,4), colors.HexColor("#fff1f2")),
        ("FONTNAME",  (1,4),(1,4), "Helvetica-Bold"),
        ("TEXTCOLOR", (1,4),(1,4), RED),
    ]))
    story.append(t)
    story.append(sp(8))
    story.append(HBarChart([
        ("Jan 2026", 43416, "₹43,416 (17.8%)"),
        ("Feb 2026", 29295, "₹29,295 (12.0%)"),
        ("Mar 2026", 37306, "₹37,306 (15.3%)"),
        ("Apr 2026", 52570, "₹52,570 (21.6%) 🏆"),
        ("May 2026", 42542, "₹42,542 (17.5%)"),
        ("Jun 2026", 34813, "₹34,813 (14.3%)"),
    ], color_list=[BLUE, PURPLE, GREEN, RED, AMBER, CYAN]))
    story.append(sp(6))
    story.append(insight_box(
        "📅  Finding: April 2026 is the peak month with ₹52,570 (21.6% of all revenue). "
        "February is the weakest full month (₹29,295). The Jan→Feb dip and subsequent April "
        "recovery likely reflects seasonal purchasing patterns. Inventory, staffing, and "
        "promotional budgets should be scaled up 2–3 weeks before April each year."
    ))
    story.append(hr())

    # ── 10. STREAMLIT DASHBOARD ───────────────────────────────────────────────
    story.append(SectionHeading("10.  Streamlit Dashboard"))
    story.append(sp(6))
    story.append(p(
        "An interactive 9-tab dashboard was built using <b>Streamlit 1.63</b> and "
        "<b>Plotly 7.0</b>. All charts respond to sidebar filters (City, Category, Gender, "
        "Customer Type, Payment, Date Range) in real time."
    ))

    dash_data = [
        ["Tab", "Content"],
        ["📊 Overview",           "6 KPI metric cards; Category bar chart; City pie chart"],
        ["🔍 Data Quality",       "Missing value check, duplicate detection, recalculation progress bar, dtype table"],
        ["📦 Category & Product", "Category summary table; top-15 products bar chart; avg rating by category"],
        ["🏙️ City & Branch",      "City & branch performance tables; grouped category-city bar chart"],
        ["👥 Customer Insights",  "Customer type × gender revenue; avg spend; rating histogram; segment table"],
        ["💳 Payment Analysis",   "Transaction count pie; revenue bar; stacked city × payment chart"],
        ["📈 Trends",             "Dual-axis monthly trend; day-of-week bar; category-over-time line chart"],
        ["💡 Business Decisions", "10 auto-computed insights; Priority Action Matrix with timeframes"],
        ["📋 Raw Data",           "Full searchable filtered table with CSV download button"],
    ]
    t = Table(dash_data, colWidths=[3.8*cm, 11.8*cm])
    t.setStyle(TableStyle(table_style_base()))
    story.append(t)
    story.append(sp(8))

    story.append(Paragraph("<b>Run Instructions</b>", H2))
    run_data = [
        ["Step", "Command"],
        ["Install dependencies", "python -m pip install streamlit plotly openpyxl pandas"],
        ["Launch dashboard",     "python -m streamlit run analysis.py"],
        ["Open in browser",      "http://localhost:8501"],
    ]
    t = Table(run_data, colWidths=[4*cm, 11.6*cm])
    t.setStyle(TableStyle(table_style_base() + [
        ("FONTNAME", (1,1), (1,-1), "Courier"),
        ("FONTSIZE", (1,1), (1,-1), 8.5),
        ("TEXTCOLOR",(1,1), (1,-1), ACCENT_DARK),
        ("BACKGROUND",(1,1),(1,-1), colors.HexColor("#f0f6ff")),
    ]))
    story.append(t)
    story.append(hr())

    # ── 11. RECOMMENDATIONS ───────────────────────────────────────────────────
    story.append(SectionHeading("11.  Business Recommendations"))
    story.append(sp(6))

    rec_data = [
        ["Priority", "Action", "Rationale", "Expected Impact", "Timeline"],
        ["🔴 High",    "Expand Beverages product line",       "23.1% revenue share — clear leader",               "+10–15% revenue",        "Q3 2026"],
        ["🔴 High",    "Invest in Mumbai Branch C",           "Top city at 29.7%; expansion potential",           "New market share",       "Q4 2026"],
        ["🔴 High",    "Pre-season April planning",           "21.6% of annual revenue in one month",             "+8% April sales",        "Mar 2026"],
        ["🟠 Medium",  "Member conversion programme",         "Members spend 42% more than Normal",               "+₹10K/branch/year",      "Q2 2026"],
        ["🟠 Medium",  "UPI cashback incentive",              "UPI avg sale (₹537) > Cash (₹443)",                "Shift 20% Cash→UPI",     "Q3 2026"],
        ["🟠 Medium",  "February promotional campaign",       "Lowest full month (₹29,295)",                      "Fill Feb gap by 15%",    "Jan 2026"],
        ["🟡 Low",     "Bundle Bakery & Vegetables",          "Only 7.3% combined revenue share",                 "+5% volume",             "Q3 2026"],
        ["🟡 Low",     "Personal Care quality maintenance",   "2nd highest revenue — protect ratings",            "Protect repeat buys",    "Ongoing"],
    ]
    t = Table(rec_data, colWidths=[1.8*cm, 3.8*cm, 4*cm, 2.8*cm, 1.8*cm],
              repeatRows=1)
    t.setStyle(TableStyle(table_style_base() + [
        ("FONTSIZE",  (0,0), (-1,0), 7.5),
        ("FONTSIZE",  (0,1), (-1,-1), 8.5),
        ("BACKGROUND",(0,1), (-1,3), colors.HexColor("#fff1f2")),
        ("BACKGROUND",(0,4), (-1,6), colors.HexColor("#fffbeb")),
        ("BACKGROUND",(0,7), (-1,-1), colors.HexColor("#f0fdf4")),
        ("TEXTCOLOR", (0,1), (0,3), RED),
        ("TEXTCOLOR", (0,4), (0,6), AMBER),
        ("TEXTCOLOR", (0,7), (0,-1), GREEN),
        ("FONTNAME",  (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,1), (0,-1), 9),
        ("WORDWRAP",  (0,0), (-1,-1), 1),
    ]))
    story.append(t)
    story.append(hr())

    # ── 12. CONCLUSION ────────────────────────────────────────────────────────
    story.append(SectionHeading("12.  Conclusion"))
    story.append(sp(6))
    story.append(p(
        "This project successfully demonstrates a complete data analytics pipeline applied to "
        "supermarket transactional data. The analysis covered 497 transactions across 4 cities, "
        "8 product categories, and 6 months, yielding ₹2,43,409 in total revenue at an average "
        "transaction value of ₹489.76 and a customer satisfaction rating of 4.0 / 5.0."
    ))

    conclusions = [
        ("✅ Clean Data",         "No missing values, no duplicates, no erroneous records. "
                                  "Sales were independently verified via Quantity × Unit Price."),
        ("📊 Revenue Pillars",    "Beverages + Personal Care + Dairy contribute ~60% of revenue. "
                                  "These categories deserve priority in inventory and supplier strategy."),
        ("🏆 Top City",           "Mumbai leads at 29.7% but the 4-city network is well-balanced, "
                                  "suggesting all branches are viable."),
        ("👤 Loyalty Works",      "Members generate 58.7% of revenue and spend ~42% more per visit. "
                                  "Accelerating membership acquisition is the single highest-ROI action."),
        ("📅 Seasonality Clear",  "April is the peak month (21.6%). Pre-season planning each March "
                                  "should be a standing operational practice."),
        ("💳 Go Digital",         "UPI delivers the highest average sale (₹537). Incentivising digital "
                                  "payments reduces cash handling costs and increases basket sizes."),
    ]
    for icon_title, body in conclusions:
        story.append(insight_box(f"<b>{icon_title}:</b>  {body}"))

    story.append(sp(12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(sp(6))
    tech_data = [
        ["Python 3.14", "pandas 3.0.3", "Streamlit 1.63.0", "Plotly 7.0.0", "ReportLab 5.0.1"],
    ]
    t = Table(tech_data, colWidths=[3.2*cm]*5)
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 8.5),
        ("TEXTCOLOR", (0,0), (-1,-1), MUTED),
        ("ALIGN",     (0,0), (-1,-1), "CENTER"),
        ("BACKGROUND",(0,0), (-1,-1), BG_LIGHT),
        ("BOX",       (0,0), (-1,-1), 0.4, BORDER),
        ("INNERGRID", (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",(0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    story.append(t)

    # Build PDF
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
    print(f"PDF saved: {output_path}")

if __name__ == "__main__":
    build_report()
