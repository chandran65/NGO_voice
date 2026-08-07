import os
import sys
import subprocess
import urllib.request
import re
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

bin_dir = Path(__file__).resolve().parent
cloudflared_exe = bin_dir / "cloudflared.exe"

if not cloudflared_exe.exists():
    print("Downloading Cloudflare Tunnel binary (cloudflared.exe)...")
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try:
        urllib.request.urlretrieve(url, cloudflared_exe)
        print("cloudflared.exe downloaded successfully!")
    except Exception as e:
        print(f"Error downloading cloudflared: {e}")
        sys.exit(1)

print("Starting Cloudflare Tunnel to http://localhost:8000...")
cmd = [str(cloudflared_exe), "tunnel", "--url", "http://localhost:8000"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore")

found_url = False
for line in iter(proc.stdout.readline, ""):
    print(line, end="")
    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
    if match and not found_url:
        found_url = True
        pub_url = match.group(0)
        print("\n" + "="*60)
        print(f"🚀 STABLE CLOUDFLARE PUBLIC HTTPS URL:")
        print(f"👉 {pub_url}")
        print("="*60 + "\n")

proc.wait()
