
import os

file_path = r'C:\Users\menes\Desktop\open-ended-exam-assessment\backend\ocr_utils.py'

if not os.path.exists(file_path):
    print("File not found!")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """# Load environment variables
load_dotenv()"""

replacement = """# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)"""

if target in content:
    new_content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully patched ocr_utils.py")
else:
    print("Target string not found, maybe already patched?")
    # Fallback checks
    if "dotenv_path=env_path" in content:
        print("Already patched.")
    else:
        print("Could not find exact match to patch.")
