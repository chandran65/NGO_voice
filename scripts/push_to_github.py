import os
import sys
import base64
import json
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def upload_file_via_api(file_path: Path, repo: str, token: str):
    rel_path = file_path.relative_to(BASE_DIR).as_posix()
    encoded_path = urllib.parse.quote(rel_path)
    url = f"https://api.github.com/repos/{repo}/contents/{encoded_path}"
    
    try:
        with open(file_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as err:
        print(f"Error reading {rel_path}: {err}")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "NGO-Voice-Publisher"
    }

    sha = None
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sha = data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"Check failed for {rel_path}: {e.code} {e.reason}")
            return False

    payload = {
        "message": f"Add {rel_path} for NGO Voice Calling System",
        "content": content_b64
    }
    if sha:
        payload["sha"] = sha

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="PUT")
    
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Uploaded: {rel_path}")
            return True
    except Exception as e:
        print(f"❌ Failed {rel_path}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/push_to_github.py <TOKEN>")
        sys.exit(1)
        
    token = sys.argv[1].strip()
    repo = "chandran65/NGO_voice"
    
    ignore_files = [".db", ".sqlite3", ".pyc", ".log", "cloudflared.exe"]
    files_to_push = []
    
    for p in BASE_DIR.rglob("*"):
        if p.is_file():
            if any(p.name.endswith(ext) for ext in ignore_files) or "__pycache__" in str(p) or ".git" in str(p):
                continue
            files_to_push.append(p)
            
    print(f"Uploading {len(files_to_push)} files to https://github.com/{repo}...")
    success = 0
    for f in files_to_push:
        if upload_file_via_api(f, repo, token):
            success += 1
            
    print(f"\n🎉 Finished! Uploaded {success}/{len(files_to_push)} files to https://github.com/{repo}")

if __name__ == "__main__":
    main()
