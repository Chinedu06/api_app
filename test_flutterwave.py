import os
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env from current dir

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
print("Using key:", FLW_SECRET_KEY[:15] + "...")

headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}
url = "https://api.flutterwave.com/v3/banks/NG"

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print("Status:", resp.status_code)
    print("Response:", resp.json())
except Exception as e:
    print("❌ Error:", e)
exit