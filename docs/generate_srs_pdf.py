import os
import sys
import pymupdf
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
    Preformatted,
)
from reportlab.pdfgen import canvas

# Palette constants
NAVY_DARK = colors.HexColor("#0F172A")    # Primary dark navy (headings, title)
NAVY_LIGHT = colors.HexColor("#1E293B")   # Slate 800 (subheadings, table header)
BLUE_ACCENT = colors.HexColor("#2563EB")  # Blue 600 (accents, links, highlights)
BLUE_LIGHT = colors.HexColor("#EFF6FF")   # Blue 50 (light callout background)
SLATE_BORDER = colors.HexColor("#CBD5E1") # Slate 300 (borders, dividers)
SLATE_BG = colors.HexColor("#F8FAFC")     # Slate 50 (table alternate rows)
SLATE_MUTED = colors.HexColor("#64748B")  # Slate 500 (captions, footer text)
TEXT_COLOR = colors.HexColor("#1E293B")   # Slate 800 (body copy)
WHITE = colors.HexColor("#FFFFFF")
GREEN_STATUS = colors.HexColor("#15803D") # Emerald 700
AMBER_STATUS = colors.HexColor("#B45309") # Amber 700

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 54  # 0.75 inch
PRINTABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN  # 504 pt


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count ('Page X of Y')
    and render professional running headers and footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Skip header and footer on cover page (Page 1)
        if self._pageNumber == 1:
            return

        self.saveState()

        # Running Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(NAVY_LIGHT)
        self.drawString(MARGIN, PAGE_HEIGHT - 38, "RestaurantOps AI")
        self.setFont("Helvetica", 8)
        self.setFillColor(SLATE_MUTED)
        self.drawString(MARGIN + 72, PAGE_HEIGHT - 38, "|   Software Requirements Specification (SRS) v1.0")

        self.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 38, "Project Specification")

        # Header rule
        self.setStrokeColor(SLATE_BORDER)
        self.setLineWidth(0.6)
        self.line(MARGIN, PAGE_HEIGHT - 44, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 44)

        # Footer rule
        self.line(MARGIN, 44, PAGE_WIDTH - MARGIN, 44)

        # Running Footer
        self.setFont("Helvetica", 8)
        self.setFillColor(SLATE_MUTED)
        self.drawString(MARGIN, 32, "Confidential  --  Prepared by Yohannes Zewde  |  Submitted for Review & Approval")

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(PAGE_WIDTH - MARGIN, 32, page_str)

        self.restoreState()


def get_styles():
    base = getSampleStyleSheet()
    return {
        "cover_badge": ParagraphStyle(
            "CoverBadge",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=BLUE_ACCENT,
            spaceAfter=12,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            textColor=NAVY_DARK,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName="Helvetica",
            fontSize=12.5,
            leading=17,
            textColor=SLATE_MUTED,
            spaceAfter=22,
        ),
        "h1": ParagraphStyle(
            "Heading1_Custom",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=NAVY_DARK,
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Heading2_Custom",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=NAVY_LIGHT,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3_Custom",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=13,
            textColor=BLUE_ACCENT,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body_Custom",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.5,
            textColor=TEXT_COLOR,
            spaceAfter=5,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold_Custom",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12.5,
            textColor=TEXT_COLOR,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "Bullet_Custom",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.5,
            textColor=TEXT_COLOR,
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=3,
        ),
        "callout": ParagraphStyle(
            "Callout_Custom",
            fontName="Helvetica",
            fontSize=8,
            leading=12,
            textColor=NAVY_DARK,
        ),
        "th": ParagraphStyle(
            "TableHead_Custom",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=WHITE,
        ),
        "td": ParagraphStyle(
            "TableBody_Custom",
            fontName="Helvetica",
            fontSize=7.8,
            leading=10.5,
            textColor=TEXT_COLOR,
        ),
        "td_bold": ParagraphStyle(
            "TableBodyBold_Custom",
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=10.5,
            textColor=TEXT_COLOR,
        ),
        "td_center": ParagraphStyle(
            "TableBodyCenter_Custom",
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=10.5,
            textColor=BLUE_ACCENT,
            alignment=1, # Center
        ),
        "code": ParagraphStyle(
            "CodeStyle",
            fontName="Courier",
            fontSize=7,
            leading=9.5,
            textColor=NAVY_DARK,
        ),
        "code_box": ParagraphStyle(
            "CodeBoxStyle",
            fontName="Courier",
            fontSize=6.8,
            leading=9,
            textColor=NAVY_DARK,
        ),
        "status_impl": ParagraphStyle(
            "StatusImplemented",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=GREEN_STATUS,
        ),
        "status_plan": ParagraphStyle(
            "StatusPlanned",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=AMBER_STATUS,
        ),
    }


def build_story(toc_page_map=None):
    styles = get_styles()
    story = []

    # ==========================================
    # COVER PAGE
    # ==========================================
    story.append(Spacer(1, 35))
    story.append(Paragraph("RESTAURANTOPS AI &bull; SOFTWARE ENGINEERING SPECIFICATION", styles["cover_badge"]))
    story.append(Paragraph("Software Requirements<br/>Specification (SRS)", styles["cover_title"]))
    story.append(Paragraph("AI-Powered Restaurant Inventory and Procurement Management System", styles["cover_subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE_ACCENT, spaceAfter=26))

    meta_data = [
        [Paragraph("Document Title", styles["td_bold"]), Paragraph("Software Requirements Specification (SRS)", styles["td"])],
        [Paragraph("Project Name", styles["td_bold"]), Paragraph("RestaurantOps AI", styles["td"])],
        [Paragraph("Document Version", styles["td_bold"]), Paragraph("1.0", styles["td"])],
        [Paragraph("Document Status", styles["td_bold"]), Paragraph("Reconstructed Project Specification &bull; Submitted for Review", styles["td"])],
        [Paragraph("Prepared By", styles["td_bold"]), Paragraph("Yohannes Zewde", styles["td"])],
        [Paragraph("Date of Preparation", styles["td_bold"]), Paragraph("November 2026", styles["td"])],
        [Paragraph("Target Industry", styles["td_bold"]), Paragraph("Restaurant, Culinary, and Hospitality", styles["td"])],
        [Paragraph("Functional Role", styles["td_bold"]), Paragraph("AI Inventory and Procurement Manager", styles["td"])],
        [Paragraph("Target Environment", styles["td_bold"]), Paragraph("Single-Restaurant MVP (Web SPA & REST API)", styles["td"])],
    ]
    meta_table = Table(meta_data, colWidths=[140, 364])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), SLATE_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 30))

    notice_content = [
        [Paragraph("<b>Specification Notice & Formal Scope:</b><br/>"
                   "This document provides the complete, reconstructed Software Requirements Specification (SRS) for "
                   "the RestaurantOps AI system, capturing all functional requirements (FR-01 to FR-08), architectural "
                   "layers, data flows, integration contracts, and operational criteria established during project initialization "
                   "and core backend development. It serves as the baseline for system verification and final approval.", styles["callout"])]
    ]
    notice_table = Table(notice_content, colWidths=[504])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BLUE_ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(notice_table)

    story.append(PageBreak())

    # ==========================================
    # TABLE OF CONTENTS
    # ==========================================
    story.append(Paragraph("Table of Contents", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=10))

    toc_defs = [
        (1, "Introduction", "System background, context, and operational domain"),
        (2, "Purpose", "Business intent, operational goals, and expected benefits"),
        (3, "Problem Statement", "Inventory challenges: stockouts, waste, manual auditing"),
        (4, "Proposed Solution", "Automated depletion, AI recommendations, alert triggers"),
        (5, "Project Objectives", "Measurable performance benchmarks and success targets"),
        (6, "Target Users and Stakeholders", "Operator personas, responsibilities, and system access"),
        (7, "Functional Requirements", "Detailed specifications for FR-01 through FR-08"),
        (8, "Non-Functional Requirements", "Performance, security, atomicity, data integrity"),
        (9, "System Architecture", "Layered architecture, service boundaries, data flows"),
        (10, "Third-Party API Integrations", "Google Gemini API, Telegram Bot API, Open-Meteo"),
        (11, "System Workflows", "10 end-to-end operational life cycles and processes"),
        (12, "API Specifications", "REST endpoint catalog (Implemented vs Planned)"),
        (13, "User Interface & Components", "Single Page Application views and navigation structure"),
        (14, "Technology Stack", "Comprehensive stack matrix and component assignments"),
        (15, "Minimum Viable Product Scope", "Core features in-scope versus explicit exclusions"),
        (16, "Future Enhancements", "Predictive ML, supplier EDI, multi-branch scaling"),
        (17, "Acceptance Criteria", "12 concrete verification criteria for MVP readiness"),
        (18, "Deployment & Resource Plans", "Local setup, environment variables, API quota limits"),
        (19, "Conclusion", "Executive summary and architectural synthesis"),
    ]

    toc_rows = [[
        Paragraph("<b>Sec</b>", styles["th"]),
        Paragraph("<b>Section Title</b>", styles["th"]),
        Paragraph("<b>Summary Description</b>", styles["th"]),
        Paragraph("<b>Page</b>", styles["th"])
    ]]

    for sec_num, sec_title, sec_desc in toc_defs:
        page_val = str(toc_page_map.get(sec_num, "-")) if toc_page_map else "-"
        toc_rows.append([
            Paragraph(f"<b>{sec_num}</b>", styles["td_bold"]),
            Paragraph(f"<b>{sec_title}</b>", styles["td_bold"]),
            Paragraph(sec_desc, styles["td"]),
            Paragraph(f"<b>{page_val}</b>", styles["td_center"]),
        ])

    toc_table = Table(toc_rows, colWidths=[32, 168, 256, 48])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
    ]))
    story.append(toc_table)

    story.append(PageBreak())

    # ==========================================
    # 1. INTRODUCTION
    # ==========================================
    story.append(Paragraph("1. Introduction", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "The restaurant and food service industry is characterized by razor-thin operating margins, extreme demand volatility, "
        "and heavy reliance on highly perishable ingredients. Managing kitchen inventory directly dictates profitability: stockouts "
        "lead to immediate lost revenue and frustrated diners, while over-purchasing results in food spoilage, tied-up working capital, "
        "and elevated Cost of Goods Sold (CoGS).",
        styles["body"]
    ))
    story.append(Paragraph(
        "Traditionally, culinary inventory control has depended on manual clipboard counts, physical checklists, and disconnected spreadsheets. "
        "These methods suffer from human calculation error, lack real-time visibility, and fail to anticipate impending shortages before dinner service. "
        "<b>RestaurantOps AI</b> is engineered as a modern, full-stack, AI-powered inventory and procurement management solution. "
        "By binding point-of-sale customer orders to granular ingredient consumption via recipes, the system delivers continuous stock visibility, "
        "proactive risk alerting, and conversational intelligence powered by Google's Gemini API.",
        styles["body"]
    ))

    # ==========================================
    # 2. PURPOSE
    # ==========================================
    story.append(Paragraph("2. Purpose", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "The primary purpose of RestaurantOps AI is to provide restaurant owners, executive chefs, and inventory managers with an intelligent, "
        "automated platform that eliminates operational guesswork and streamlines daily pantry operations.",
        styles["body"]
    ))
    story.append(Paragraph("&bull; <b>Automate ingredient depletion:</b> Automatically deduct precise ingredient portions upon every menu item sale through configured recipe bill-of-materials.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Eliminate ordering guesswork:</b> Generate deterministic reorder recommendations calculated from actual sales velocity and minimum stock thresholds.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Mitigate spoilage risk:</b> Continuously monitor ingredient shelf life and flag batches approaching expiration at least 48 to 72 hours in advance.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Provide AI-driven operational assistance:</b> Deliver natural language inventory insights and trend explanations through an integrated Gemini AI agent.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Enforce governance:</b> Maintain a strict 'Human-in-the-Loop' workflow requiring managerial review and explicit approval for all purchasing proposals.", styles["bullet"]))

    # ==========================================
    # 3. PROBLEM STATEMENT
    # ==========================================
    story.append(Paragraph("3. Problem Statement", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "Independent and commercial dining establishments grapple with systemic inefficiencies across pantry and supply chain workflows:",
        styles["body"]
    ))
    problem_items = [
        ("Manual & Error-Prone Tracking", "Pantry audits conducted late at night via paper logs suffer from arithmetic inaccuracies and inconsistent logging, obscuring actual stock positions."),
        ("Unexpected Mid-Service Stockouts", "Exhaustion of key ingredients during peak hours forces kitchens to '86' signature dishes, directly damaging revenue and guest loyalty."),
        ("Overstocking & Locked Capital", "Buffer purchasing driven by fear of stockouts ties up essential operating cash and creates physical overcrowding in cold and dry storage."),
        ("Perishable Waste & Spoilage", "Failure to track batch expiration dates leads to spoiled proteins, dairy, and produce, driving food waste expenses up to 4-10% of total food costs."),
        ("Fragmented Procurement", "Orders placed haphazardly across phone calls and vendor portals lack alignment with current stock levels or historical consumption."),
        ("Lack of Actionable Insights", "Managers lack synthesized visibility combining recent sales velocity, storage status, and ambient context into unified operational action plans.")
    ]
    for title, desc in problem_items:
        story.append(Paragraph(f"&bull; <b>{title}:</b> {desc}", styles["bullet"]))

    # ==========================================
    # 4. PROPOSED SOLUTION
    # ==========================================
    story.append(Paragraph("4. Proposed Solution", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "RestaurantOps AI resolves these challenges through a unified, service-oriented architecture combining automated inventory math with "
        "advanced AI reasoning:",
        styles["body"]
    ))
    story.append(Paragraph("&bull; <b>Recipe-Driven Depletion:</b> Every recorded sale initiates an atomic deduction across all associated ingredients, preserving an exact digital replica of kitchen stock.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Immutable Transaction Ledger:</b> All stock modifications (sales depletions, manual reconciliations, waste records, restocks) are recorded to an auditable transaction journal.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Deterministic Procurement Logic:</b> Reorder quantities are computed mathematically using strict threshold formulas: $Q = \\max((2 \\times \\text{min}) - \\text{current}, \\text{min})$.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>AI Contextual Analysis:</b> A Gemini-powered agent translates stock deficiencies into human-readable procurement recommendations with accurate cost estimates.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Human-in-the-Loop Governance:</b> The MVP requires explicit manager review and approval before purchase recommendations transition to actionable purchasing orders.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Automated Proactive Alerts:</b> Background APScheduler workers sweep stock levels periodically and transmit urgent low-stock and near-expiry alerts via Telegram.", styles["bullet"]))

    # ==========================================
    # 5. PROJECT OBJECTIVES
    # ==========================================
    story.append(Paragraph("5. Project Objectives", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))

    obj_data = [
        [Paragraph("<b>ID</b>", styles["th"]), Paragraph("<b>Strategic Objective</b>", styles["th"]), Paragraph("<b>Target Metric / Acceptance Threshold</b>", styles["th"])],
        [Paragraph("OBJ-01", styles["td_bold"]), Paragraph("Automated Recipe Consumption", styles["td"]), Paragraph("100% of recorded sales automatically deduct linked ingredients in an atomic database transaction.", styles["td"])],
        [Paragraph("OBJ-02", styles["td_bold"]), Paragraph("Real-Time Inventory Visibility", styles["td"]), Paragraph("Pantry balances update with < 200 ms latency; dashboard reflects actual database state immediately.", styles["td"])],
        [Paragraph("OBJ-03", styles["td_bold"]), Paragraph("Early Shortage Detection", styles["td"]), Paragraph("Zero untracked stockouts; 100% of items at or below minimum threshold flagged automatically.", styles["td"])],
        [Paragraph("OBJ-04", styles["td_bold"]), Paragraph("Perishable Waste Mitigation", styles["td"]), Paragraph("Identify 100% of ingredients expiring within 7 days, highlighting items with < 48 hours remaining.", styles["td"])],
        [Paragraph("OBJ-05", styles["td_bold"]), Paragraph("Procurement Efficiency", styles["td"]), Paragraph("Reduce time required for managers to draft daily vendor orders by at least 60%.", styles["td"])],
        [Paragraph("OBJ-06", styles["td_bold"]), Paragraph("Grounded AI Assistance", styles["td"]), Paragraph("Gemini agent answers user inquiries using validated backend tools with 0 direct SQL exposure.", styles["td"])],
        [Paragraph("OBJ-07", styles["td_bold"]), Paragraph("Complete Movement Auditability", styles["td"]), Paragraph("Maintain an immutable audit trail for 100% of stock additions, depletions, and reconciliations.", styles["td"])],
    ]
    obj_table = Table(obj_data, colWidths=[54, 180, 270])
    obj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(obj_table)

    # ==========================================
    # 6. TARGET USERS AND STAKEHOLDERS
    # ==========================================
    story.append(Paragraph("6. Target Users and Stakeholders", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "RestaurantOps AI supports five operational personas within the restaurant management hierarchy:",
        styles["body"]
    ))

    user_data = [
        [Paragraph("<b>Stakeholder Role</b>", styles["th"]), Paragraph("<b>Core Responsibilities</b>", styles["th"]), Paragraph("<b>Primary System Interactions</b>", styles["th"])],
        [Paragraph("Restaurant General Manager", styles["td_bold"]), Paragraph("Daily operations, P&L oversight, purchasing authorization, team management.", styles["td"]), Paragraph("Executive Dashboard, Procurement Approval/Rejection, Telegram Alerts, AI Assistant.", styles["td"])],
        [Paragraph("Kitchen / Inventory Manager", styles["td_bold"]), Paragraph("Pantry audits, physical stock receiving, recipe verification, culinary quality.", styles["td"]), Paragraph("Inventory Grid, Stock Adjustments, Expiry Tracker, Menu & Recipe Studio.", styles["td"])],
        [Paragraph("Procurement Personnel", styles["td_bold"]), Paragraph("Vendor communication, supplier pricing negotiations, purchase order dispatch.", styles["td"]), Paragraph("Approved Purchase Orders, Reorder Summary Reports, Vendor Spend Summaries.", styles["td"])],
        [Paragraph("Restaurant Owner / Executive", styles["td_bold"]), Paragraph("High-level profitability, food cost percentage (CoGS), multi-period margin analysis.", styles["td"]), Paragraph("Dashboard Analytics, Historical Consumption Reports, Waste Exposure Trends.", styles["td"])],
        [Paragraph("System Administrator", styles["td_bold"]), Paragraph("System configuration, security credentials, scheduled job monitoring, uptime.", styles["td"]), Paragraph("Health Check API, Automation Execution Logs, Database Migration Commands.", styles["td"])],
    ]
    user_table = Table(user_data, colWidths=[120, 180, 204])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(user_table)

    # ==========================================
    # 7. FUNCTIONAL REQUIREMENTS
    # ==========================================
    story.append(Paragraph("7. Functional Requirements", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "The functional scope of RestaurantOps AI is organized into eight formal requirement blocks (FR-01 to FR-08). "
        "Each requirement defines its operational capability, technical constraints, and verifiable acceptance conditions.",
        styles["body"]
    ))

    fr_specs = [
        ("FR-01: Inventory Management", [
            "<b>Description:</b> The system shall provide comprehensive CRUD capabilities for restaurant ingredients.",
            "<b>Attributes Tracked:</b> Ingredient name, unique SKU, culinary category (Proteins, Dairy, Produce, Dry Goods, Bakery, Beverages, Seasonings), measurement unit (kg, g, l, ml, piece), current stock balance, minimum threshold (`min_quantity`), cost per unit, and optional expiration date.",
            "<b>Business Rules:</b> Stock quantities must be non-negative (`current_quantity >= 0`). Deletion of ingredients referenced by active recipes or sales history is prohibited.",
            "<b>Acceptance Conditions:</b> Ingredient creation succeeds with valid data; duplicate SKUs return HTTP 400; category filtering and full-text name/SKU search function correctly."
        ]),
        ("FR-02: Sales and Ingredient Consumption Tracking", [
            "<b>Description:</b> The system shall record restaurant customer sales, associate menu items with recipes, and automatically deduct underlying ingredients.",
            "<b>Recipe Bill-of-Materials:</b> Menu items are linked to ingredients via `recipe_ingredients` specifying exact `quantity_required` per portion.",
            "<b>Depletion Process:</b> On sale recording, the backend retrieves all item recipes, aggregates total consumption, validates stock availability, and deducts quantities atomically.",
            "<b>Acceptance Conditions:</b> Selling 2 Chicken Burgers deducts 0.30 kg chicken, 2 buns, and 2 cheese slices in an atomic transaction; insufficient stock blocks the sale cleanly."
        ]),
        ("FR-03: AI-Powered Inventory Analysis", [
            "<b>Description:</b> The system shall analyze inventory levels, consumption velocity, and sales trends to identify anomalies and operational risks.",
            "<b>Analytical Capabilities:</b> Classify ingredients into `Critical`, `Low Stock`, and `Healthy`; calculate burn rates based on recent sales; generate natural language summaries.",
            "<b>Acceptance Conditions:</b> Low-stock ingredients are identified deterministically; Gemini generates clear, evidence-based commentary contextualizing stock variances."
        ]),
        ("FR-04: Procurement Planning", [
            "<b>Description:</b> The system shall generate deterministic procurement recommendations and manage their review and approval lifecycle.",
            "<b>Reorder Calculation:</b> Suggested replenishment quantity: $Q = \\max((2 \\times \\text{min\\_quantity}) - \\text{current\\_quantity}, \\text{min\\_quantity})$.",
            "<b>Order Lifecycle:</b> Order proposals transition from `draft` to `approved` or `rejected`. Total estimated purchase cost is computed using unit costs.",
            "<b>Acceptance Conditions:</b> Recommendations display itemized quantities and estimated totals; manager approval updates order status and timestamps; no automated supplier dispatch occurs in MVP."
        ]),
        ("FR-05: Expiration and Waste Monitoring", [
            "<b>Description:</b> The system shall monitor batch expiration dates to identify ingredients at risk of spoilage and calculate financial waste exposure.",
            "<b>Horizon Classification:</b> Flag items into `Expired`, `Urgent (< 48 hours)`, `Approaching (< 7 days)`, and `Safe`.",
            "<b>Acceptance Conditions:</b> The expiring items endpoint accurately filters ingredients within the requested lookahead window; at-risk dollar value is computed accurately."
        ]),
        ("FR-06: Notifications and Reporting", [
            "<b>Description:</b> The system shall transmit proactive operational alerts and daily summaries to restaurant managers via Telegram.",
            "<b>Notification Types:</b> Instant low-stock alerts, near-expiry batch warnings, and a consolidated morning daily operational report.",
            "<b>Acceptance Conditions:</b> Messages are dispatched asynchronously using `httpx`; failed network requests log warnings to `automation_logs` without failing core APIs."
        ]),
        ("FR-07: AI Assistant", [
            "<b>Description:</b> The system shall provide an interactive conversational AI interface powered by Google Gemini and the official `google-genai` SDK.",
            "<b>Tool-Calling Architecture:</b> Gemini interacts with the system exclusively through registered backend tool declarations mapped to service-layer methods.",
            "<b>Acceptance Conditions:</b> The AI retrieves real inventory data via service tools; direct raw SQL querying by the model is blocked; answers are strictly grounded in restaurant data."
        ]),
        ("FR-08: Scheduled Automation", [
            "<b>Description:</b> The system shall run background scheduled routines using APScheduler to execute routine checks and audit reporting.",
            "<b>Automated Tasks:</b> Periodic inventory health sweeps, automated low-stock detection, and scheduled morning report generation.",
            "<b>Acceptance Conditions:</b> Scheduled jobs run at configured cron intervals without user intervention; execution results, duration, and errors are written to `automation_logs`."
        ]),
    ]

    for title, points in fr_specs:
        story.append(Paragraph(title, styles["h2"]))
        for pt in points:
            story.append(Paragraph(f"&bull; {pt}", styles["bullet"]))
        story.append(Spacer(1, 3))

    # ==========================================
    # 8. NON-FUNCTIONAL REQUIREMENTS
    # ==========================================
    story.append(Paragraph("8. Non-Functional Requirements", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))

    nfr_data = [
        [Paragraph("<b>Category</b>", styles["th"]), Paragraph("<b>Specification & Technical Criteria</b>", styles["th"])],
        [Paragraph("Performance", styles["td_bold"]), Paragraph("Core CRUD and inventory query endpoints must respond in < 200 ms under typical single-restaurant concurrent loads. Database queries must utilize indexes on SKUs, categories, and foreign keys.", styles["td"])],
        [Paragraph("Security & Isolation", styles["td_bold"]), Paragraph("All external credentials (<code>GEMINI_API_KEY</code>, <code>TELEGRAM_BOT_TOKEN</code>) must reside strictly on the backend in <code>.env</code> and must never be transmitted to the frontend bundle.", styles["td"])],
        [Paragraph("Transaction Atomicity", styles["td_bold"]), Paragraph("Sales recording, ingredient depletions, and audit logging must execute within an atomic transaction. Any runtime error triggers an immediate database rollback.", styles["td"])],
        [Paragraph("Maintainability", styles["td_bold"]), Paragraph("Strict layered architecture (Router $\\rightarrow$ Service $\\rightarrow$ Model). Pydantic v2 schemas for all I/O contracts. Alembic for database version control and migration management.", styles["td"])],
        [Paragraph("Scalability", styles["td_bold"]), Paragraph("Stateless FastAPI architecture running asynchronously on <code>uvicorn</code>. Clean SQLAlchemy ORM abstraction enables frictionless transition from SQLite to PostgreSQL in multi-unit scaling.", styles["td"])],
        [Paragraph("Usability & Responsiveness", styles["td_bold"]), Paragraph("Responsive web interface styled with Tailwind CSS v4, supporting desktop terminals, kitchen tablets, and mobile devices. Conforms to WCAG 2.1 AA accessibility standards.", styles["td"])],
        [Paragraph("Data Integrity", styles["td_bold"]), Paragraph("Database constraints enforce non-negative stock (<code>current_quantity &gt;= 0</code>), unique SKU keys, and foreign-key referential integrity across recipes and sales records.", styles["td"])],
        [Paragraph("Standardized Error Handling", styles["td_bold"]), Paragraph("All responses conform to a unified JSON response envelope (<code>ApiSuccess&lt;T&gt;</code> or <code>ApiError</code>), providing structured error messages and machine-readable error reasons.", styles["td"])],
    ]
    nfr_table = Table(nfr_data, colWidths=[120, 384])
    nfr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(nfr_table)

    # ==========================================
    # 9. SYSTEM ARCHITECTURE
    # ==========================================
    arch_flow = []
    arch_flow.append(Paragraph("9. System Architecture", styles["h1"]))
    arch_flow.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    arch_flow.append(Paragraph(
        "RestaurantOps AI adheres to a strict layered architecture with clear separation of responsibilities. "
        "The service layer acts as the single gated point of entry for all business logic, shielding the database from direct "
        "manipulation by web controllers, background tasks, or AI agents.",
        styles["body"]
    ))

    arch_diagram = """+-------------------------------------------------------------------------------+
|                            FRONTEND CLIENT LAYER                              |
|   React 19 + TypeScript + Vite + Tailwind CSS v4 + Lucide React + Recharts    |
+-------------------------------------------------------------------------------+
                                     |  HTTPS / JSON (Vite Reverse Proxy)
                                     v
+-------------------------------------------------------------------------------+
|                             BACKEND API LAYER                                 |
|                      FastAPI (Asynchronous ASGI Server)                       |
|   [Health]   [Ingredients]   [Menu/Recipes]   [Sales]   [Inventory]   [AI]    |
+-------------------------------------------------------------------------------+
                                     |  Pydantic v2 Request/Response Validation
                                     v
+-------------------------------------------------------------------------------+
|                            SERVICE BUSINESS LAYER                             |
|  IngredientService  |  MenuService  |  SalesService  |  InventoryService      |
|  ProcurementService |  DashboardService  |  TelegramService  |  WeatherService|
+-------------------------------------------------------------------------------+
       |                               |                               |
       v                               v                               v
+---------------+             +---------------+               +---------------+
| DATABASE LAYER|             | AI AGENT LAYER|               |EXTERNAL SYSTEM|
| SQLAlchemy 2.x|             | Google Gemini |               |Telegram BotAPI|
| aiosqlite     |             | google-genai  |               |Open-Meteo API |
| SQLite DB     |             | Tool Calling  |               |APScheduler    |
+---------------+             +---------------+               +---------------+"""
    arch_flow.append(Preformatted(arch_diagram, styles["code_box"]))
    arch_flow.append(Spacer(1, 4))
    arch_flow.append(Paragraph("&bull; <b>Single Gated Service Layer:</b> All database operations flow through dedicated service functions. AI agents and background jobs call the same validated methods as web controllers.", styles["bullet"]))
    arch_flow.append(Paragraph("&bull; <b>End-to-End Asynchronous I/O:</b> FastAPI, aiosqlite, and SQLAlchemy 2.x async ORM ensure non-blocking event loop execution across all database queries and HTTP calls.", styles["bullet"]))
    arch_flow.append(Paragraph("&bull; <b>Type-Safe Contract Enforcement:</b> Pydantic v2 models validate all incoming payloads and serialize all outgoing JSON envelopes, preventing malformed data transmission.", styles["bullet"]))
    
    story.append(KeepTogether(arch_flow))

    # ==========================================
    # 10. THIRD-PARTY API INTEGRATIONS
    # ==========================================
    story.append(Paragraph("10. Third-Party API Integrations", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))

    integrations_data = [
        [Paragraph("<b>External Service</b>", styles["th"]), Paragraph("<b>SDK / Protocol</b>", styles["th"]), Paragraph("<b>Functional Responsibility & Architectural Boundaries</b>", styles["th"])],
        [Paragraph("Google Gemini API", styles["td_bold"]), Paragraph("<code>google-genai</code><br/>REST / gRPC", styles["td"]), Paragraph("Powers conversational assistant, inventory anomaly analysis, and procurement drafting. Interacts via registered service tool declarations; direct database querying is strictly prohibited.", styles["td"])],
        [Paragraph("Telegram Bot API", styles["td_bold"]), Paragraph("<code>httpx</code><br/>HTTPS REST", styles["td"]), Paragraph("Outbound notification pipeline for urgent low-stock alerts and morning operational digests. Operates asynchronously; failures log to database without interrupting user transactions.", styles["td"])],
        [Paragraph("Open-Meteo Weather", styles["td_bold"]), Paragraph("<code>httpx</code><br/>HTTPS REST", styles["td"]), Paragraph("Fetches local temperature and precipitation probabilities to provide contextual operational footfall insights. <i>Weather data is strictly contextual and never used as a primary inventory depletion signal.</i>", styles["td"])],
    ]
    integrations_table = Table(integrations_data, colWidths=[120, 94, 290])
    integrations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(integrations_table)

    # ==========================================
    # 11. SYSTEM WORKFLOWS
    # ==========================================
    story.append(Paragraph("11. System Workflows", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "RestaurantOps AI coordinates ten primary end-to-end operational workflows spanning daily restaurant operations:",
        styles["body"]
    ))

    workflows = [
        ("1. Inventory Item Onboarding", "Manager inputs ingredient specifications (name, SKU, category, unit, cost, min_quantity) $\\rightarrow$ Pydantic validates payload $\\rightarrow$ Database persists record and initializes stock balance at zero or intake level."),
        ("2. Menu Item & Recipe Configuration", "Manager creates a menu item $\\rightarrow$ specifies linked recipe ingredients and exact unit portions $\\rightarrow$ Backend validates existence of all referenced ingredients $\\rightarrow$ Persists relational recipe mapping."),
        ("3. Point-of-Sale Recording & Atomic Depletion", "POS records dish sale $\\rightarrow$ SalesService retrieves recipes $\\rightarrow$ verifies sufficient stock $\\rightarrow$ deducts ingredients $\\rightarrow$ writes audit records $\\rightarrow$ commits atomically."),
        ("4. Inventory Shortage Detection", "Scheduled cron or manual trigger compares current balances against minimum thresholds $\\rightarrow$ Flags items where `current_quantity <= min_quantity` $\\rightarrow$ Aggregates deficit metrics."),
        ("5. Procurement Recommendation Generation", "System evaluates stock deficits $\\rightarrow$ Applies deterministic reorder formula $\\rightarrow$ Gemini enriches proposal with vendor notes $\\rightarrow$ Drafts procurement proposal with cost estimates."),
        ("6. Manager Review & Order Authorization", "Manager reviews draft proposal on dashboard $\\rightarrow$ Evaluates line items and totals $\\rightarrow$ Executes explicit approval or rejection with notes $\\rightarrow$ Order state updates to `approved` or `rejected`."),
        ("7. Perishable Expiration Monitoring", "Background routine scans batch expiration dates $\\rightarrow$ Filters items expiring in $\\le 7$ days $\\rightarrow$ Categorizes urgency $\\rightarrow$ Recommends culinary specials to minimize waste."),
        ("8. Conversational AI Consultation", "Manager submits query via chat $\\rightarrow$ Gemini agent executes registered tool calls $\\rightarrow$ Service layer returns real data $\\rightarrow$ Gemini formats grounded answer."),
        ("9. Scheduled Background Sweeps", "APScheduler fires cron job $\\rightarrow$ Executes inventory health check $\\rightarrow$ Evaluates shortages and near-expiry items $\\rightarrow$ Records execution status to `automation_logs`."),
        ("10. Push Notification Alerting", "Critical stock condition detected $\\rightarrow$ Formats markdown notification payload $\\rightarrow$ Dispatches via Telegram Bot API asynchronously $\\rightarrow$ Verifies HTTP 200 delivery.")
    ]
    for title, desc in workflows:
        story.append(Paragraph(f"&bull; <b>{title}:</b> {desc}", styles["bullet"]))

    # ==========================================
    # 12. API SPECIFICATIONS
    # ==========================================
    story.append(Paragraph("12. API Specifications", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "The following catalog details the RESTful API endpoints for RestaurantOps AI. Endpoints verified in the current "
        "codebase (Stages 1–3) are designated as <b>Implemented</b>, while upcoming endpoints are marked as <i>Planned</i>.",
        styles["body"]
    ))

    api_endpoints = [
        ("GET", "/api/v1/health", "Implemented", "System health check, database ping, and environment status."),
        ("GET", "/api/v1/ingredients", "Implemented", "List ingredients with pagination, category filter, and search."),
        ("POST", "/api/v1/ingredients", "Implemented", "Register a new ingredient with SKU and threshold validation."),
        ("GET", "/api/v1/ingredients/{id}", "Implemented", "Retrieve complete ingredient details by unique ID."),
        ("PUT", "/api/v1/ingredients/{id}", "Implemented", "Update ingredient pricing, thresholds, or metadata."),
        ("DELETE", "/api/v1/ingredients/{id}", "Implemented", "Delete ingredient (rejected if linked to recipes or sales)."),
        ("GET", "/api/v1/menu-items", "Implemented", "List all menu items with pricing and active status."),
        ("POST", "/api/v1/menu-items", "Implemented", "Create a new restaurant menu item."),
        ("GET", "/api/v1/menu-items/{id}", "Implemented", "Retrieve a menu item and its recipe bill-of-materials."),
        ("PUT", "/api/v1/menu-items/{id}", "Implemented", "Update menu item details or active status flag."),
        ("POST", "/api/v1/menu-items/{id}/recipe", "Implemented", "Define or replace recipe ingredients for a menu item."),
        ("GET", "/api/v1/menu-items/{id}/recipe", "Implemented", "Retrieve recipe ingredient quantities for a menu item."),
        ("GET", "/api/v1/sales", "Implemented", "Query historical sales transactions with pagination."),
        ("POST", "/api/v1/sales", "Implemented", "Record sale and execute atomic recipe stock deductions."),
        ("GET", "/api/v1/sales/{id}", "Implemented", "Retrieve itemized sale details and consumed recipe line items."),
        ("POST", "/api/v1/inventory/adjust", "Implemented", "Record manual stock reconciliation, receiving, or waste."),
        ("GET", "/api/v1/inventory/transactions", "Implemented", "Query immutable inventory movement audit log."),
        ("GET", "/api/v1/inventory/low-stock", "Implemented", "Retrieve list of ingredients at or below minimum threshold."),
        ("GET", "/api/v1/inventory/expiring", "Implemented", "Retrieve ingredients approaching expiration date."),
        ("GET", "/api/v1/dashboard/summary", "Implemented", "Aggregate KPIs: stock value, low-stock count, sales totals."),
        ("POST", "/api/v1/agent/chat", "Planned", "Conversational interface endpoint for Gemini AI assistant."),
        ("GET", "/api/v1/procurement/recommendations", "Planned", "Fetch active AI-generated procurement proposals."),
        ("POST", "/api/v1/procurement/recommendations/{id}/approve", "Planned", "Approve a procurement proposal (transitions to approved)."),
        ("POST", "/api/v1/procurement/recommendations/{id}/reject", "Planned", "Reject a procurement proposal with manager rationale."),
        ("GET", "/api/v1/reports/daily", "Planned", "Generate consolidated daily operational performance report."),
        ("GET", "/api/v1/alerts", "Planned", "Fetch active system alerts and Telegram delivery history."),
    ]

    api_rows = [[Paragraph("<b>Method</b>", styles["th"]), Paragraph("<b>Endpoint Path</b>", styles["th"]), Paragraph("<b>Status</b>", styles["th"]), Paragraph("<b>Description</b>", styles["th"])]]
    for method, path, status, desc in api_endpoints:
        status_style = styles["status_impl"] if status == "Implemented" else styles["status_plan"]
        api_rows.append([
            Paragraph(f"<b>{method}</b>", styles["td_bold"]),
            Paragraph(f"<code>{path}</code>", styles["code"]),
            Paragraph(status, status_style),
            Paragraph(desc, styles["td"]),
        ])

    api_table = Table(api_rows, colWidths=[46, 178, 64, 216])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(api_table)

    # ==========================================
    # 13. USER INTERFACE AND COMPONENTS
    # ==========================================
    story.append(Paragraph("13. User Interface and System Components", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "The frontend is engineered as a responsive Single Page Application (SPA) prioritizing clean data visualization, "
        "rapid kitchen navigation, and mobile tablet compatibility:",
        styles["body"]
    ))

    ui_components = [
        ("Executive KPI Dashboard", "Displays high-level operational metrics: Total Inventory Asset Value, Low Stock Count, Approaching Expirations, Today's Sales Volume, and 7-day Recharts stock consumption trends."),
        ("Collapsible Sidebar Navigation", "Persistent desktop and mobile sidebar providing immediate access to Pantry Inventory, Menu & Recipes, Sales Register, Procurement Workbench, AI Assistant, and System Logs."),
        ("Top Operational Bar", "Houses breadcrumb pathing, backend API health status pill (Green/Red), quick-action Manual Stock Adjustment launcher, and local meteorological snippet."),
        ("Inventory Data Grid", "Searchable, sortable, and category-filtered grid displaying current stock against minimum thresholds, unit costs, dynamic status badges (In Stock, Low Stock, Depleted), and inline editing."),
        ("Menu & Recipe Studio", "Interface for composing culinary items and mapping bill-of-materials ingredient weights and portion measures."),
        ("Sales Register Console", "Simplified POS simulation interface allowing operators to log menu dish sales and monitor automatic ingredient consumption in real time."),
        ("AI Assistant Drawer", "Interactive conversational terminal for natural language queries with Google Gemini, equipped with one-click quick prompt pills."),
        ("Procurement Review Workbench", "Review board for evaluating draft purchasing recommendations, editing proposed quantities, inspecting cost impacts, and executing manager approvals or rejections."),
    ]
    for comp, desc in ui_components:
        story.append(Paragraph(f"&bull; <b>{comp}:</b> {desc}", styles["bullet"]))

    # ==========================================
    # 14. TECHNOLOGY STACK
    # ==========================================
    story.append(Paragraph("14. Technology Stack", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))

    tech_data = [
        [Paragraph("<b>Component Layer</b>", styles["th"]), Paragraph("<b>Technology</b>", styles["th"]), Paragraph("<b>Version</b>", styles["th"]), Paragraph("<b>Architectural Responsibility</b>", styles["th"])],
        [Paragraph("Frontend Framework", styles["td_bold"]), Paragraph("React", styles["td"]), Paragraph("19.x", styles["td"]), Paragraph("Declarative component UI architecture and virtual DOM.", styles["td"])],
        [Paragraph("Frontend Language", styles["td_bold"]), Paragraph("TypeScript", styles["td"]), Paragraph("5.x", styles["td"]), Paragraph("Type safety and schema contract parity with backend models.", styles["td"])],
        [Paragraph("Build Tooling", styles["td_bold"]), Paragraph("Vite", styles["td"]), Paragraph("6.x", styles["td"]), Paragraph("Fast ESM bundler and development proxy server.", styles["td"])],
        [Paragraph("CSS Framework", styles["td_bold"]), Paragraph("Tailwind CSS", styles["td"]), Paragraph("4.x", styles["td"]), Paragraph("Utility-first responsive layout and design system.", styles["td"])],
        [Paragraph("Data Visualization", styles["td_bold"]), Paragraph("Recharts", styles["td"]), Paragraph("2.x", styles["td"]), Paragraph("Interactive SVG consumption velocity and sales charts.", styles["td"])],
        [Paragraph("Backend Framework", styles["td_bold"]), Paragraph("FastAPI", styles["td"]), Paragraph("0.115+", styles["td"]), Paragraph("Asynchronous REST API controllers and dependency injection.", styles["td"])],
        [Paragraph("Language Runtime", styles["td_bold"]), Paragraph("Python", styles["td"]), Paragraph("3.11+", styles["td"]), Paragraph("Core server execution environment and math logic.", styles["td"])],
        [Paragraph("Data Validation", styles["td_bold"]), Paragraph("Pydantic", styles["td"]), Paragraph("v2.x", styles["td"]), Paragraph("Payload parsing, serialization, and input validation.", styles["td"])],
        [Paragraph("Database ORM", styles["td_bold"]), Paragraph("SQLAlchemy", styles["td"]), Paragraph("2.x (Async)", styles["td"]), Paragraph("Async ORM mapping, relation loading, and queries.", styles["td"])],
        [Paragraph("Database Engine", styles["td_bold"]), Paragraph("SQLite / aiosqlite", styles["td"]), Paragraph("3.x", styles["td"]), Paragraph("Zero-ops local relational storage with async driver.", styles["td"])],
        [Paragraph("Database Migrations", styles["td_bold"]), Paragraph("Alembic", styles["td"]), Paragraph("1.14+", styles["td"]), Paragraph("Declarative, version-controlled schema evolution.", styles["td"])],
        [Paragraph("AI Reasoning Engine", styles["td_bold"]), Paragraph("Google Gemini", styles["td"]), Paragraph("Current", styles["td"]), Paragraph("Conversational agent and structured tool calling.", styles["td"])],
        [Paragraph("AI Python SDK", styles["td_bold"]), Paragraph("<code>google-genai</code>", styles["td"]), Paragraph("2.x", styles["td"]), Paragraph("Official client library for Gemini API interactions.", styles["td"])],
        [Paragraph("Task Scheduling", styles["td_bold"]), Paragraph("APScheduler", styles["td"]), Paragraph("3.x", styles["td"]), Paragraph("Background cron scheduler for automated health sweeps.", styles["td"])],
        [Paragraph("Outbound Alerts", styles["td_bold"]), Paragraph("Telegram Bot API", styles["td"]), Paragraph("Current", styles["td"]), Paragraph("Push delivery of urgent shortage and summary messages.", styles["td"])],
        [Paragraph("Meteorological Data", styles["td_bold"]), Paragraph("Open-Meteo", styles["td"]), Paragraph("Current", styles["td"]), Paragraph("Contextual local temperature and precipitation feed.", styles["td"])],
        [Paragraph("Automated Testing", styles["td_bold"]), Paragraph("Pytest / Asyncio", styles["td"]), Paragraph("Current", styles["td"]), Paragraph("Asynchronous test suite verifying endpoints and models.", styles["td"])],
    ]
    tech_table = Table(tech_data, colWidths=[95, 100, 55, 254])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(tech_table)

    # ==========================================
    # 15. MVP SCOPE
    # ==========================================
    story.append(Paragraph("15. Minimum Viable Product (MVP) Scope", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "To ensure high software quality and rapid time-to-market, the MVP boundary is explicitly partitioned into included core capabilities "
        "and deliberate architectural exclusions:",
        styles["body"]
    ))

    scope_data = [
        [Paragraph("<b>Included Core Capabilities (In-Scope MVP)</b>", styles["th"]), Paragraph("<b>Explicit Exclusions (Out-of-Scope MVP)</b>", styles["th"])],
        [
            Paragraph(
                "&bull; Full CRUD management for pantry ingredients.<br/>"
                "&bull; Menu item creation with multi-ingredient recipes.<br/>"
                "&bull; Atomic sales recording with automated recipe deductions.<br/>"
                "&bull; Negative stock prevention and validation rules.<br/>"
                "&bull; Immutable inventory transaction audit ledger.<br/>"
                "&bull; Deterministic low-stock and near-expiry detection.<br/>"
                "&bull; AI-assisted procurement proposal generation.<br/>"
                "&bull; Manager approval/rejection procurement workflow.<br/>"
                "&bull; Conversational Gemini AI assistant with service tools.<br/>"
                "&bull; Telegram notification alerts for critical conditions.<br/>"
                "&bull; Contextual Open-Meteo weather integration.<br/>"
                "&bull; Background APScheduler inventory health checks.<br/>"
                "&bull; Executive KPI dashboard with Recharts trends.",
                styles["td"]
            ),
            Paragraph(
                "&bull; <b>No automated supplier purchasing:</b> System will not execute external purchase orders via vendor portals without manual approval.<br/>"
                "&bull; <b>No live payment processing:</b> Excludes credit card gateways or physical payment hardware.<br/>"
                "&bull; <b>No direct supplier EDI integration:</b> Electronic data interchange with wholesale distributors is reserved for future phases.<br/>"
                "&bull; <b>No multi-branch enterprise support:</b> Scoped for single-restaurant operation; no multi-location synchronization.<br/>"
                "&bull; <b>No complex ML predictive models:</b> Forecasting relies on deterministic run rates rather than multi-year neural nets.<br/>"
                "&bull; <b>No native mobile applications:</b> Excludes native iOS/Android binaries; supported via responsive web.",
                styles["td"]
            )
        ]
    ]
    scope_table = Table(scope_data, colWidths=[252, 252])
    scope_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(scope_table)

    # ==========================================
    # 16. FUTURE ENHANCEMENTS
    # ==========================================
    story.append(Paragraph("16. Future Enhancements", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "Following initial deployment and operational stabilization of the MVP, the roadmap envisions several architectural expansions:",
        styles["body"]
    ))
    enhancements = [
        ("Predictive Machine Learning Demand Forecasting", "Incorporate neural network regression models factoring in local holidays, seasonal trends, and reservations to predict future ingredient demand weeks in advance."),
        ("Direct Supplier Electronic Ordering (EDI)", "Connect approved purchase orders directly to major food distributors (Sysco, US Foods, Gordon Food Service) via punchout or API protocols upon manager approval."),
        ("Multi-Unit Enterprise Centralization", "Expand data models to support restaurant groups with shared commissary kitchens, inter-branch stock transfers, and consolidated master purchasing."),
        ("Camera Barcode & RFID Stock Scanning", "Enable kitchen mobile devices to scan GS1 barcodes during delivery intake, instantly reconciling physical receipts against expected purchase orders."),
        ("Kitchen Display System (KDS) & POS Integrations", "Direct plug-and-play webhook connectors for commercial POS platforms (Toast, Square, Clover, Aloha) to eliminate manual sales simulation entry."),
        ("Accounting & Invoicing Synchronization", "Automated two-way integration with general ledger accounting systems (QuickBooks Online, Xero, Sage) to synchronize actual Food Costs and invoices.")
    ]
    for title, desc in enhancements:
        story.append(Paragraph(f"&bull; <b>{title}:</b> {desc}", styles["bullet"]))

    # ==========================================
    # 17. ACCEPTANCE CRITERIA
    # ==========================================
    story.append(Paragraph("17. Acceptance Criteria", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "Verification of system functionality and readiness for production sign-off shall be determined against twelve "
        "concrete acceptance conditions:",
        styles["body"]
    ))

    ac_data = [
        [Paragraph("<b>Criteria ID</b>", styles["th"]), Paragraph("<b>Verification Category</b>", styles["th"]), Paragraph("<b>Acceptance Condition & Validation Method</b>", styles["th"])],
        [Paragraph("AC-01", styles["td_bold"]), Paragraph("Inventory CRUD", styles["td"]), Paragraph("Ingredients can be created, viewed, updated, and deleted. Submitting a duplicate SKU returns an explicit HTTP 400 Bad Request error.", styles["td"])],
        [Paragraph("AC-02", styles["td_bold"]), Paragraph("Recipe Integrity", styles["td"]), Paragraph("Menu items can be mapped to multiple ingredients. Deleting an ingredient referenced by an active recipe is rejected with referential integrity failure.", styles["td"])],
        [Paragraph("AC-03", styles["td_bold"]), Paragraph("Atomic Depletion", styles["td"]), Paragraph("Recording a dish sale deducts exact recipe quantities across all underlying ingredients in a single atomic transaction.", styles["td"])],
        [Paragraph("AC-04", styles["td_bold"]), Paragraph("Shortage Protection", styles["td"]), Paragraph("Attempting to record a sale where any required ingredient has insufficient stock is blocked cleanly, leaving all stock levels unchanged.", styles["td"])],
        [Paragraph("AC-05", styles["td_bold"]), Paragraph("Movement Auditing", styles["td"]), Paragraph("Every inventory addition, sale deduction, manual adjustment, and waste log writes an immutable record to <code>inventory_transactions</code>.", styles["td"])],
        [Paragraph("AC-06", styles["td_bold"]), Paragraph("Deterministic Reorders", styles["td"]), Paragraph("Procurement proposals calculate suggested quantities using the exact threshold formula: $Q = \\max((2 \\times \\text{min}) - \\text{current}, \\text{min})$.", styles["td"])],
        [Paragraph("AC-07", styles["td_bold"]), Paragraph("Human Approval Gate", styles["td"]), Paragraph("Procurement recommendations remain in <code>draft</code> state until an authorized manager explicitly approves or rejects them.", styles["td"])],
        [Paragraph("AC-08", styles["td_bold"]), Paragraph("Perishable Expiry", styles["td"]), Paragraph("Ingredients expiring within the configured lookahead horizon (default: 7 days) are returned accurately by the expiry monitoring endpoint.", styles["td"])],
        [Paragraph("AC-09", styles["td_bold"]), Paragraph("AI Tool Grounding", styles["td"]), Paragraph("The Gemini assistant answers user questions by calling validated backend service functions; direct database querying is strictly prohibited.", styles["td"])],
        [Paragraph("AC-10", styles["td_bold"]), Paragraph("Telegram Alerts", styles["td"]), Paragraph("Configured low-stock and near-expiry conditions trigger asynchronous Telegram bot notification messages to the target channel.", styles["td"])],
        [Paragraph("AC-11", styles["td_bold"]), Paragraph("Automation Auditing", styles["td"]), Paragraph("APScheduler scheduled sweeps execute on schedule without user presence and record execution timestamps, status, and traces to <code>automation_logs</code>.", styles["td"])],
        [Paragraph("AC-12", styles["td_bold"]), Paragraph("Response Uniformity", styles["td"]), Paragraph("All REST API responses conform to a unified JSON response envelope (<code>ApiSuccess&lt;T&gt;</code> or <code>ApiError</code>).", styles["td"])],
    ]
    ac_table = Table(ac_data, colWidths=[54, 110, 340])
    ac_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, SLATE_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, SLATE_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ac_table)

    # ==========================================
    # 18. DEPLOYMENT AND RESOURCE CONSIDERATIONS
    # ==========================================
    story.append(Paragraph("18. Deployment and Resource Considerations", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))

    story.append(Paragraph("<b>18.1 Local Development Environment:</b>", styles["body_bold"]))
    story.append(Paragraph(
        "The project requires Python 3.11+ and Node.js 18+. Backend setup entails creating a Python virtual environment, "
        "installing dependencies from <code>requirements.txt</code>, and applying Alembic migrations via <code>alembic upgrade head</code>. "
        "Frontend setup requires installing npm packages and starting the Vite dev server with proxy routing to <code>localhost:8000</code>.",
        styles["body"]
    ))

    story.append(Paragraph("<b>18.2 Server Environment Variables (<code>backend/.env</code>):</b>", styles["body_bold"]))
    env_sample = """PROJECT_NAME="RestaurantOps AI"
DATABASE_URL="sqlite+aiosqlite:///./restaurantops.db"
GEMINI_API_KEY="AIzaSy..."             # Google AI Studio API Key (backend only)
TELEGRAM_BOT_TOKEN="123456:ABC..."      # Telegram BotFather Token
TELEGRAM_CHAT_ID="-100..."             # Manager Notification Channel ID
WEATHER_LATITUDE="40.7128"             # Restaurant Location Latitude (NYC)
WEATHER_LONGITUDE="-74.0060"           # Restaurant Location Longitude (NYC)
LOG_LEVEL="INFO"
"""
    story.append(Preformatted(env_sample, styles["code_box"]))
    story.append(Spacer(1, 3))

    story.append(Paragraph("<b>18.3 Resource and Free-Tier Limits:</b>", styles["body_bold"]))
    story.append(Paragraph(
        "&bull; <b>Google Gemini API:</b> Free-tier Google AI Studio API keys operate under Requests Per Minute (RPM) and Tokens Per Minute (TPM) limits. "
        "The application incorporates exponential backoff to handle transient 429 quota codes without crashing.<br/>"
        "&bull; <b>Open-Meteo API:</b> Operates without an API key under open-access terms for non-commercial rates. Local caching prevents redundant hourly queries.<br/>"
        "&bull; <b>Telegram Bot API:</b> Free of charge with a global broadcast limit of 30 messages/second, well within single-restaurant needs.",
        styles["body"]
    ))

    # ==========================================
    # 19. CONCLUSION
    # ==========================================
    story.append(Paragraph("19. Conclusion", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SLATE_BORDER, spaceAfter=6))
    story.append(Paragraph(
        "RestaurantOps AI bridges a critical operational gap in modern hospitality management by fusing deterministic, recipe-driven "
        "inventory math with advanced generative reasoning powered by Google's Gemini API. By automating routine consumption deductions, "
        "detecting low-stock emergencies prior to peak service, and actively monitoring perishable expiration horizons, the system directly tackles "
        "the core drivers of food cost inflation and kitchen chaos.",
        styles["body"]
    ))
    story.append(Paragraph(
        "With a steadfast architectural commitment to a unified service layer, complete transaction auditability, strict secret isolation, "
        "and human-in-the-loop purchasing governance, RestaurantOps AI establishes a production-grade software foundation designed to optimize "
        "restaurant profitability today while paving the way for enterprise hospitality expansion.",
        styles["body"]
    ))

    return story


def build_pdf_with_exact_toc(output_path: str):
    # Pass 1: Build initial PDF to detect exact page numbers for each section
    doc1 = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    story1 = build_story(toc_page_map=None)
    doc1.build(story1, canvasmaker=NumberedCanvas)

    # Detect exact section page numbers using PyMuPDF
    doc_fitz = pymupdf.open(output_path)
    section_pages = {}
    for i, page in enumerate(doc_fitz):
        text = page.get_text()
        for sec_num in range(1, 20):
            if sec_num not in section_pages:
                prefix = f"{sec_num}. "
                for line in text.split("\n"):
                    clean = line.strip()
                    if clean.startswith(prefix) and not clean.endswith("..."):
                        section_pages[sec_num] = i + 1
                        break
    doc_fitz.close()
    print(f"Pass 1 detected section pages: {section_pages}")

    # Pass 2: Rebuild with exact detected section page numbers
    doc2 = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    story2 = build_story(toc_page_map=section_pages)
    doc2.build(story2, canvasmaker=NumberedCanvas)
    print(f"Pass 2 completed. Final PDF generated at: {output_path}")


if __name__ == "__main__":
    out = os.path.abspath(r"c:\Users\DELL\OneDrive\Desktop\project\RestaurantOps AI\docs\RestaurantOps_AI_SRS_Yohannes_Zewde.pdf")
    build_pdf_with_exact_toc(out)
