
import os

file_path = r'C:\Users\menes\Desktop\open-ended-exam-assessment\backend\ocr_utils.py'

if os.path.exists(file_path):
    print(f"File found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print(f"File NOT found: {file_path}")
