
import os
import shutil

desktop_backend = r'C:\Users\menes\Desktop\open-ended-exam-assessment\backend'
local_backend = r'c:\open-ended-exam-assessment\backend'

files_to_sync = ['main.py', 'ocr_utils.py']

for file in files_to_sync:
    src = os.path.join(desktop_backend, file)
    dst = os.path.join(local_backend, file)
    
    if os.path.exists(src):
        # Read src
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Write dst
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Synced {file} from Desktop to Workspace.")
    else:
        print(f"Warning: {file} not found on Desktop.")

print("Sync complete.")
