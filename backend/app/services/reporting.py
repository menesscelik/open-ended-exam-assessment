from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_fonts():
    """Registers a font that supports Turkish characters (Arial on Windows)."""
    font_name = "Helvetica"  # fallback
    try:
        font_path = r"C:\Windows\Fonts\arial.ttf"
        bold_path = r"C:\Windows\Fonts\arialbd.ttf"
        if os.path.exists(font_path) and os.path.exists(bold_path):
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            pdfmetrics.registerFont(TTFont("Arial-Bold", bold_path))
            font_name = "Arial"
            logger.info("Successfully registered Arial font.")
        else:
            logger.warning("Arial font not found. Using Helvetica (TR chars may be limited).")
    except Exception as e:
        logger.warning(f"Could not register custom font: {e}")
    return font_name


def generate_exam_report_pdf(student_data, results, output_path, question_weights=None):
    """
    FINAL MANTIK (RUBRIK UYUMLU):
    - final_puan: INTERNAL puan (0-100) => modelin soru bazli basarisi
    - max_puan: Rubrikteki o sorunun sinavdaki agirligi / maksimum puani (Orn: 30, 70)
    - Katki puani = (final_puan / 100) * max_puan
    - Toplam = sum(katki puani)
    - Toplam max = sum(max_puan)

    Args:
        student_data (dict): {'name': 'Name Surname', 'number': '12345'}
        results (list[dict|object]): each item has:
            - soru_no
            - soru_metni
            - ogrenci_cevabi
            - final_puan (INTERNAL 0-100)
            - yorum
            - max_puan (rubrik agirligi; optional)
        output_path (str): save path
        question_weights (dict[int,float]|None): e.g. {1: 30, 2: 70}
            result'larda max_puan yoksa buradan alinacak.
    """

    font_name = register_fonts()
    bold_font_name = "Arial-Bold" if font_name == "Arial" else "Helvetica-Bold"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontName=bold_font_name,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=24,
        textColor=colors.darkblue
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=12
    )

    h3_style = ParagraphStyle(
        "CustomH3",
        parent=styles["Heading3"],
        fontName=bold_font_name,
        fontSize=12,
        textColor=colors.darkblue,
        spaceBefore=12,
        spaceAfter=6
    )

    # 1) Title
    story.append(Paragraph("Sınav Değerlendirme Raporu", title_style))

    # 2) Student info
    info_data = [
        ["Öğrenci Adı Soyadı:", student_data.get("name", "Bilinmiyor")],
        ["Öğrenci Numarası:", student_data.get("number", "Bilinmiyor")],
        ["Değerlendirme Tarihi:", "Otomatik Sistem"]
    ]
    t_info = Table(info_data, colWidths=[5 * cm, 10 * cm])
    t_info.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTNAME", (0, 0), (0, -1), bold_font_name),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 16))

    # -----------------------------------
    # RUBRIC MAX PUAN (WEIGHT) RESOLUTION
    # -----------------------------------
    # Öncelik:
    # 1) results içindeki max_puan
    # 2) question_weights parametresi
    # 3) eşit böl (toplam 100 olacak şekilde)
    resolved_max = {}  # soru_no -> max_puan (rubrik agirligi)

    # 1) results'tan max_puan çek (varsa)
    for idx, r in enumerate(results):
        if isinstance(r, dict):
            soru_no = int(r.get("soru_no", idx + 1))
            mp = r.get("max_puan", None)
        else:
            soru_no = int(getattr(r, "soru_no", idx + 1))
            mp = getattr(r, "max_puan", None)

        if mp is not None:
            try:
                resolved_max[soru_no] = float(mp)
            except Exception:
                pass

    # 2) param weight'lerden tamamla (eğer eksik soru varsa)
    if question_weights:
        for k, v in question_weights.items():
            k = int(k)
            if k not in resolved_max:
                resolved_max[k] = float(v)

    # 3) hala boşsa veya bazı sorular yoksa => eşit böl
    if not resolved_max:
        n = max(len(results), 1)
        eq = 100.0 / n
        for idx, r in enumerate(results):
            soru_no = int(r.get("soru_no", idx + 1)) if isinstance(r, dict) else int(getattr(r, "soru_no", idx + 1))
            resolved_max[soru_no] = eq
    else:
        # bazı sorularda max yoksa eşit dağıtıp tamamla
        missing = []
        for idx, r in enumerate(results):
            soru_no = int(r.get("soru_no", idx + 1)) if isinstance(r, dict) else int(getattr(r, "soru_no", idx + 1))
            if soru_no not in resolved_max:
                missing.append(soru_no)

        if missing:
            # kalan ağırlığı eksiklere eşit böl
            current_sum = sum(resolved_max.values())
            remaining = max(0.0, 100.0 - current_sum)
            eq = remaining / len(missing) if len(missing) else 0.0
            for s in missing:
                resolved_max[s] = eq

    # safety: toplamı 100'e normalize et (rubrik 100 değilse de tutarlı olur)
    max_sum = sum(resolved_max.values())
    if max_sum <= 0:
        max_sum = 100.0
    for k in list(resolved_max.keys()):
        resolved_max[k] = (resolved_max[k] / max_sum) * 100.0

    # -----------------------------------
    # TOTAL SCORE: internal(0-100) -> rubric points
    # -----------------------------------
    total_score = 0.0
    total_max_score = 0.0
    per_q = []  # (soru_no, internal, max_puan, katki)

    for idx, r in enumerate(results):
        if isinstance(r, dict):
            soru_no = int(r.get("soru_no", idx + 1))
            internal = float(r.get("final_puan", 0) or 0)  # 0-100
        else:
            soru_no = int(getattr(r, "soru_no", idx + 1))
            internal = float(getattr(r, "final_puan", 0) or 0)

        # clamp internal
        internal = max(0.0, min(100.0, internal))

        max_puan = float(resolved_max.get(soru_no, 0.0))  # rubrik agirligi (0-100 toplam)
        katki = (internal / 100.0) * max_puan

        total_score += katki
        total_max_score += max_puan

        per_q.append((soru_no, internal, max_puan, katki))

    if total_max_score <= 0:
        total_max_score = 100.0

    pct = (total_score / total_max_score) * 100.0

    summary_style = ParagraphStyle("Summary", parent=normal_style, fontSize=13, spaceAfter=14)
    summary_text = f"<b>Toplam Puan:</b> {total_score:.1f} / {total_max_score:.1f} (%{pct:.1f})"
    story.append(Paragraph(summary_text, summary_style))

    # Breakdown Table
    breakdown_rows = [["Soru", "Ic Puan (0-100)", "Rubrik Agirligi (Max)", "Puan Katkisi"]]
    for (soru_no, internal, max_puan, katki) in per_q:
        breakdown_rows.append([
            str(soru_no),
            f"{internal:.1f}",
            f"{max_puan:.1f}",
            f"{katki:.1f}"
        ])

    t_break = Table(breakdown_rows, colWidths=[2 * cm, 4.5 * cm, 5.0 * cm, 4.0 * cm])
    t_break.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTNAME", (0, 0), (-1, 0), bold_font_name),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_break)
    story.append(Spacer(1, 14))

    # 3) Detailed section title
    story.append(Paragraph("Detaylı Soru Analizi", ParagraphStyle(
        "SubTitle", parent=title_style, fontSize=18, alignment=TA_LEFT, spaceAfter=8
    )))
    story.append(Spacer(1, 6))

    # Build details with corrected per-question display
    per_q_map = {q[0]: q for q in per_q}  # soru_no -> tuple

    for idx, res in enumerate(results):
        if isinstance(res, dict):
            soru_no = int(res.get("soru_no", idx + 1))
            soru_metni = res.get("soru_metni", "")
            ogrenci_cevabi = res.get("ogrenci_cevabi", "")
            yorum = res.get("yorum", "")
        else:
            soru_no = int(getattr(res, "soru_no", idx + 1))
            soru_metni = getattr(res, "soru_metni", "")
            ogrenci_cevabi = getattr(res, "ogrenci_cevabi", "")
            yorum = getattr(res, "yorum", "")

        _, internal, max_puan, katki = per_q_map.get(soru_no, (soru_no, 0.0, 0.0, 0.0))

        q_header = f"Soru {soru_no} (Ic Puan: {internal:.1f}/100 | Rubrik Max: {max_puan:.1f} | Katki: {katki:.1f}/{max_puan:.1f})"
        story.append(Paragraph(q_header, h3_style))

        row_data = [
            [Paragraph("<b>Soru:</b>", normal_style), Paragraph(str(soru_metni).replace("\n", "<br/>"), normal_style)],
            [Paragraph("<b>Cevap:</b>", normal_style), Paragraph(str(ogrenci_cevabi).replace("\n", "<br/>"), normal_style)],
            [Paragraph("<b>Yorum:</b>", normal_style), Paragraph(str(yorum).replace("\n", "<br/>"), normal_style)],
        ]

        q_table = Table(row_data, colWidths=[2.5 * cm, 13.5 * cm])
        q_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))

        story.append(q_table)
        story.append(Spacer(1, 12))

    doc.build(story)
    logger.info(f"PDF Report generated at: {output_path}")
    return output_path
