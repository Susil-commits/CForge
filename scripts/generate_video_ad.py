"""Generate a high-production-value video commercial for ContextForge.

Resolution: 1280x720 (720p HD @ 30 FPS, 20 seconds, 600 frames)
Format: MP4 (H.264 / mp4v codec compatible with LinkedIn, Twitter, GitHub)

Script:
- 00:00 - 04:00 | The Enterprise Problem (The AI Context Crisis)
- 04:00 - 08:00 | Meet ContextForge (The Governed Metadata Layer)
- 08:00 - 13:00 | Feature Showcase (AST Lineage DAG & Policy-as-Code Approval)
- 13:00 - 17:00 | Empirical Proof & Benchmarks (+13.34 pt lift, 87% defense)
- 17:00 - 20:00 | Outro & CTA (GitHub / Supabase Live)
"""

import math
import os
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1280
HEIGHT = 720
FPS = 30
TOTAL_SECONDS = 20
TOTAL_FRAMES = FPS * TOTAL_SECONDS  # 600 frames

# Palettes
BG_CANVAS = (4, 4, 6)
BG_CARD = (12, 12, 16)
BG_CARD_SUBTLE = (18, 18, 24)
BORDER_MUTED = (39, 39, 45)
BORDER_ACTIVE = (82, 82, 95)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (161, 161, 170)
TEXT_SUBTLE = (113, 113, 122)
EMERALD = (52, 211, 153)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
BLUE = (96, 165, 250)

# Fonts
FONT_BOLD_PATH = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG_PATH = "C:/Windows/Fonts/segoeui.ttf"
FONT_MONO_PATH = "C:/Windows/Fonts/consola.ttf"

font_hero = ImageFont.truetype(FONT_BOLD_PATH, 42)
font_title = ImageFont.truetype(FONT_BOLD_PATH, 28)
font_subtitle = ImageFont.truetype(FONT_REG_PATH, 18)
font_card_num = ImageFont.truetype(FONT_BOLD_PATH, 40)
font_nav = ImageFont.truetype(FONT_BOLD_PATH, 14)
font_code = ImageFont.truetype(FONT_MONO_PATH, 13)
font_code_bold = ImageFont.truetype(FONT_MONO_PATH, 15)
font_small = ImageFont.truetype(FONT_REG_PATH, 12)


def clamp(val, low=0.0, high=1.0):
    return max(low, min(high, val))


def ease_out_cubic(x):
    return 1 - pow(1 - x, 3)


def draw_header(draw, active_tab="OVERVIEW"):
    draw.rectangle([0, 0, WIDTH, 54], fill=(8, 8, 10))
    draw.line([0, 54, WIDTH, 54], fill=BORDER_MUTED, width=1)
    draw.polygon([(30, 18), (42, 18), (48, 36), (24, 36)], fill=(255, 255, 255))
    draw.text((58, 18), "CONTEXTFORGE", font=font_nav, fill=TEXT_WHITE)

    # Tabs
    tabs = ["OVERVIEW", "LINEAGE DAG", "ASSET CATALOG", "STEWARD QUEUE", "BENCHMARKS"]
    x = 220
    for t in tabs:
        w = len(t) * 9 + 20
        is_active = (t == active_tab)
        if is_active:
            draw.rectangle([x, 12, x + w, 42], fill=(24, 24, 30), outline=BORDER_ACTIVE, width=1)
            draw.text((x + 10, 19), t, font=font_nav, fill=TEXT_WHITE)
        else:
            draw.text((x + 10, 19), t, font=font_nav, fill=TEXT_MUTED)
        x += w + 8

    # Live Supabase Badge
    bx = WIDTH - 280
    draw.rectangle([bx, 14, WIDTH - 24, 40], fill=(14, 14, 18), outline=BORDER_MUTED, width=1)
    draw.ellipse([bx + 12, 24, bx + 20, 32], fill=EMERALD)
    draw.text((bx + 28, 19), "Estate: 31 Tables · Supabase Live", font=font_small, fill=TEXT_WHITE)


def render_frame(frame_idx):
    """Render frame_idx out of TOTAL_FRAMES."""
    t = frame_idx / FPS  # Current time in seconds
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_CANVAS)
    draw = ImageDraw.Draw(img)

    # =========================================================================
    # SCENE 1: The Problem (0.0s - 4.0s)
    # =========================================================================
    if t < 4.0:
        progress = clamp(t / 4.0)
        # Pulse vignette border
        red_intensity = int(80 * (0.5 + 0.5 * math.sin(t * 8)))
        draw.rectangle([0, 0, WIDTH, HEIGHT], outline=(red_intensity, 15, 15), width=3)

        # Warning Tag
        draw.rectangle([WIDTH // 2 - 130, 80, WIDTH // 2 + 130, 115], fill=(30, 10, 10), outline=RED, width=1)
        draw.text((WIDTH // 2 - 110, 89), "! THE ENTERPRISE AI PROBLEM", font=font_nav, fill=RED)

        # Main Question
        draw.text((WIDTH // 2 - 340, 140), "Connecting LLMs Directly to Raw Data Fails.", font=font_hero, fill=TEXT_WHITE)
        draw.text((WIDTH // 2 - 310, 195), "Bare database schemas give AI zero business definitions and zero privacy controls.", font=font_subtitle, fill=TEXT_MUTED)

        # 3 Pain Point Cards animating in sequentially
        cards = [
            ("01 / BROKEN JOINS", "Cryptic DDL ('usr_id', 'stat_cd') causes query crashes and wrong metric aggregations.", 0.8),
            ("02 / SILENT PII LEAKS", "When asked for customer patterns, agents unmask phone numbers and addresses.", 1.6),
            ("03 / 73.3% ACCURACY FLOOR", "12 out of 45 real enterprise queries fail execution without governed context.", 2.4),
        ]

        card_w = 360
        card_h = 240
        for i, (title, desc, appear_t) in enumerate(cards):
            if t >= appear_t:
                card_prog = clamp((t - appear_t) / 0.5)
                eased = ease_out_cubic(card_prog)
                x = 70 + i * (card_w + 35)
                # Slide up animation
                y = int(380 - 80 * (1 - eased))

                draw.rectangle([x, y, x + card_w, y + card_h], fill=BG_CARD, outline=(RED if i == 1 else BORDER_MUTED), width=1)
                draw.text((x + 24, y + 24), title, font=font_nav, fill=RED if i == 1 else AMBER)
                draw.text((x + 24, y + 70), desc, font=font_subtitle, fill=TEXT_WHITE)

                # Bottom failure stat
                if i == 0:
                    draw.text((x + 24, y + 175), "Execution match: FAILED", font=font_code, fill=RED)
                elif i == 1:
                    draw.text((x + 24, y + 175), "Regulatory Risk: CRITICAL", font=font_code, fill=RED)
                elif i == 2:
                    draw.text((x + 24, y + 175), "12/45 queries hallucinated", font=font_code, fill=AMBER)

    # =========================================================================
    # SCENE 2: The Solution / Introduction (4.0s - 8.0s)
    # =========================================================================
    elif t < 8.0:
        local_t = t - 4.0
        draw_header(draw, active_tab="OVERVIEW")

        # Animated reveal of ContextForge
        draw.text((WIDTH // 2 - 200, 90), "THE SOLUTION", font=font_nav, fill=EMERALD)
        draw.text((WIDTH // 2 - 260, 120), "CONTEXTFORGE", font=font_hero, fill=TEXT_WHITE)
        draw.text((WIDTH // 2 - 360, 175), "The Governed Metadata Enrichment & Context Platform for Enterprise AI", font=font_subtitle, fill=TEXT_MUTED)

        # 4 Core System Engine Blocks
        engines = [
            ("Statistical Profiler", "Non-LLM profiling computes cardinality, nulls, and distributions locally.", EMERALD),
            ("AST Lineage Engine", "sqlglot parser maps deterministic column provenance across all transforms.", BLUE),
            ("Policy-as-Code Gate", "15 declarative rules intercept uncertified writes and PII leakage.", AMBER),
            ("Governed MCP Server", "Model Context Protocol provides role-based column masking directly to agents.", TEXT_WHITE)
        ]

        gw = 560
        gh = 170
        for i, (eng_title, eng_desc, eng_color) in enumerate(engines):
            col = i % 2
            row = i // 2
            x = 60 + col * (gw + 40)
            y = 230 + row * (gh + 30)

            draw.rectangle([x, y, x + gw, y + gh], fill=BG_CARD, outline=BORDER_MUTED, width=1)
            draw.rectangle([x, y, x + 6, y + gh], fill=eng_color)
            draw.text((x + 24, y + 24), eng_title, font=font_title, fill=TEXT_WHITE)
            draw.text((x + 24, y + 68), eng_desc, font=font_subtitle, fill=TEXT_MUTED)
            draw.text((x + 24, y + 120), "STATUS: VERIFIED & ACTIVE", font=font_small, fill=eng_color)

        # Bottom live status
        draw.rectangle([60, 630, WIDTH - 60, 670], fill=BG_CARD_SUBTLE, outline=BORDER_MUTED, width=1)
        draw.text((80, 642), "LIVE HYBRID INFRASTRUCTURE: Supabase Cloud PostgreSQL (31 Tables) + Embedded DuckDB Engine", font=font_small, fill=EMERALD)

    # =========================================================================
    # SCENE 3: Feature Deep Dive (8.0s - 13.0s)
    # =========================================================================
    elif t < 13.0:
        local_t = t - 8.0

        if local_t < 2.5:
            # Sub-scene A: Column Lineage DAG
            draw_header(draw, active_tab="LINEAGE DAG")
            draw.text((60, 76), "FEATURE 1: COLUMN-LEVEL LINEAGE DAG", font=font_title, fill=TEXT_WHITE)
            draw.text((60, 114), "Tracing data origin, downstream transforms, and multi-hop PII tag propagation.", font=font_subtitle, fill=TEXT_MUTED)

            draw.rectangle([60, 150, WIDTH - 60, 650], fill=BG_CARD, outline=BORDER_MUTED, width=1)

            # 4 DAG nodes with animated arrow glow
            dag_nodes = [
                (100, 260, "raw_olist_customers", "Raw Source", "customer_id [ORIGIN PII]"),
                (380, 260, "stg_customers", "Staging View", "customer_id [DIRECT_COPY]"),
                (660, 260, "dim_customers", "Analytics Dim", "customer_unique_id [AGGREGATE]"),
                (940, 260, "customer_ltv", "Certified Mart", "customer_unique_id [LTV_METRIC]")
            ]
            for i, (nx, ny, ntitle, nlayer, ncol) in enumerate(dag_nodes):
                draw.rectangle([nx, ny, nx + 220, ny + 160], fill=BG_CARD_SUBTLE, outline=BORDER_ACTIVE, width=1)
                draw.text((nx + 16, ny + 14), nlayer.upper(), font=font_small, fill=TEXT_MUTED)
                draw.text((nx + 16, ny + 45), ntitle, font=font_nav, fill=TEXT_WHITE)

                draw.rectangle([nx + 14, ny + 85, nx + 206, ny + 140], fill=(28, 22, 10), outline=AMBER, width=1)
                draw.text((nx + 20, ny + 95), "TAG: PII:CUSTOMER_ID", font=font_small, fill=AMBER)
                draw.text((nx + 20, ny + 115), ncol, font=font_small, fill=TEXT_MUTED)

                if i < len(dag_nodes) - 1:
                    next_x = dag_nodes[i + 1][0]
                    # Arrow connecting
                    draw.line([nx + 220, ny + 80, next_x, ny + 80], fill=AMBER, width=2)
                    draw.polygon([(next_x - 8, ny + 74), (next_x, ny + 80), (next_x - 8, ny + 86)], fill=AMBER)

            # Audit trace line
            draw.rectangle([100, 480, WIDTH - 100, 610], fill=(16, 16, 22), outline=BORDER_MUTED, width=1)
            draw.text((120, 500), "AUDITABLE PROPAGATION TRACE (SHA-256 SECURED)", font=font_nav, fill=AMBER)
            draw.text((120, 530), "• Hop 0 -> Hop 1: Direct Clean Projection (Confidence: 0.980 · Policy POL-007 Fired)", font=font_small, fill=TEXT_WHITE)
            draw.text((120, 555), "• Hop 1 -> Hop 2: Group By Aggregation (Confidence: 0.960 · Policy POL-008 Fired)", font=font_small, fill=TEXT_WHITE)
            draw.text((120, 580), "• Hop 2 -> Hop 3: Downstream LTV Mart (Masking Enforced for Role: ANALYST · Conf: 0.941)", font=font_small, fill=EMERALD)

        else:
            # Sub-scene B: Steward Approval Queue
            draw_header(draw, active_tab="STEWARD QUEUE")
            draw.text((60, 76), "FEATURE 2: POLICY-AS-CODE & HUMAN STEWARD APPROVAL", font=font_title, fill=TEXT_WHITE)
            draw.text((60, 114), "Autonomous AI proposals gated by Policy-as-Code. Requires steward review before catalog commit.", font=font_subtitle, fill=TEXT_MUTED)

            # Proposal Card
            approved_state = (local_t >= 3.8)
            draw.rectangle([60, 160, WIDTH - 60, 450], fill=BG_CARD, outline=EMERALD if approved_state else AMBER, width=2)

            draw.text((90, 190), "CHANGE PROPOSAL #CF-PROP-9821", font=font_nav, fill=TEXT_MUTED)
            status_text = "STATUS: APPROVED & COMMITTED" if approved_state else "STATUS: PENDING STEWARD REVIEW"
            draw.text((WIDTH - 420, 190), status_text, font=font_nav, fill=EMERALD if approved_state else AMBER)

            draw.text((90, 235), "Target: cforge.public.dim_customers.primary_zip", font=font_small, fill=TEXT_MUTED)
            draw.text((90, 260), "Change Type: ADD_TAG (PII: POSTAL_CODE)", font=font_title, fill=TEXT_WHITE)
            draw.text((90, 310), "Proposed By: Agent_Classifier (Confidence: 0.95)", font=font_subtitle, fill=TEXT_MUTED)
            draw.text((90, 340), "Gating Policy: POL-002: PII classification requires compliance steward human sign-off.", font=font_subtitle, fill=AMBER)

            if not approved_state:
                draw.rectangle([90, 380, 260, 425], fill=(255, 255, 255))
                draw.text((125, 395), "APPROVE [Click]", font=font_nav, fill=(0, 0, 0))
                draw.rectangle([280, 380, 430, 425], fill=BG_CARD_SUBTLE, outline=BORDER_MUTED, width=1)
                draw.text((320, 395), "REJECT", font=font_nav, fill=TEXT_MUTED)
            else:
                draw.rectangle([90, 380, 520, 425], fill=(15, 35, 20), outline=EMERALD, width=1)
                draw.text((110, 395), "[APPROVED] Compliance Steward Alice (Signed)", font=font_nav, fill=EMERALD)

            # Audit ledger
            draw.rectangle([60, 480, WIDTH - 60, 640], fill=BG_CARD_SUBTLE, outline=BORDER_MUTED, width=1)
            draw.text((90, 505), "CRYPTOGRAPHIC AUDIT CHAIN (SHA-256)", font=font_nav, fill=TEXT_MUTED)
            draw.text((90, 540), "Hash: 8f9b4c09d3e8e21a4f00923b... Chained to Genesis Root", font=font_code, fill=TEXT_WHITE)
            draw.text((90, 570), "Timestamp: 2026-10-24T21:40:00Z · Action: CATALOG_COMMIT · Actor: Governance_Steward", font=font_code, fill=TEXT_MUTED)
            draw.text((90, 600), "Ledger Status: 100% Tamper-Proof Cryptographic Verification Complete", font=font_code, fill=EMERALD)

    # =========================================================================
    # SCENE 4: Empirical Benchmark Results (13.0s - 17.0s)
    # =========================================================================
    elif t < 17.0:
        local_t = t - 13.0
        draw_header(draw, active_tab="BENCHMARKS")

        draw.text((60, 76), "EMPIRICAL BENCHMARK PROOF (45 ENTERPRISE QUERIES)", font=font_title, fill=TEXT_WHITE)
        draw.text((60, 114), "Rigorous execution match against DuckDB. Gold SQL never revealed to the model.", font=font_subtitle, fill=TEXT_MUTED)

        # Big Headline Lift Card
        draw.rectangle([60, 150, 480, 640], fill=BG_CARD, outline=EMERALD, width=2)
        draw.text((90, 185), "TEXT-TO-SQL ACCURACY LIFT", font=font_nav, fill=TEXT_MUTED)
        draw.text((90, 230), "+13.34 pts", font=font_hero, fill=EMERALD)
        draw.text((90, 290), "Single run, one model (Gemini Flash)", font=font_small, fill=TEXT_MUTED)

        # Comparison Bar
        draw.text((90, 350), "Governed Context: 86.67% (39/45)", font=font_small, fill=TEXT_WHITE)
        draw.rectangle([90, 375, 90 + int(340 * 0.8667), 395], fill=EMERALD)

        draw.text((90, 425), "Bare Schema Baseline: 73.33% (33/45)", font=font_small, fill=TEXT_MUTED)
        draw.rectangle([90, 450, 90 + int(340 * 0.7333), 470], fill=BORDER_ACTIVE)

        draw.rectangle([90, 520, 450, 600], fill=(16, 25, 20), outline=EMERALD, width=1)
        draw.text((105, 540), "Execution Match Rate:", font=font_small, fill=TEXT_MUTED)
        draw.text((105, 565), "39 of 45 Business Questions Solved", font=font_nav, fill=TEXT_WHITE)

        # Right Grid: The Other Metrics
        benchmarks = [
            ("87.0%", "PII Attacks Blocked", "20 of 23 adversarial prompt injection attacks intercepted"),
            ("94.3%", "PII F1-Score", "96.2% Precision, 92.6% Recall across 94 held-out columns"),
            ("97.4%", "Lineage Accuracy", "38 of 39 hand-verified columns extracted via AST parser"),
            ("$0.1024", "Enrichment Unit Cost", "Per 1,000 API calls — 99% cost reduction vs manual curation"),
        ]

        bw = 320
        bh = 220
        for i, (bval, btitle, bsub) in enumerate(benchmarks):
            col = i % 2
            row = i // 2
            x = 520 + col * (bw + 30)
            y = 150 + row * (bh + 40)

            draw.rectangle([x, y, x + bw, y + bh], fill=BG_CARD, outline=BORDER_MUTED, width=1)
            draw.text((x + 20, y + 24), bval, font=font_card_num, fill=TEXT_WHITE)
            draw.text((x + 20, y + 80), btitle, font=font_nav, fill=TEXT_WHITE)
            draw.text((x + 20, y + 115), bsub, font=font_small, fill=TEXT_MUTED)

    # =========================================================================
    # SCENE 5: Outro & Call to Action (17.0s - 20.0s)
    # =========================================================================
    else:
        local_t = t - 17.0
        # Grand cinematic finale
        # Logo Mark Large
        draw.polygon([(WIDTH // 2 - 40, 160), (WIDTH // 2 + 40, 160), (WIDTH // 2 + 60, 240), (WIDTH // 2 - 60, 240)], fill=(255, 255, 255))
        draw.text((WIDTH // 2 - 190, 270), "CONTEXTFORGE", font=font_hero, fill=TEXT_WHITE)
        draw.text((WIDTH // 2 - 270, 340), "Governed Metadata Enrichment for Enterprise AI Agents", font=font_subtitle, fill=TEXT_MUTED)

        # 3 Key Pills
        draw.rectangle([WIDTH // 2 - 360, 400, WIDTH // 2 - 130, 440], fill=BG_CARD, outline=BORDER_MUTED, width=1)
        draw.text((WIDTH // 2 - 340, 412), "31 Tables Supabase Live", font=font_nav, fill=EMERALD)

        draw.rectangle([WIDTH // 2 - 110, 400, WIDTH // 2 + 110, 440], fill=BG_CARD, outline=BORDER_MUTED, width=1)
        draw.text((WIDTH // 2 - 90, 412), "+13.34 pt Accuracy Lift", font=font_nav, fill=TEXT_WHITE)

        draw.rectangle([WIDTH // 2 + 130, 400, WIDTH // 2 + 360, 440], fill=BG_CARD, outline=BORDER_MUTED, width=1)
        draw.text((WIDTH // 2 + 150, 412), "87% PII Attack Defense", font=font_nav, fill=AMBER)

        # Call to Action Card
        draw.rectangle([WIDTH // 2 - 320, 480, WIDTH // 2 + 320, 580], fill=BG_CARD, outline=EMERALD, width=2)
        draw.text((WIDTH // 2 - 180, 505), "EXPLORE THE LIVE REPOSITORY", font=font_nav, fill=TEXT_MUTED)
        draw.text((WIDTH // 2 - 220, 535), "github.com/Susil-commits/CForge", font=font_title, fill=TEXT_WHITE)

        draw.text((WIDTH // 2 - 140, 620), "Production Ready · Open Source", font=font_small, fill=TEXT_SUBTLE)

    # Convert PIL Image (RGB) to OpenCV format (BGR)
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def generate_video(output_path="docs/contextforge_commercial.mp4"):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_file), fourcc, FPS, (WIDTH, HEIGHT))

    print(f"Rendering {TOTAL_FRAMES} frames ({TOTAL_SECONDS}s commercial ad @ {FPS} FPS)...")
    for f in range(TOTAL_FRAMES):
        if f % 60 == 0:
            print(f"  Frame {f}/{TOTAL_FRAMES} ({(f/TOTAL_FRAMES)*100:.1f}% complete)...")
        bgr_frame = render_frame(f)
        out.write(bgr_frame)

    out.release()
    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"SUCCESS: Commercial ad generated at {output_file} ({size_mb:.2f} MB)")
    return output_file


if __name__ == "__main__":
    generate_video()
