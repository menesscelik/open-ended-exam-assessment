from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import json
import re

from app.schemas.dtos import ReportRequest
from app.services.reporting import generate_exam_report_pdf
from app.core.config import settings

router = APIRouter()

@router.post("/create-report")
def create_report(request: ReportRequest):
    """
    Generates a PDF report for the given exam results.
    """
    try:
        # Load student data
        student_data = {}
        # Assuming results are stored in 'results/' relative to backend root
        # We need to construct absolute path or rely on CWD being backend root
        results_dir = os.path.join(settings.BASE_DIR, "results")
        student_data_path = os.path.join(results_dir, f"{request.request_id}_student.json")
        
        if os.path.exists(student_data_path):
            try:
                with open(student_data_path, "r", encoding="utf-8") as f:
                    student_data = json.load(f)
            except Exception as e:
                print(f"Warning: Error reading student data: {e}")
        
        # Generate PDF
        # Sanitize filename
        s_name = student_data.get('name', 'Ogrenci').replace(' ', '_')
        s_num = student_data.get('number', 'No')
        # Remove non-alphanumeric chars from filename just in case
        s_name = re.sub(r'[^\w\-_]', '', s_name)
        s_num = re.sub(r'[^\w\-_]', '', str(s_num))
        
        pdf_filename = f"{s_name}_{s_num}.pdf"
        output_path = os.path.join(results_dir, pdf_filename)
        
        # Ensure directory exists (it should, but safety first)
        os.makedirs(results_dir, exist_ok=True)
        
        # Generate
        generate_exam_report_pdf(student_data, request.results, output_path)
        
        return FileResponse(output_path, media_type='application/pdf', filename=pdf_filename)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Rapor oluşturulamadı: {str(e)}")
