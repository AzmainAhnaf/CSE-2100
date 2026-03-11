import customtkinter as ctk
import threading
import math
import time
import json
from datetime import datetime
from tkinter import font as tkfont, filedialog, messagebox
import tkinter as tk
from backend import analyze_handle

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG          = "#0d0f14"
PANEL       = "#13161e"
BORDER      = "#1e2330"
ACCENT      = "#4f8ef7"
ACCENT2     = "#7c5cfc"
GREEN       = "#2ecc71"
GREEN_DIM   = "#1a3d2b"
YELLOW      = "#f0c040"
YELLOW_DIM  = "#3a3010"
RED         = "#e74c3c"
RED_DIM     = "#3d1a1a"
GREY_DIM    = "#1e2330"
TEXT        = "#e8eaf0"
SUBTEXT     = "#6b7591"
WHITE       = "#ffffff"

RANK_COLORS = {
    "legendary grandmaster": "#ff0000",
    "international grandmaster": "#ff3300",
    "grandmaster": "#ff3300",
    "international master": "#ffaa00",
    "master": "#ffaa00",
    "candidate master": "#aa00aa",
    "expert": "#0000ff",
    "specialist": "#03a89e",
    "pupil": "#008000",
    "newbie": "#808080",
}

def rank_color(rank):
    return RANK_COLORS.get(rank.lower(), ACCENT)

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_frame(parent, **kwargs):
    defaults = dict(fg_color=PANEL, corner_radius=12, border_width=1, border_color=BORDER)
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)

def label(parent, text, size=13, weight="normal", color=TEXT, **kwargs):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont(family="Courier New", size=size, weight=weight),
                        text_color=color, **kwargs)

# ── Canvas donut chart ─────────────────────────────────────────────────────────

class DonutChart(tk.Canvas):
    def __init__(self, parent, values, colors, labels, size=140, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=PANEL, highlightthickness=0, **kwargs)
        self.size = size
        self.values = values
        self.colors = colors
        self.labels = labels
        self._draw()

    def _draw(self):
        s = self.size
        pad = 10
        total = sum(self.values) or 1
        start = -90
        cx, cy, r, ri = s/2, s/2, s/2 - pad, s/2 - pad - 22

        for val, col in zip(self.values, self.colors):
            extent = (val / total) * 360
            if extent > 0:
                self.create_arc(pad, pad, s-pad, s-pad,
                                start=start, extent=extent,
                                fill=col, outline=PANEL, width=2, style=tk.PIESLICE)
                start += extent

        # hollow center
        self.create_oval(cx-ri, cy-ri, cx+ri, cy+ri, fill=PANEL, outline=PANEL)
        self.create_text(cx, cy-8, text=str(sum(self.values)),
                         fill=WHITE, font=("Courier New", 16, "bold"))
        self.create_text(cx, cy+10, text="problems",
                         fill=SUBTEXT, font=("Courier New", 9))

# ── Mini horizontal bar ────────────────────────────────────────────────────────

class MiniBar(tk.Canvas):
    def __init__(self, parent, ratio, color, width=180, height=6, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=PANEL, highlightthickness=0, **kwargs)
        self.create_rectangle(0, 0, width, height, fill=BORDER, outline="")
        filled = int(ratio * width)
        if filled > 0:
            self.create_rectangle(0, 0, filled, height, fill=color, outline="")

# ── Zone pill ──────────────────────────────────────────────────────────────────

def zone_pill(parent, text, zone):
    cfg = {
        "strong": (GREEN, GREEN_DIM),
        "mid":    (YELLOW, YELLOW_DIM),
        "weak":   (RED, RED_DIM),
    }
    fg, bg = cfg.get(zone, (SUBTEXT, GREY_DIM))
    f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
    ctk.CTkLabel(f, text=text,
                 font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
                 text_color=fg).pack(padx=10, pady=3)
    return f

# ── Loading overlay ────────────────────────────────────────────────────────────

class LoadingOverlay(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._angle = 0
        self._running = False

        self.canvas = tk.Canvas(self, width=80, height=80,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(pady=(120, 16))

        self.status_var = tk.StringVar(value="Initializing...")
        ctk.CTkLabel(self, textvariable=self.status_var,
                     font=ctk.CTkFont(family="Courier New", size=13),
                     text_color=SUBTEXT).pack()

        self.bar_var = tk.DoubleVar(value=0)
        self.bar = ctk.CTkProgressBar(self, variable=self.bar_var,
                                      width=280, height=4,
                                      fg_color=BORDER, progress_color=ACCENT)
        self.bar.pack(pady=(18, 0))

    def start(self):
        self._running = True
        self._spin()

    def stop(self):
        self._running = False

    def update_progress(self, val, msg):
        self.bar_var.set(val)
        self.status_var.set(msg)

    def _spin(self):
        if not self._running:
            return
        c = self.canvas
        c.delete("all")
        cx, cy, r = 40, 40, 28
        # background ring
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=0, extent=359,
                     outline=BORDER, width=5, style=tk.ARC)
        # spinning arc
        a = self._angle
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=a, extent=260,
                     outline=ACCENT, width=5, style=tk.ARC)
        self._angle = (self._angle + 8) % 360
        self.after(30, self._spin)

# ── Main App ───────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CF Analyzer")
        self.geometry("980x720")
        self.minsize(860, 640)
        self.configure(fg_color=BG)
        self._last_result = None
        self._build_ui()

    # ── Layout skeleton ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header bar ──
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=56,
                              border_width=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="⚡ CF ANALYZER",
                     font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
                     text_color=ACCENT).pack(side="left", padx=24, pady=12)

        # Exit button — always visible, far right of title area
        ctk.CTkButton(
            header, text="✕ Exit", width=80, height=36,
            corner_radius=8, fg_color=RED_DIM, hover_color="#5a1f1f",
            border_width=1, border_color=RED,
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            text_color=RED, command=self.destroy).pack(side="left", padx=(0, 8), pady=10)

        # Home button — only shown on results page
        self.home_btn = ctk.CTkButton(
            header, text="⌂ Home", width=80, height=36,
            corner_radius=8, fg_color=GREY_DIM, hover_color="#1e3a5f",
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(family="Courier New", size=12),
            text_color=SUBTEXT, command=self._go_home, state="disabled")
        self.home_btn.pack(side="left", pady=10)

        # search row inside header
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="right", padx=16, pady=8)

        self.handle_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Enter Codeforces handle...",
            width=260, height=36, corner_radius=8,
            fg_color="#0d0f14", border_color=BORDER, text_color=TEXT,
            font=ctk.CTkFont(family="Courier New", size=13))
        self.handle_entry.pack(side="left", padx=(0, 10))
        self.handle_entry.bind("<Return>", lambda e: self._start_analysis())

        self.analyze_btn = ctk.CTkButton(
            search_frame, text="Analyze →", width=110, height=36,
            corner_radius=8, fg_color=ACCENT, hover_color=ACCENT2,
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            command=self._start_analysis)
        self.analyze_btn.pack(side="left")

        # import/export buttons
        io_frame = ctk.CTkFrame(header, fg_color="transparent")
        io_frame.pack(side="right", padx=(0, 8), pady=8)

        self.import_btn = ctk.CTkButton(
            io_frame, text="⬆ Import", width=90, height=36,
            corner_radius=8, fg_color=GREY_DIM, hover_color="#0f3d3d",
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(family="Courier New", size=12),
            text_color=TEXT, command=self._import_json)
        self.import_btn.pack(side="left", padx=(0, 6))

        self.export_btn = ctk.CTkButton(
            io_frame, text="⬇ Export", width=90, height=36,
            corner_radius=8, fg_color=GREY_DIM, hover_color="#1a3d2b",
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(family="Courier New", size=12),
            text_color=SUBTEXT, command=self._export_json, state="disabled")
        self.export_btn.pack(side="left")

        # ── Main content area ──
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20, pady=16)

        self._show_welcome()

    # ── Welcome screen ─────────────────────────────────────────────────────────

    def _show_welcome(self):
        self._clear_content()
        f = ctk.CTkFrame(self.content, fg_color="transparent")
        f.place(relx=0.5, rely=0.45, anchor="center")

        label(f, "◈", size=52, color=ACCENT).pack()
        label(f, "Competitive Programming\nPerformance Analyzer",
              size=20, weight="bold", color=TEXT).pack(pady=(8, 6))
        label(f, "Enter your Codeforces handle above to discover your\nstrong zones, weak spots, and trending topics.",
              size=12, color=SUBTEXT).pack()

    # ── Analysis trigger ───────────────────────────────────────────────────────

    def _start_analysis(self):
        handle = self.handle_entry.get().strip()
        if not handle:
            return
        self.analyze_btn.configure(state="disabled")
        self._clear_content()

        self.overlay = LoadingOverlay(self.content)
        self.overlay.start()

        thread = threading.Thread(target=self._run_analysis, args=(handle,), daemon=True)
        thread.start()

    def _run_analysis(self, handle):
        try:
            result = analyze_handle(handle, progress_callback=self._on_progress)
            self.after(0, self._show_results, result)
        except Exception as e:
            self.after(0, self._show_error, str(e))

    def _on_progress(self, step, msg):
        self.after(0, lambda: self.overlay.update_progress(step, msg))

    # ── Results screen ─────────────────────────────────────────────────────────

    def _show_results(self, r):
        if hasattr(self, "overlay"):
            self.overlay.stop()
        self._clear_content()
        self.analyze_btn.configure(state="normal")
        self._last_result = r
        self.export_btn.configure(state="normal", text_color=TEXT)
        self.home_btn.configure(state="normal", text_color=TEXT)

        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent",
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=ACCENT)
        scroll.pack(fill="both", expand=True)

        # ── User card row ──
        self._build_user_card(scroll, r)

        # ── Middle: zones + donut ──
        mid_row = ctk.CTkFrame(scroll, fg_color="transparent")
        mid_row.pack(fill="x", pady=(12, 0))
        mid_row.columnconfigure(0, weight=3)
        mid_row.columnconfigure(1, weight=2)

        self._build_zones_panel(mid_row, r)
        self._build_donut_panel(mid_row, r)

        # ── Tag frequency ──
        self._build_tag_panel(scroll, r)

        # ── Focus recommendations ──
        self._build_focus_panel(scroll, r)

        # ── Submission breakdown ──
        self._build_submission_table(scroll, r)

    def _build_user_card(self, parent, r):
        card = make_frame(parent)
        card.pack(fill="x", pady=(0, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        # avatar placeholder
        av = tk.Canvas(inner, width=56, height=56, bg=ACCENT2,
                       highlightthickness=0)
        av.pack(side="left", padx=(0, 16))
        initials = r["handle"][:2].upper()
        av.create_text(28, 28, text=initials, fill=WHITE,
                       font=("Courier New", 20, "bold"))
        av.create_oval(0, 0, 56, 56, outline=ACCENT, width=2)

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left")
        rc = rank_color(r["rank"])
        label(info, r["handle"], size=20, weight="bold", color=WHITE).pack(anchor="w")
        label(info, r["rank"].title(), size=12, color=rc).pack(anchor="w")

        stats = ctk.CTkFrame(inner, fg_color="transparent")
        stats.pack(side="right")

        for title, val, col in [
            ("Current Rating", str(r["rating"]), ACCENT),
            ("Max Rating",     str(r["max_rating"]), ACCENT2),
        ]:
            sf = ctk.CTkFrame(stats, fg_color=GREY_DIM, corner_radius=10)
            sf.pack(side="left", padx=6)
            label(sf, val, size=22, weight="bold", color=col).pack(padx=16, pady=(8, 2))
            label(sf, title, size=10, color=SUBTEXT).pack(padx=16, pady=(0, 8))

    def _build_zones_panel(self, parent, r):
        card = make_frame(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        label(card, "ZONE ANALYSIS", size=11, color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 8))

        for zone_name, items, color, dim in [
            ("Strong Zone", r["strong"], GREEN, GREEN_DIM),
            ("Mid Zone",    r["mid"],    YELLOW, YELLOW_DIM),
            ("Weak Zone",   r["weak"],   RED,   RED_DIM),
        ]:
            section = ctk.CTkFrame(card, fg_color="transparent")
            section.pack(fill="x", padx=16, pady=(0, 10))

            row = ctk.CTkFrame(section, fg_color="transparent")
            row.pack(fill="x")
            label(row, zone_name, size=12, weight="bold", color=color).pack(side="left")
            label(row, f"({len(items)} topics)", size=10, color=SUBTEXT).pack(side="left", padx=6)

            pill_row = ctk.CTkFrame(section, fg_color="transparent")
            pill_row.pack(fill="x", pady=(4, 0))

            if items:
                for i, tag in enumerate(items[:8]):
                    zone_key = "strong" if color == GREEN else ("mid" if color == YELLOW else "weak")
                    p = zone_pill(pill_row, tag, zone_key)
                    p.grid(row=i//4, column=i%4, padx=3, pady=3, sticky="w")
            else:
                label(pill_row, "None detected", size=11, color=SUBTEXT).pack(anchor="w")

        pad_bottom = ctk.CTkFrame(card, fg_color="transparent", height=8)
        pad_bottom.pack()

    def _build_donut_panel(self, parent, r):
        card = make_frame(parent)
        card.grid(row=0, column=1, sticky="nsew")

        label(card, "SUBMISSION OVERVIEW", size=11, color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 8))

        total_good = sum(r["good"].values())
        total_bad  = sum(r["bad"].values())
        total_all  = total_good + total_bad

        chart_frame = ctk.CTkFrame(card, fg_color="transparent")
        chart_frame.pack(pady=8)

        DonutChart(chart_frame,
                   values=[total_good, total_bad],
                   colors=[GREEN, RED],
                   labels=["Accepted", "Wrong"],
                   size=140).pack()

        legend = ctk.CTkFrame(card, fg_color="transparent")
        legend.pack(pady=(4, 16))
        for lbl, val, col in [("Accepted", total_good, GREEN), ("Wrong", total_bad, RED)]:
            row = ctk.CTkFrame(legend, fg_color="transparent")
            row.pack(anchor="w", padx=24, pady=2)
            dot = tk.Canvas(row, width=10, height=10, bg=PANEL, highlightthickness=0)
            dot.pack(side="left", padx=(0, 6))
            dot.create_oval(1, 1, 9, 9, fill=col, outline="")
            pct = f"{val/total_all*100:.0f}%" if total_all else "—"
            label(row, f"{lbl}  {val}  ({pct})", size=11, color=TEXT).pack(side="left")

    def _build_tag_panel(self, parent, r):
        card = make_frame(parent)
        card.pack(fill="x", pady=(12, 0))

        label(card, "TRENDING TOPICS  (among similar-rated users)", size=11, color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 8))

        tags = list(r["tagcount"].items())[:12]
        if not tags:
            label(card, "No data available", size=12, color=SUBTEXT).pack(padx=16, pady=8)
            return

        max_count = tags[0][1] if tags else 1
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 14))

        for i, (tag, count) in enumerate(tags):
            row_f = ctk.CTkFrame(grid, fg_color="transparent")
            row_f.grid(row=i//2, column=i%2, sticky="ew", padx=(0, 20), pady=3)
            grid.columnconfigure(i%2, weight=1)

            label(row_f, tag, size=11, color=TEXT).pack(anchor="w")
            bar_row = ctk.CTkFrame(row_f, fg_color="transparent")
            bar_row.pack(anchor="w", fill="x")
            MiniBar(bar_row, count/max_count, ACCENT, width=200).pack(side="left", pady=2)
            label(bar_row, f"  {count}", size=10, color=SUBTEXT).pack(side="left")

    def _build_focus_panel(self, parent, r):
        # Top 5 trending tags
        top5 = [tag for tag, _ in list(r["tagcount"].items())[:5]]

        # Priority 1: weak topics in top 5
        focus_topics = [(tag, "weak") for tag in r["weak"] if tag in top5]

        # Priority 2: mid topics in top 5 (only if no weak found)
        if not focus_topics:
            focus_topics = [(tag, "mid") for tag in r["mid"] if tag in top5]

        card = make_frame(parent)
        card.pack(fill="x", pady=(12, 0))

        # Header row
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(14, 4))
        label(header_row, "FOCUS RECOMMENDATIONS", size=11, color=SUBTEXT).pack(side="left")

        if not focus_topics:
            # No recommendations
            empty = ctk.CTkFrame(card, fg_color=GREY_DIM, corner_radius=8)
            empty.pack(fill="x", padx=16, pady=(4, 14))
            label(empty, "✓  No urgent focus areas — your trending topics are well covered!",
                  size=12, color=GREEN).pack(padx=16, pady=12)
            return

        zone_used = focus_topics[0][1]
        source_label = "weak zone" if zone_used == "weak" else "mid zone"
        label(header_row,
              f"  ·  top-5 trending ∩ {source_label}",
              size=10, color=SUBTEXT).pack(side="left")

        # Rank of each tag in trending list (for display)
        trending_rank = {tag: i+1 for i, (tag, _) in enumerate(r["tagcount"].items())}

        for i, (tag, zone) in enumerate(focus_topics):
            good  = r["good"].get(tag, 0)
            bad   = r["bad"].get(tag, 0)
            total = r["total"].get(tag, 0)
            pct   = good / total * 100 if total else 0
            rank  = trending_rank.get(tag, "?")

            zone_color = RED if zone == "weak" else YELLOW
            zone_dim   = RED_DIM if zone == "weak" else YELLOW_DIM
            zone_text  = "Weak Zone" if zone == "weak" else "Mid Zone"

            row_bg = PANEL if i % 2 == 0 else "#161921"
            row_f = ctk.CTkFrame(card, fg_color=row_bg, corner_radius=8 if i == 0 else 0)
            row_f.pack(fill="x", padx=16, pady=(0, 2))

            # Trending rank badge
            rank_badge = ctk.CTkFrame(row_f, fg_color=ACCENT2, corner_radius=6, width=28, height=28)
            rank_badge.pack(side="left", padx=(10, 10), pady=10)
            rank_badge.pack_propagate(False)
            label(rank_badge, f"#{rank}", size=10, weight="bold", color=WHITE).place(relx=0.5, rely=0.5, anchor="center")

            # Topic name
            label(row_f, tag, size=13, weight="bold", color=TEXT).pack(side="left", padx=(0, 12))

            # Zone pill
            pill = ctk.CTkFrame(row_f, fg_color=zone_dim, corner_radius=6)
            pill.pack(side="left", padx=(0, 14))
            label(pill, zone_text, size=10, weight="bold", color=zone_color).pack(padx=8, pady=3)

            # Stats
            stats_frame = ctk.CTkFrame(row_f, fg_color="transparent")
            stats_frame.pack(side="right", padx=14)
            label(stats_frame,
                  f"✓ {good}  ✗ {bad}  ({pct:.0f}% acc)",
                  size=11, color=SUBTEXT).pack()

            # Mini progress bar
            bar_frame = ctk.CTkFrame(row_f, fg_color="transparent")
            bar_frame.pack(side="right", padx=(0, 8))
            MiniBar(bar_frame, pct / 100, zone_color, width=100).pack(pady=2)

        pad = ctk.CTkFrame(card, fg_color="transparent", height=12)
        pad.pack()

    def _build_submission_table(self, parent, r):
        card = make_frame(parent)
        card.pack(fill="x", pady=(12, 0))

        label(card, "TOPIC BREAKDOWN  (classified topics only)", size=11, color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 4))

        # header
        hdr = ctk.CTkFrame(card, fg_color=GREY_DIM, corner_radius=6)
        hdr.pack(fill="x", padx=16, pady=(0, 4))

        for col, w in [("Topic", 200), ("Zone", 80), ("Total", 70), ("Accepted", 90), ("Wrong", 70), ("Acc%", 70)]:
            label(hdr, col, size=11, weight="bold", color=SUBTEXT,
                  width=w, anchor="w").pack(side="left", padx=8, pady=6)

        classified = set(r["strong"] + r["mid"] + r["weak"])
        rows = sorted(
            [(tag, cnt) for tag, cnt in r["total"].items() if tag in classified],
            key=lambda x: x[1], reverse=True
        )
        for i, (tag, total) in enumerate(rows):
            good = r["good"].get(tag, 0)
            bad  = r["bad"].get(tag, 0)
            pct  = good / total * 100 if total else 0
            pct_color = GREEN if pct >= 75 else (YELLOW if pct >= 40 else RED)

            if tag in r["strong"]:
                zone_label, zone_color = "Strong", GREEN
            elif tag in r["mid"]:
                zone_label, zone_color = "Mid", YELLOW
            else:
                zone_label, zone_color = "Weak", RED

            row_bg = PANEL if i % 2 == 0 else "#161921"
            row_f = ctk.CTkFrame(card, fg_color=row_bg, corner_radius=0)
            row_f.pack(fill="x", padx=16)

            for val, w, color in [
                (tag,           200, TEXT),
                (zone_label,     80, zone_color),
                (str(total),     70, TEXT),
                (str(good),      90, GREEN),
                (str(bad),       70, RED),
                (f"{pct:.0f}%",  70, pct_color),
            ]:
                label(row_f, val, size=11, color=color,
                      width=w, anchor="w").pack(side="left", padx=8, pady=5)

        pad = ctk.CTkFrame(card, fg_color="transparent", height=12)
        pad.pack()

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _go_home(self):
        self._clear_content()
        self.home_btn.configure(state="disabled", text_color=SUBTEXT)
        self.export_btn.configure(state="disabled", text_color=SUBTEXT)
        self._show_welcome()

    # ── Export / Import ────────────────────────────────────────────────────────

    def _export_json(self):
        if not self._last_result:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"cf_{self._last_result['handle']}_{timestamp}.json"
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_name,
            title="Export analysis data"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._last_result, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exported", f"Data saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def _import_json(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import analysis data"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validate required keys
            required = {"handle", "name", "rating", "rank", "max_rating",
                        "tagcount", "total", "good", "bad", "strong", "mid", "weak", "nd"}
            missing = required - set(data.keys())
            if missing:
                messagebox.showerror("Invalid file",
                    f"This JSON is missing required fields:\n{', '.join(sorted(missing))}")
                return
            self.handle_entry.delete(0, "end")
            self.handle_entry.insert(0, data["handle"])
            self._show_results(data)
        except json.JSONDecodeError:
            messagebox.showerror("Invalid file", "The selected file is not valid JSON.")
        except Exception as e:
            messagebox.showerror("Import failed", str(e))

    # ── Error screen ───────────────────────────────────────────────────────────

    def _show_error(self, msg):
        self.overlay.stop()
        self._clear_content()
        self.analyze_btn.configure(state="normal")

        f = ctk.CTkFrame(self.content, fg_color="transparent")
        f.place(relx=0.5, rely=0.4, anchor="center")
        label(f, "✕", size=40, color=RED).pack()
        label(f, "Something went wrong", size=16, weight="bold", color=TEXT).pack(pady=(6, 4))
        label(f, msg, size=12, color=SUBTEXT).pack()

    # ── Utils ──────────────────────────────────────────────────────────────────

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()