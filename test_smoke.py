import urllib.request, urllib.parse, http.cookiejar, re

BASE = "http://127.0.0.1:5000"

def make_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get_csrf(opener, path):
    with opener.open(BASE + path) as r:
        html = r.read().decode('utf-8', errors='ignore')
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return (m.group(1) if m else None), html

def login(opener, email, password, role):
    csrf, _ = get_csrf(opener, "/auth/login")
    data = urllib.parse.urlencode({
        "csrf_token": csrf,
        "email": email,
        "password": password,
        "role": role,
        "remember": "y",
        "submit": "Login"
    }).encode()
    req = urllib.request.Request(BASE + "/auth/login", data=data, method="POST")
    with opener.open(req) as r:
        return r.geturl(), r.getcode()

def test_role(email, password, role, urls):
    opener = make_opener()
    final, code = login(opener, email, password, role)
    print(f"\n=== Login {role} {email} -> final={final} code={code}")
    for u in urls:
        try:
            with opener.open(BASE + u) as r:
                print(f"  [{r.getcode()}] {u}")
        except urllib.error.HTTPError as e:
            print(f"  [{e.code}] {u} (forbidden if 403)")
        except Exception as e:
            print(f"  [ERR] {u}: {e}")

test_role("citizen1@test.com", "Citizen@123", "citizen",
          ["/dashboard/citizen", "/grievance/submit", "/grievance/my"])
test_role("off_water_n@cgs.gov", "Officer@123", "officer",
          ["/dashboard/officer", "/chat/department", "/stats/"])
test_role("co_water@cgs.gov", "Officer@123", "co_officer",
          ["/dashboard/co-officer", "/chat/department", "/stats/"])
test_role("admin@cgs.gov", "Admin@123", "main_authority",
          ["/dashboard/admin", "/admin-panel/", "/admin-panel/users",
           "/admin-panel/performance", "/admin-panel/notifications", "/stats/"])
