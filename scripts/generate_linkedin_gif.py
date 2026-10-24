"""Generate a high-definition, animated showcase GIF of ContextForge for LinkedIn.

Creates a 5-scene cinematic product tour:
1. Executive Overview & Live Estate Metrics (+13.34 pts lift, 87% attack defense)
2. Column-Level Lineage DAG (Multi-hop PII propagation trace)
3. Governed Asset Catalog (31 tables on Supabase Cloud PostgreSQL)
4. Steward Approval Queue (Policy-as-Code gate & human approval)
5. Talk-to-Data Agent & Empirical Benchmark Proof
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Canvas dimensions (LinkedIn optimal aspect ratio: 16:9 widescreen)
WIDTH = 1200
HEIGHT = 675

# Color Palette (Austere Monochrome Dark / Linear Aesthetic)
BG_CANVAS = (0, 0, 0)           # #000000 True Black
BG_CARD = (10, 10, 12)          # #0a0a0c Zinc surface
BG_CARD_SUBTLE = (16, 16, 20)   # #101014
BORDER_MUTED = (39, 39, 42)     # #27272a 1px borders
BORDER_ACTIVE = (82, 82, 91)    # #52525b
TEXT_MAIN = (255, 255, 255)     # #ffffff Crisp white
TEXT_MUTED = (161, 161, 170)    # #a1a1aa Zinc text
TEXT_SUBTLE = (113, 113, 122)   # #71717a
EMERALD = (52, 211, 153)        # #34d399 Success / Live status
AMBER = (251, 191, 36)          # #fbbf24 PII / Warning
RED = (248, 113, 113)           # #f87171 Refusal / Block

# Fonts
FONT_BOLD_PATH = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG_PATH = "C:/Windows/Fonts/segoeui.ttf"
FONT_MONO_PATH = "C:/Windows/Fonts/consola.ttf"

font_title = ImageFont.truetype(FONT_BOLD_PATH, 28)
font_subtitle = ImageFont.truetype(FONT_REG_PATH, 15)
font_card_num = ImageFont.truetype(FONT_BOLD_PATH, 36)
font_card_label = ImageFont.truetype(FONT_REG_PATH, 13)
font_code = ImageFont.truetype(FONT_MONO_PATH, 13)
font_code_bold = ImageFont.truetype(FONT_MONO_PATH, 14)
font_nav = ImageFont.truetype(FONT_BOLD_PATH, 13)
font_small = ImageFont.truetype(FONT_REG_PATH, 11)


def draw_topbar(draw, active_tab="overview"):
    # Main Header Bar
    draw.rectangle([0, 0, WIDTH, 54], fill=(8, 8, 10))
    draw.line([0, 54, WIDTH, 54], fill=BORDER_MUTED, width=1)

    # Logo Mark
    draw.polygon([(24, 18), (36, 18), (42, 36), (18, 36)], fill=(255, 255, 255))
    draw.text((50, 18), "CONTEXTFORGE", font=font_nav, fill=TEXT_MAIN)

    # Nav Tabs
    tabs = [
        ("overview", "Overview"),
        ("lineage", "Lineage DAG"),
        ("catalog", "Asset Catalog"),
        ("queue", "Steward Queue"),
        ("eval", "Benchmarks")
    ]
    x_pos = 200
    for tab_id, tab_label in tabs:
        is_active = (tab_id == active_tab)
        w = len(tab_label) * 8 + 24
        if is_active:
            draw.rectangle([x_pos, 12, x_pos + w, 42], fill=(24, 24, 28), outline=BORDER_ACTIVE, width=1)
            draw.text((x_pos + 12, 19), tab_label, font=font_nav, fill=TEXT_MAIN)
        else:
            draw.text((x_pos + 12, 19), tab_label, font=font_nav, fill=TEXT_MUTED)
        x_pos += w + 8

    # Live Supabase Badge in top right
    badge_x = WIDTH - 260
    draw.rectangle([badge_x, 14, WIDTH - 20, 40], fill=(12, 12, 16), outline=BORDER_MUTED, width=1)
    draw.ellipse([badge_x + 12, 24, badge_x + 20, 32], fill=EMERALD)
    draw.text((badge_x + 28, 19), "Estate: 31 Tables · Supabase Live", font=font_small, fill=TEXT_MAIN)


def render_scene_1_overview():
    """Scene 1: Platform Overview & High-Impact Metric Cards."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(img)
    draw_topbar(draw, active_tab="overview")

    # Headline
    draw.text((36, 76), "Governed Metadata Intelligence & Context Platform", font=font_title, fill=TEXT_MAIN)
    draw.text((36, 114), "Active context layer for enterprise AI agents: profiling schemas, mapping AST lineage, and enforcing policy guardrails.", font=font_subtitle, fill=TEXT_MUTED)

    # 6 Metric Cards (3x2 grid)
    metrics = [
        ("+13.34 pts", "Text-to-SQL Lift", "73.33% bare schema -> 86.67% governed context", EMERALD),
        ("87.0%", "PII Attacks Blocked", "20/23 adversarial prompt injection attacks halted", AMBER),
        ("94.3%", "PII F1-Score", "25/27 sensitive columns classified with zero leakage", TEXT_MAIN),
        ("97.4%", "Lineage Accuracy", "38/39 hand-verified columns mapped via AST parser", TEXT_MAIN),
        ("3 Pending", "Steward Approval Queue", "Human-in-the-loop review for policy proposals", AMBER),
        ("$0.1024", "Enrichment Unit Cost", "Per 1,000 API calls (gemini-3.1-flash-lite rates)", EMERALD),
    ]

    card_w = (WIDTH - 72 - 32) // 3
    card_h = 130
    for i, (val, label, subtext, color) in enumerate(metrics):
        col = i % 3
        row = i // 3
        x = 36 + col * (card_w + 16)
        y = 150 + row * (card_h + 16)

        draw.rectangle([x, y, x + card_w, y + card_h], fill=BG_CARD, outline=BORDER_MUTED, width=1)
        draw.text((x + 20, y + 16), val, font=font_card_num, fill=color)
        draw.text((x + 20, y + 66), label, font=font_nav, fill=TEXT_MAIN)
        draw.text((x + 20, y + 90), subtext, font=font_small, fill=TEXT_SUBTLE)

    # Bottom Architecture Banner
    draw.rectangle([36, 460, WIDTH - 36, 630], fill=BG_CARD, outline=BORDER_MUTED, width=1)
    draw.text((56, 480), "ENTERPRISE HYBRID ARCHITECTURE", font=font_nav, fill=TEXT_MUTED)
    draw.text((56, 510), "Live Cloud PostgreSQL (Supabase Mumbai) + Local DuckDB Embedded Engine + Fast Model Context Protocol", font=font_subtitle, fill=TEXT_MAIN)

    badges = ["Multi-Hop PII Propagation", "SHA-256 Audit Chain", "Zero-Shot Profiling", "sqlglot AST Traversal", "Role-Based Masking"]
    bx = 56
    for b in badges:
        bw = len(b) * 7 + 20
        draw.rectangle([bx, 560, bx + bw, 592], fill=(20, 20, 24), outline=BORDER_MUTED, width=1)
        draw.text((bx + 10, 568), b, font=font_small, fill=TEXT_MAIN)
        bx += bw + 12

    return img


def render_scene_2_lineage():
    """Scene 2: Column-Level Lineage DAG & Multi-Hop Tag Propagation."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(img)
    draw_topbar(draw, active_tab="lineage")

    draw.text((36, 76), "Column-Level Lineage DAG & Multi-Hop Propagation", font=font_title, fill=TEXT_MAIN)
    draw.text((36, 114), "Deterministic AST-parsed provenance. PII tags traverse downstream models with verified reason chains.", font=font_subtitle, fill=TEXT_MUTED)

    # Viewport Container
    draw.rectangle([36, 150, WIDTH - 36, 630], fill=BG_CARD, outline=BORDER_MUTED, width=1)

    # 4 Sequential Nodes in DAG
    nodes = [
        (80, 240, "raw_olist_customers", "Raw Ingestion", "customer_id [ORIGIN PII]"),
        (330, 240, "stg_customers", "Staging View", "customer_id [DIRECT_COPY]"),
        (580, 240, "dim_customers", "Analytics Dimension", "customer_unique_id [AGGREGATE]"),
        (830, 240, "customer_ltv", "Certified BI Mart", "customer_unique_id [LTV_METRIC]")
    ]

    for i, (nx, ny, title, layer, col_text) in enumerate(nodes):
        # Card
        draw.rectangle([nx, ny, nx + 210, ny + 150], fill=BG_CARD_SUBTLE, outline=BORDER_ACTIVE, width=1)
        draw.rectangle([nx, ny, nx + 210, ny + 32], fill=(24, 24, 30))
        draw.text((nx + 12, ny + 8), layer.upper(), font=font_small, fill=TEXT_MUTED)
        draw.text((nx + 12, ny + 45), title, font=font_nav, fill=TEXT_MAIN)

        # Sensitive tag pill
        draw.rectangle([nx + 12, ny + 80, nx + 198, ny + 130], fill=(25, 20, 10), outline=AMBER, width=1)
        draw.text((nx + 18, ny + 88), "TAG: PII:CUSTOMER_ID", font=font_small, fill=AMBER)
        draw.text((nx + 18, ny + 106), col_text, font=font_small, fill=TEXT_MUTED)

        # Connector arrow to next node
        if i < len(nodes) - 1:
            next_x = nodes[i + 1][0]
            arrow_y = ny + 75
            draw.line([nx + 210, arrow_y, next_x, arrow_y], fill=AMBER, width=2)
            draw.polygon([(next_x - 8, arrow_y - 6), (next_x, arrow_y), (next_x - 8, arrow_y + 6)], fill=AMBER)

    # Reason Chain Audit Box
    draw.rectangle([80, 440, WIDTH - 80, 590], fill=(14, 14, 18), outline=BORDER_MUTED, width=1)
    draw.text((100, 455), "AUDITABLE PROPAGATION REASON CHAIN (SHA-256 VERIFIED)", font=font_nav, fill=AMBER)
    trace = [
        "Hop 0: raw_olist_customers.customer_id (Origin Ingestion · Tag: PII:CUSTOMER_ID · Confidence: 1.000)",
        "Hop 1: stg_customers.customer_id (Transformation: DIRECT_COPY · Policy POL-007 Fired · Conf: 0.980)",
        "Hop 2: dim_customers.customer_unique_id (Transformation: AGGREGATE/JOIN · Policy POL-008 Fired · Conf: 0.960)",
        "Hop 3: customer_ltv.customer_unique_id (Downstream BI Mart · Role Masking Enforced for ANALYST · Conf: 0.941)"
    ]
    for idx, t in enumerate(trace):
        draw.text((100, 485 + idx * 24), "• " + t, font=font_small, fill=TEXT_MAIN)

    return img


def render_scene_3_catalog():
    """Scene 3: Governed Asset Catalog with 31 Cloud Tables."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(img)
    draw_topbar(draw, active_tab="catalog")

    draw.text((36, 76), "Governed Asset Catalog Explorer", font=font_title, fill=TEXT_MAIN)
    draw.text((36, 114), "31 materialized enterprise tables on Supabase Cloud. Schema inspection, data quality scores, and role masking.", font=font_subtitle, fill=TEXT_MUTED)

    # Split Layout
    draw.rectangle([36, 150, 360, 630], fill=BG_CARD, outline=BORDER_MUTED, width=1)
    draw.rectangle([380, 150, WIDTH - 36, 630], fill=BG_CARD, outline=BORDER_MUTED, width=1)

    # Left: Tree View
    draw.text((54, 170), "DATA ESTATE (31 TABLES)", font=font_nav, fill=TEXT_MUTED)
    tables = [
        ("dim_customers", True, "9 cols · PII Protected"),
        ("fct_orders", False, "12 cols · Certified"),
        ("dim_products", False, "8 cols · Clean"),
        ("dim_sellers", False, "6 cols · Staged"),
        ("stg_reviews", True, "7 cols · PII Protected"),
        ("customer_ltv", False, "5 cols · BI Mart"),
        ("mart_geo_performance", False, "6 cols · BI Mart"),
        ("stg_payments", False, "5 cols · Financial"),
    ]
    for idx, (tname, has_pii, desc) in enumerate(tables):
        ty = 205 + idx * 50
        if tname == "dim_customers":
            draw.rectangle([46, ty - 6, 350, ty + 38], fill=(24, 24, 32), outline=BORDER_ACTIVE, width=1)
            draw.text((60, ty), "> " + tname, font=font_nav, fill=TEXT_MAIN)
        else:
            draw.text((60, ty), "  " + tname, font=font_nav, fill=TEXT_MUTED)
        draw.text((60, ty + 18), desc, font=font_small, fill=AMBER if has_pii else TEXT_SUBTLE)

    # Right: Detail Inspector
    draw.text((410, 175), "cforge.public.dim_customers", font=font_title, fill=TEXT_MAIN)
    draw.rectangle([410, 215, 520, 240], fill=(20, 35, 25), outline=EMERALD, width=1)
    draw.text((422, 221), "CERTIFIED MART", font=font_small, fill=EMERALD)

    draw.rectangle([530, 215, 640, 240], fill=(20, 20, 25), outline=BORDER_MUTED, width=1)
    draw.text((542, 221), "QUALITY: 0.94 / 1.0", font=font_small, fill=TEXT_MAIN)

    draw.rectangle([650, 215, 780, 240], fill=(35, 25, 10), outline=AMBER, width=1)
    draw.text((662, 221), "2 PII COLUMNS MASKED", font=font_small, fill=AMBER)

    # Columns Table Header
    draw.rectangle([410, 260, WIDTH - 56, 290], fill=(16, 16, 20))
    draw.text((420, 268), "COLUMN", font=font_small, fill=TEXT_MUTED)
    draw.text((580, 268), "TYPE", font=font_small, fill=TEXT_MUTED)
    draw.text((680, 268), "CLASSIFICATION", font=font_small, fill=TEXT_MUTED)
    draw.text((880, 268), "POLICY RULE", font=font_small, fill=TEXT_MUTED)

    # Columns Rows
    col_data = [
        ("customer_unique_id", "VARCHAR", "PII: CUSTOMER_ID", "POL-002: Masked for Analyst", AMBER),
        ("primary_zip", "VARCHAR", "PII: POSTAL_CODE", "POL-006: Redacted", AMBER),
        ("customer_city", "VARCHAR", "PUBLIC DIMENSION", "POL-001: Description Clean", TEXT_MUTED),
        ("customer_state", "VARCHAR", "PUBLIC DIMENSION", "POL-001: Description Clean", TEXT_MUTED),
        ("lifetime_orders", "INTEGER", "METRIC: COUNT", "Certified Aggregation", EMERALD),
        ("lifetime_spend_brl", "DOUBLE", "METRIC: FINANCIAL", "Certified Currency", EMERALD),
    ]
    for idx, (col_name, c_type, c_class, c_pol, color) in enumerate(col_data):
        cy = 300 + idx * 48
        draw.line([410, cy + 40, WIDTH - 56, cy + 40], fill=BORDER_MUTED, width=1)
        draw.text((420, cy + 10), col_name, font=font_code_bold, fill=TEXT_MAIN)
        draw.text((580, cy + 10), c_type, font=font_code, fill=TEXT_MUTED)
        draw.text((680, cy + 10), c_class, font=font_small, fill=color)
        draw.text((880, cy + 10), c_pol, font=font_small, fill=TEXT_SUBTLE)

    return img


def render_scene_4_queue(approved=False):
    """Scene 4: Steward Approval Queue & Policy Gating."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(img)
    draw_topbar(draw, active_tab="queue")

    draw.text((36, 76), "Steward Approval Queue (Human-in-the-Loop Gate)", font=font_title, fill=TEXT_MAIN)
    draw.text((36, 114), "Autonomous AI proposals gated by Policy-as-Code. Requires steward review before catalog commit.", font=font_subtitle, fill=TEXT_MUTED)

    # Proposal Card
    draw.rectangle([36, 160, WIDTH - 36, 440], fill=BG_CARD, outline=BORDER_ACTIVE if approved else AMBER, width=2)

    # Card Header
    draw.text((60, 185), "CHANGE PROPOSAL #CF-PROP-9821", font=font_nav, fill=TEXT_MUTED)
    status_text = "STATUS: APPROVED · COMMITTED TO CATALOG" if approved else "STATUS: PENDING STEWARD REVIEW"
    status_color = EMERALD if approved else AMBER
    draw.text((WIDTH - 420, 185), status_text, font=font_nav, fill=status_color)

    # Details
    draw.text((60, 225), "Asset ID: cforge.public.dim_customers.primary_zip", font=font_card_label, fill=TEXT_MUTED)
    draw.text((60, 245), "Change Type: ADD_TAG (PII: POSTAL_CODE)", font=font_title, fill=TEXT_MAIN)
    draw.text((60, 290), "Proposed By: Agent_Classifier (Confidence: 0.95)", font=font_subtitle, fill=TEXT_MUTED)
    draw.text((60, 315), "Gating Policy: POL-002: PII classification requires compliance steward human sign-off.", font=font_subtitle, fill=AMBER)

    if not approved:
        # Action Buttons (Before approval)
        draw.rectangle([60, 360, 220, 405], fill=(255, 255, 255), outline=TEXT_MAIN, width=1)
        draw.text((88, 375), "APPROVE [Enter]", font=font_nav, fill=(0, 0, 0))

        draw.rectangle([240, 360, 380, 405], fill=(20, 20, 24), outline=BORDER_MUTED, width=1)
        draw.text((276, 375), "REJECT [Esc]", font=font_nav, fill=TEXT_MUTED)
    else:
        # Approved Confirmation Banner
        draw.rectangle([60, 360, 520, 405], fill=(15, 35, 20), outline=EMERALD, width=1)
        draw.text((80, 375), "[APPROVED] Compliance Steward Alice (Signed)", font=font_nav, fill=EMERALD)

    # Immutable Audit Log Chain
    draw.rectangle([36, 465, WIDTH - 36, 620], fill=BG_CARD_SUBTLE, outline=BORDER_MUTED, width=1)
    draw.text((56, 485), "CRYPTOGRAPHIC AUDIT CHAIN (SHA-256)", font=font_nav, fill=TEXT_MUTED)
    draw.text((56, 515), "Hash: 8f9b4c09d3e8e21a4f00923b... -> Genesis chained with prev_hash", font=font_code, fill=TEXT_MAIN)
    draw.text((56, 545), "Timestamp: 2026-10-24T21:40:00Z · Action: CATALOG_COMMIT · Actor: Governance_Steward", font=font_code, fill=TEXT_MUTED)
    draw.text((56, 575), "Policy Audit Ledger Status: 100% Tamper-Proof Hash Chain Verified", font=font_code, fill=EMERALD)

    return img


def render_scene_5_agent():
    """Scene 5: Talk-to-Data AI Agent & Evaluation Benchmark."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(img)
    draw_topbar(draw, active_tab="eval")

    draw.text((36, 76), "Talk-to-Data Agent & Empirical Benchmark Proof", font=font_title, fill=TEXT_MAIN)
    draw.text((36, 114), "Empirically validated +13.34 pt Text-to-SQL accuracy lift with 87% PII prompt attack defense.", font=font_subtitle, fill=TEXT_MUTED)

    # Chat Console Panel (Left)
    draw.rectangle([36, 150, 680, 630], fill=BG_CARD, outline=BORDER_MUTED, width=1)
    draw.text((56, 175), "TALK-TO-DATA AGENT CONSOLE (ROLE: ANALYST)", font=font_nav, fill=TEXT_MUTED)

    # User Query Box
    draw.rectangle([56, 210, 660, 260], fill=(20, 20, 25), outline=BORDER_ACTIVE, width=1)
    draw.text((72, 225), "Q: What is our customer lifetime value breakdown by VIP tiers?", font=font_subtitle, fill=TEXT_MAIN)

    # Guardrail Verification Pill
    draw.rectangle([56, 280, 480, 310], fill=(15, 30, 20), outline=EMERALD, width=1)
    draw.text((70, 290), "[PASSED] POLICIES EVALUATED: Zero unmasked PII returned to Analyst", font=font_small, fill=EMERALD)

    # Agent Generated Governed SQL
    draw.rectangle([56, 330, 660, 460], fill=(6, 6, 8), outline=BORDER_MUTED, width=1)
    draw.text((72, 345), "-- Discovered certified mart 'customer_ltv' via MCP search", font=font_code, fill=TEXT_SUBTLE)
    draw.text((72, 370), "SELECT ltv_segment, COUNT(*) AS customer_count,", font=font_code_bold, fill=TEXT_MAIN)
    draw.text((72, 395), "       ROUND(AVG(total_lifetime_spend_brl), 2) AS avg_spend,", font=font_code_bold, fill=TEXT_MAIN)
    draw.text((72, 420), "       ROUND(AVG(satisfaction_score), 2) AS avg_csat", font=font_code_bold, fill=TEXT_MAIN)
    draw.text((72, 440), "FROM customer_ltv GROUP BY ltv_segment ORDER BY 2 DESC;", font=font_code_bold, fill=TEXT_MAIN)

    # Execution Result Snippet
    draw.rectangle([56, 480, 660, 605], fill=(12, 12, 16), outline=BORDER_MUTED, width=1)
    draw.text((72, 495), "EXECUTION RESULT (DUCKDB ENGINE):", font=font_small, fill=TEXT_MUTED)
    draw.text((72, 520), "VIP Tier    | Customers | Avg Spend   | Avg CSAT", font=font_code, fill=TEXT_MUTED)
    draw.text((72, 545), "Diamond     | 4,120     | R$ 2,450.00 | 4.8 / 5.0", font=font_code, fill=EMERALD)
    draw.text((72, 570), "Gold        | 12,890    | R$ 890.50   | 4.4 / 5.0", font=font_code, fill=TEXT_MAIN)

    # Right: Benchmark Lift Scorecard
    draw.rectangle([705, 150, WIDTH - 36, 630], fill=BG_CARD, outline=BORDER_MUTED, width=1)
    draw.text((725, 175), "HEADLINE BENCHMARK LIFT", font=font_nav, fill=TEXT_MUTED)

    draw.text((725, 220), "+13.34 pts", font=font_card_num, fill=EMERALD)
    draw.text((725, 270), "Text-to-SQL Execution Accuracy Lift", font=font_nav, fill=TEXT_MAIN)

    # Side-by-side comparison bar
    draw.text((725, 320), "Governed Context: 86.67% (39/45 matched)", font=font_small, fill=TEXT_MAIN)
    draw.rectangle([725, 345, 725 + int(420 * 0.8667), 365], fill=EMERALD)

    draw.text((725, 385), "Bare Schema Baseline: 73.33% (33/45 matched)", font=font_small, fill=TEXT_MUTED)
    draw.rectangle([725, 410, 725 + int(420 * 0.7333), 430], fill=BORDER_ACTIVE)

    # Summary Stats
    stats = [
        ("Defect Catch Rate", "62.5% (5/8 schema defects caught)"),
        ("PII Classification F1", "94.3% on held-out test split"),
        ("Lineage Accuracy", "97.4% (38/39 hand-verified columns)"),
        ("Enrichment Cost", "$0.1024 per 1k API calls")
    ]
    for idx, (s_name, s_val) in enumerate(stats):
        sy = 465 + idx * 36
        draw.text((725, sy), s_name + ":", font=font_small, fill=TEXT_MUTED)
        draw.text((880, sy), s_val, font=font_small, fill=TEXT_MAIN)

    return img


def generate_gif(output_path="docs/contextforge_overview.gif"):
    """Compile scenes into a smooth, looped GIF."""
    print("Rendering Scene 1: Overview...")
    s1 = render_scene_1_overview()

    print("Rendering Scene 2: Lineage DAG...")
    s2 = render_scene_2_lineage()

    print("Rendering Scene 3: Asset Catalog...")
    s3 = render_scene_3_catalog()

    print("Rendering Scene 4A: Steward Queue Pending...")
    s4a = render_scene_4_queue(approved=False)

    print("Rendering Scene 4B: Steward Queue Approved...")
    s4b = render_scene_4_queue(approved=True)

    print("Rendering Scene 5: Talk-to-Data Agent & Benchmark...")
    s5 = render_scene_5_agent()

    # Frames sequence with frame durations in milliseconds
    # Scene 1: 2500ms
    # Scene 2: 2800ms
    # Scene 3: 2800ms
    # Scene 4A: 1600ms -> Scene 4B (Approved transition): 2000ms
    # Scene 5: 3200ms
    frames = [s1, s2, s3, s4a, s4b, s5]
    durations = [2600, 3000, 3000, 1600, 2200, 3500]

    # Convert to 256-color palette with diffusion for compact, crisp GIF
    p_frames = []
    for f in frames:
        p_frame = f.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
        p_frames.append(p_frame)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Saving animated GIF to {output_file}...")
    p_frames[0].save(
        str(output_file),
        format="GIF",
        save_all=True,
        append_images=p_frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"SUCCESS: Generated {output_file} ({size_mb:.2f} MB)")
    return output_file


if __name__ == "__main__":
    generate_gif()
