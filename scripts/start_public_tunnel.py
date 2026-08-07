import time
import sys
from pyngrok import ngrok

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("Connecting ngrok tunnel to localhost:8080...")
try:
    public_url = ngrok.connect(8080).public_url
    print(f"==================================================")
    print(f"LIVE PUBLIC HTTPS URL: {public_url}")
    print(f"==================================================")
    while True:
        time.sleep(10)
except Exception as e:
    print(f"Error starting ngrok tunnel: {e}")
