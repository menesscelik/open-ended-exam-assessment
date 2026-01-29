import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Otomatik Sınav Değerlendirme Sistemi"
    
    # Base directory of the project (backend/)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Poppler Configuration
    # Prioritize local project bin, then system paths
    LOCAL_POPPLER_PATH = os.path.join(BASE_DIR, 'bin', 'poppler-24.02.0', 'Library', 'bin')
    SYSTEM_POPPLER_PATH_1 = r'C:\Program Files\poppler\Library\bin'
    SYSTEM_POPPLER_PATH_2 = r'C:\Program Files\poppler\bin'

    @property
    def POPPLER_PATH(self):
        if os.path.exists(self.LOCAL_POPPLER_PATH):
            return self.LOCAL_POPPLER_PATH
        if os.path.exists(self.SYSTEM_POPPLER_PATH_1):
            return self.SYSTEM_POPPLER_PATH_1
        if os.path.exists(self.SYSTEM_POPPLER_PATH_2):
            return self.SYSTEM_POPPLER_PATH_2
        return None

settings = Settings()
