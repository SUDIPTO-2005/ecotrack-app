import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"

# Step 1: Login
login_data = json.dumps({"email": "testuser@ecotrack.example.com", "password": "GreenPlanet2024!"}).encode()
req = urllib.request.Request(
    f"{BASE}/api/v1/accounts/login/",
    data=login_data,
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req) as r:
        auth = json.loads(r.read())
    token = auth.get("access", "")
    print(f"[LOGIN OK] token={token[:30]}...")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[LOGIN FAIL] {e.code}: {body}")
    exit(1)

# Step 2: POST /ai-coach/tips/
tips_req = urllib.request.Request(
    f"{BASE}/api/v1/ai-coach/tips/",
    data=b"{}",
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    method="POST"
)
try:
    with urllib.request.urlopen(tips_req) as r:
        result = json.loads(r.read())
    print("[TIPS OK]")
    print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[TIPS FAIL] HTTP {e.code}: {body}")
