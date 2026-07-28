"""PDF export: the client's meal plan + training program + shopping list.

Engine order: WeasyPrint (full HTML/CSS fidelity — needs pango/cairo system
libs) -> fpdf2 (pure python, no system deps) -> None. Never raises for a
missing engine; callers hide the download button when build returns None.
"""
import html as _html
from datetime import date

import coachlib as cl

INK = (23, 21, 15)
CREAM = (239, 237, 230)
SAND = (232, 228, 219)
ACCENT = (228, 83, 31)
ACCENT2 = (201, 67, 15)
MUTED = (120, 115, 106)
GOOD = (63, 122, 91)


def engine():
    """'weasyprint' | 'fpdf' | None."""
    try:
        import weasyprint  # noqa: F401
        return "weasyprint"
    except Exception:
        pass
    try:
        import fpdf  # noqa: F401
        return "fpdf"
    except Exception:
        return None


def build_plan_pdf(name):
    """Bytes of the client bundle, or None when no engine is available."""
    eng = engine()
    if eng == "weasyprint":
        try:
            return _build_weasy(name)
        except Exception:
            pass   # fall through to fpdf if weasy blows up at runtime
    if eng in ("weasyprint", "fpdf"):
        try:
            return _build_fpdf(name)
        except Exception:
            return None
    return None


def _latin(s):
    """fpdf2 core fonts are latin-1 only — transliterate the house
    typography (em-dashes, arrows, fractions) instead of crashing."""
    repl = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
            "⅛": "1/8", "✓": "", "→": "->", "←": "<-", "✳": "*", "⚡": "",
            "…": "...", "▶": ">"}
    out = str(s)
    for k, v in repl.items():
        out = out.replace(k, v)
    return out.encode("latin-1", "replace").decode("latin-1")


# ---------------- fpdf2 (the guaranteed path) --------------------------------
def _build_fpdf(name):
    from fpdf import FPDF

    grid = cl.plan_grid(name)
    training = cl.get_training(name)
    shopping = cl.shopping_list(name)
    rec = cl.get_client(name) or {}

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    def header_band():
        pdf.set_fill_color(*INK)
        pdf.rect(pdf.l_margin, pdf.get_y(), W, 16, style="F")
        pdf.set_xy(pdf.l_margin + 4, pdf.get_y() + 3)
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(W * 0.6, 10, "TRAIN & EAT", align="L")
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*CREAM)
        pdf.cell(W * 0.4 - 8, 10,
                 _latin(f"{name}  ·  {date.today().isoformat()}"), align="R")
        pdf.ln(16)
        pdf.set_text_color(*INK)

    def section(title):
        pdf.ln(4)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*ACCENT2)
        pdf.cell(0, 5, _latin(f"[ {title.upper()} ]"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)

    def bar(text, right=""):
        pdf.set_fill_color(*INK)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(W * 0.5, 7, _latin(f"  {text}"), fill=True)
        pdf.set_font("helvetica", "", 8)
        pdf.cell(W * 0.5, 7, _latin(f"{right}  "), fill=True, align="R",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)

    def row(cells, widths, bold=False, fill=None, align=None):
        pdf.set_font("helvetica", "B" if bold else "", 8)
        if fill:
            pdf.set_fill_color(*fill)
        for i, (txt, w) in enumerate(zip(cells, widths)):
            a = (align[i] if align else "L")
            pdf.cell(w, 6.5, _latin(str(txt))[:44], border=1,
                     fill=bool(fill), align=a)
        pdf.ln()

    header_band()

    # ---- meal plans ----
    for daytype, day in grid.items():
        section(daytype)
        tgt = day.get("targets") or {}
        if tgt:
            pdf.set_font("helvetica", "", 8)
            pdf.set_text_color(*MUTED)
            pdf.cell(0, 5,
                     _latin(f'Targets: {tgt.get("cal", "-")} cal · '
                     f'P {tgt.get("protein", "-")}g · '
                     f'F {tgt.get("fats", "-")}g · '
                     f'C {tgt.get("carbs", "-")}g'),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*INK)
        widths = [W * x for x in (0.28, 0.12, 0.08, 0.12, 0.1, 0.1, 0.1,
                                  0.1)]
        aligns = ["L", "R", "R", "R", "R", "R", "R", "R"]
        for m in day["meals"]:
            t = m["totals"]
            bar(m["meal"], f'{round(t[0])} cal · P{t[1]:.0f} · '
                           f'F{t[2]:.0f} · C{t[3]:.0f}')
            row(["Food", "Serving", "No.", "Amount", "Cal", "P", "F", "C"],
                widths, bold=True, fill=SAND, align=aligns)
            for x in m["rows"]:
                row([x["food"], x["serving"], f'{x["n"]:g}', x["amount"],
                     round(x["cal"]), f'{x["p"]:.1f}', f'{x["f"]:.1f}',
                     f'{x["c"]:.1f}'], widths, align=aligns)
            row(["Totals", "", "", "", round(t[0]), f"{t[1]:.1f}",
                 f"{t[2]:.1f}", f"{t[3]:.1f}"], widths, bold=True,
                fill=SAND, align=aligns)
            pdf.ln(2)
        d = day["totals"]
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*ACCENT2)
        pdf.cell(0, 6, _latin(f'{daytype} total — {round(d[0])} cal · '
                       f'P {d[1]:.0f} · F {d[2]:.0f} · C {d[3]:.0f}'),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)

    # ---- training ----
    if cl.has_program(name):
        section(f'Training — Block {training["block"]}, '
                f'Week {training["week"]} of {training["weeks_total"]}')
        tw = [W * x for x in (0.3, 0.12, 0.16, 0.08, 0.34)]
        ta = ["L", "R", "R", "R", "L"]
        for dday in training["days"]:
            if not dday["exercises"]:
                continue
            bar(dday["name"], f'{len(dday["exercises"])} exercises')
            row(["Exercise", "Sets", "Reps", "RIR", "Cue"], tw, bold=True,
                fill=SAND, align=ta)
            for e in dday["exercises"]:
                row([e["exercise"], e["sets"], e["reps"], e["rir"],
                     e["cue"]], tw, align=ta)
            pdf.ln(2)

    # ---- shopping list ----
    if shopping:
        section("Shopping list — one training + one rest day; "
                "scale to your week")
        for cat, items in shopping.items():
            pdf.set_font("helvetica", "B", 8.5)
            pdf.set_text_color(*ACCENT2)
            pdf.cell(0, 6, _latin(cl.CAT_LABEL.get(cat, cat) if
                     hasattr(cl, "CAT_LABEL") else cat),
                     new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*INK)
            pdf.set_font("helvetica", "", 9)
            for it in items:
                y = pdf.get_y()
                pdf.rect(pdf.l_margin + 1, y + 1.2, 3.2, 3.2)
                pdf.set_x(pdf.l_margin + 7)
                pdf.cell(W * 0.6, 6, _latin(it["food"])[:60])
                pdf.cell(W * 0.3, 6, _latin(it["label"]), align="R",
                         new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

    out = pdf.output()
    return bytes(out)


# ---------------- WeasyPrint (design-faithful when libs exist) ----------------
def _build_weasy(name):
    from weasyprint import HTML

    grid = cl.plan_grid(name)
    training = cl.get_training(name)
    shopping = cl.shopping_list(name)

    def e(x):
        return _html.escape(str(x))

    css = """
    @page{size:A4;margin:16mm 14mm}
    body{font-family:Helvetica,Arial,sans-serif;color:#17150F;font-size:9.5px}
    h1{font-size:16px;letter-spacing:-.02em;margin:0 0 2px}
    .kick{color:#C9430F;font-size:8px;letter-spacing:.16em;
      text-transform:uppercase;font-weight:700;margin:14px 0 6px}
    .bar{background:#17150F;color:#fff;padding:5px 8px;font-weight:700;
      font-size:9px;letter-spacing:.08em;text-transform:uppercase}
    .bar span{float:right;font-weight:400;color:#cfc9bf}
    table{width:100%;border-collapse:collapse;margin-bottom:8px}
    th,td{border:1px solid #CDC6B8;padding:4px 6px;text-align:right}
    th{background:#E8E4DB;font-size:7.5px;text-transform:uppercase;
      letter-spacing:.06em}
    th.l,td.l{text-align:left}
    tr.tot td{background:#E8E4DB;font-weight:700}
    .muted{color:#78736A}
    .cat{color:#C9430F;font-weight:700;text-transform:uppercase;
      font-size:8px;letter-spacing:.08em;margin:6px 0 2px}
    .item{padding:2px 0;border-bottom:0.5px solid #E4E0D6}
    .box{display:inline-block;width:8px;height:8px;
      border:1px solid #17150F;margin-right:6px}
    """
    parts = [f"<h1>TRAIN &amp; EAT — {e(name)}</h1>",
             f'<div class="muted">{date.today().isoformat()}</div>']
    for daytype, day in grid.items():
        parts.append(f'<div class="kick">[ {e(daytype)} ]</div>')
        for m in day["meals"]:
            t = m["totals"]
            parts.append(
                f'<div class="bar">{e(m["meal"])}<span>{round(t[0])} cal · '
                f'P{t[1]:.0f} · F{t[2]:.0f} · C{t[3]:.0f}</span></div>')
            trs = "".join(
                f'<tr><td class="l">{e(x["food"])}</td>'
                f'<td>{e(x["serving"])}</td><td>{x["n"]:g}</td>'
                f'<td>{e(x["amount"])}</td><td>{round(x["cal"])}</td>'
                f'<td>{x["p"]:.1f}</td><td>{x["f"]:.1f}</td>'
                f'<td>{x["c"]:.1f}</td></tr>' for x in m["rows"])
            parts.append(
                '<table><tr><th class="l">Food</th><th>Serving</th>'
                '<th>No.</th><th>Amount</th><th>Cal</th><th>P</th>'
                f'<th>F</th><th>C</th></tr>{trs}'
                f'<tr class="tot"><td class="l">Totals</td><td></td>'
                f'<td></td><td></td><td>{round(t[0])}</td>'
                f'<td>{t[1]:.1f}</td><td>{t[2]:.1f}</td>'
                f'<td>{t[3]:.1f}</td></tr></table>')
    if cl.has_program(name):
        parts.append(f'<div class="kick">[ Training — Block '
                     f'{training["block"]}, Week {training["week"]} of '
                     f'{training["weeks_total"]} ]</div>')
        for dday in training["days"]:
            if not dday["exercises"]:
                continue
            parts.append(f'<div class="bar">{e(dday["name"])}</div>')
            trs = "".join(
                f'<tr><td class="l">{e(x["exercise"])}</td>'
                f'<td>{e(x["sets"])}</td><td>{e(x["reps"])}</td>'
                f'<td>{e(x["rir"])}</td><td class="l">{e(x["cue"])}</td>'
                '</tr>' for x in dday["exercises"])
            parts.append('<table><tr><th class="l">Exercise</th>'
                         '<th>Sets</th><th>Reps</th><th>RIR</th>'
                         f'<th class="l">Cue</th></tr>{trs}</table>')
    if shopping:
        parts.append('<div class="kick">[ Shopping list — one training + '
                     'one rest day; scale to your week ]</div>')
        for cat, items in shopping.items():
            parts.append(f'<div class="cat">{e(cat)}</div>')
            for it in items:
                parts.append(f'<div class="item"><span class="box"></span>'
                             f'{e(it["food"])} — {e(it["label"])}</div>')
    html_doc = f"<html><head><style>{css}</style></head><body>" \
               + "".join(parts) + "</body></html>"
    return HTML(string=html_doc).write_pdf()
