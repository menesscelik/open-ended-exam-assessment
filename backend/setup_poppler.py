import os
import requests
import zipfile
import sys

def setup_poppler():
    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bin_dir = os.path.join(base_dir, 'bin')
    os.makedirs(bin_dir, exist_ok=True)
    
    # URL for Poppler
    POPPLER_URL = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip"
    zip_path = os.path.join(bin_dir, "poppler.zip")
    
    print(f"Checking for Poppler in {bin_dir}...", flush=True)
    
    # Check if already installed
    poppler_check_path = os.path.join(bin_dir, 'poppler-24.02.0', 'Library', 'bin')
    if os.path.exists(poppler_check_path):
        print("Poppler already installed locally.", flush=True)
        return poppler_check_path

    print(f"Downloading Poppler to {zip_path}...", flush=True)
    try:
        # Stream download
        with requests.get(POPPLER_URL, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(zip_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = int(100 * downloaded / total_size)
                        print(f"Progress: {percent}%", end='\r', flush=True)
        print("\nDownload complete.", flush=True)
        
        print("Extracting...", flush=True)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(bin_dir)
            
        print("Cleaning up...", flush=True)
        os.remove(zip_path)
        
        print("Poppler installed successfully!", flush=True)
        return poppler_check_path
            
    except Exception as e:
        print(f"\nError installing Poppler: {e}", flush=True)
        return None

if __name__ == "__main__":
    path = setup_poppler()
    if path:
        print(f"POPPLER_PATH={path}", flush=True)
    else:
        print("Setup failed.", flush=True)
