"""Quick check of stats, chat, and notification pages."""
import urllib.request, urllib.parse, http.cookiejar, re

BASE = "http://127.0.0.1:5000"

def make_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def csrf(opener, path):
    with opener.open(BASE + path) as r:
        html = r.read().decode('utf-8', errors='ignore')
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return (m.group(1) if m else None), html

def login(opener, email, password, role):
    token, _ = csrf(opener, "/auth/login")
    data = urllib.parse.urlencode({
        "csrf_token": token, "email": email, "password": password,
        "role": role, "submit": "Login"
    }).encode()
    opener.open(urllib.request.Request(BASE + "/auth/login", data=data, method="POST")).read()

print("=== Admin: checking stats, notifications, performance ===")
admin = make_opener()
login(admin, "admin@cgs.gov", "Admin@123", "main_authority")

for path in ["/stats/", "/admin-panel/notifications", "/admin-panel/performance", "/admin-panel/users"]:
    try:
        with admin.open(BASE + path) as r:
            html = r.read().decode('utf-8', errors='ignore')
            # Check for Chart.js presence on stats page
            has_chart = "Chart" in html or "canvas" in html.lower()
            print(f"  [200] {path}  (len={len(html)}, charts={'yes' if has_chart else 'no'})")
    except Exception as e:
        print(f"  [ERR] {path}: {e}")

print("\n=== Officer: checking department chat ===")
off = make_opener()
login(off, "off_water_n@cgs.gov", "Officer@123", "officer")
try:
    with off.open(BASE + "/chat/department") as r:
        html = r.read().decode('utf-8', errors='ignore')
        print(f"  [200] /chat/department (len={len(html)})")
    # Send a chat message
    token, _ = csrf(off, "/chat/department")
    data = urllib.parse.urlencode({
        "csrf_token": token, "department_id": "1", "message": "Test message from officer for demo."
    }).encode()
    off.open(urllib.request.Request(BASE + "/chat/department/send", data=data, method="POST")).read()
    print("  Chat message sent successfully.")
except Exception as e:
    print(f"  [ERR] chat: {e}")

print("\n=== Notification logs count (from notifications page) ===")
with admin.open(BASE + "/admin-panel/notifications") as r:
    html = r.read().decode('utf-8', errors='ignore')
    # Count table rows in notification log
    rows = re.findall(r'<tr>', html)
    print(f"  Notification log rows found: {len(rows)}")

print("\nAll phase checks done.")
