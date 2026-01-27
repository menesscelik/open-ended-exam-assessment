from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_fonts():
    """Registers a font that supports Turkish characters (Arial on Windows)."""
    font_name = "Helvetica" # Fallback
    try:
        # Common Windows path
        font_path = 'C:\\Windows\\Fonts\\arial.ttf'
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:\\Windows\\Fonts\\arialbd.ttf'))
            font_name = 'Arial'
            logger.info("Successfully registered Arial font.")
        else:
            logger.warning("Arial font not found at default Windows path. Using Helvetica (may not support all TR chars).")
    except Exception as e:
        logger.warning(f"Could not register custom font: {e}")
    
    return font_name

def generate_exam_report_pdf(student_data, results, output_path):
    """
    Generates a PDF report for the exam results.
    
    Args:
        student_data (dict): {'name': 'Name Surname', 'number': '12345'}
        results (list): List of result objects/dicts. Each should have:
            - soru_no
            - ogrenci_cevabi
            - final_puan
            - yorum
            - ideal_cevap (optional)
        output_path (str): Path to save the PDF.
    """
    
    font_name = register_fonts()
    bold_font_name = 'Arial-Bold' if font_name == 'Arial' else 'Helvetica-Bold'
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=bold_font_name,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.darkblue
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontName=bold_font_name,
        fontSize=12,
        textColor=colors.grey
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=12
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontName=bold_font_name,
        fontSize=12,
        textColor=colors.darkblue,
        spaceBefore=12,
        spaceAfter=6
    )

    # 1. Title & Header
    story.append(Paragraph("Sınav Değerlendirme Raporu", title_style))
    
    # Student Info Table
    data = [
        ["Öğrenci Adı Soyadı:", student_data.get('name', 'Bilinmiyor')],
        ["Öğrenci Numarası:", student_data.get('number', 'Bilinmiyor')],
        ["Değerlendirme Tarihi:", "Otomatik Sistem"] # Could add current date
    ]
    
    t_info = Table(data, colWidths=[5*cm, 10*cm])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTNAME', (0,0), (0,-1), bold_font_name),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 20))
    
    # 2. Overall Score Calculation
    total_score = 0
    total_max_score = 0
    
    for r in results:
        # Handle dict or object
        puan = r.get('final_puan') if isinstance(r, dict) else getattr(r, 'final_puan', 0)
        mx = r.get('max_puan') if isinstance(r, dict) else getattr(r, 'max_puan', 100)
        
        total_score += float(puan) if puan else 0
        total_max_score += float(mx) if mx else 0
        
    # Formatting the summary
    summary_text = f"<b>Toplam Başarı:</b> {total_score:.1f} / {total_max_score:.1f}"
    if total_max_score > 0:
        percentage = (total_score / total_max_score) * 100
        summary_text += f" (%{percentage:.1f})"
        
    story.append(Paragraph(summary_text, ParagraphStyle('Summary', parent=normal_style, fontSize=14, spaceAfter=20)))

    # 3. Detailed Results
    story.append(Paragraph("Detaylı Soru Analizi", ParagraphStyle('SubTitle', parent=title_style, fontSize=18, alignment=TA_LEFT)))
    story.append(Spacer(1, 10))
    
    for idx, res in enumerate(results):
        # Extract data safely
        if isinstance(res, dict):
            soru_no = res.get('soru_no', idx + 1)
            soru_metni = res.get('soru_metni', '')
            ogrenci_cevabi = res.get('ogrenci_cevabi', '')
            puan = res.get('final_puan', 0)
            max_puan = res.get('max_puan', 100)
            yorum = res.get('yorum', '')
        else:
            soru_no = getattr(res, 'soru_no', idx + 1)
            soru_metni = getattr(res, 'soru_metni', '')
            ogrenci_cevabi = getattr(res, 'ogrenci_cevabi', '')
            puan = getattr(res, 'final_puan', 0)
            max_puan = getattr(res, 'max_puan', 100)
            yorum = getattr(res, 'yorum', '')
            
        # Question Header
        q_header = f"Soru {soru_no} (Puan: {puan} / {max_puan})"
        story.append(Paragraph(q_header, h3_style))
        
        # Details Table
        # Using a table for layout to keep things aligned nicely
        
        # Truncate very long texts if needed or rely on Wrap
        
        row_data = [
            [Paragraph("<b>Soru:</b>", normal_style), Paragraph(str(soru_metni).replace('\n', '<br/>'), normal_style)],
            [Paragraph("<b>Cevap:</b>", normal_style), Paragraph(str(ogrenci_cevabi).replace('\n', '<br/>'), normal_style)],
            [Paragraph("<b>Yorum & Puan:</b>", normal_style), Paragraph(str(yorum).replace('\n', '<br/>').replace('KRİTER DETAYLARI:', '<b>KRİTER DETAYLARI:</b>'), normal_style)]
        ]
        
        q_table = Table(row_data, colWidths=[2.5*cm, 13.5*cm])
        q_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        
        story.append(q_table)
        story.append(Spacer(1, 15))
        
    doc.build(story)
    logger.info(f"PDF Report generated at: {output_path}")
    return output_path
