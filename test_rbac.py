import urllib.request, urllib.parse, http.cookiejar, re

BASE = "http://127.0.0.1:5000"

def make_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get_csrf(opener, path):
    with opener.open(BASE + path) as r:
        html = r.read().decode('utf-8', errors='ignore')
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None

def login(opener, email, password, role):
    csrf = get_csrf(opener, "/auth/login")
    data = urllib.parse.urlencode({
        "csrf_token": csrf,
        "email": email, "password": password, "role": role,
        "remember": "y", "submit": "Login"
    }).encode()
    req = urllib.request.Request(BASE + "/auth/login", data=data, method="POST")
    opener.open(req).read()

def check(urls, expected):
    opener = make_opener()
    login(opener, *expected['login'])
    print(f"\n[USER {expected['login'][2]}] expecting {expected['status']} for:")
    for u in urls:
        try:
            with opener.open(BASE + u) as r:
                code = r.getcode()
        except urllib.error.HTTPError as e:
            code = e.code
        symbol = "✅" if code == expected['status'] else "❌"
        print(f"  {symbol} {u} -> {code} (expected {expected['status']})")

# Citizen -> dashboard OK but admin forbidden
check(["/dashboard/citizen"], {"login": ("citizen1@test.com","Citizen@123","citizen"), "status": 200})
check(["/admin-panel/","/admin-panel/users","/dashboard/admin"],
      {"login": ("citizen1@test.com","Citizen@123","citizen"), "status": 403})
# Officer -> officer dashboard OK but admin-panel forbidden
check(["/dashboard/officer"], {"login": ("off_water_n@cgs.gov","Officer@123","officer"), "status": 200})
check(["/admin-panel/users","/dashboard/admin"],
      {"login": ("off_water_n@cgs.gov","Officer@123","officer"), "status": 403})
# Co-Officer -> co_officer dashboard OK, admin-panel/users forbidden
check(["/dashboard/co-officer"], {"login": ("co_water@cgs.gov","Officer@123","co_officer"), "status": 200})
check(["/admin-panel/users"], {"login": ("co_water@cgs.gov","Officer@123","co_officer"), "status": 403})
# Admin -> admin panel OK
check(["/dashboard/admin","/admin-panel/","/admin-panel/users","/admin-panel/performance","/admin-panel/notifications","/stats/"],
      {"login": ("admin@cgs.gov","Admin@123","main_authority"), "status": 200})

# Login as citizen, open GRV list, pick first GRV, check detail page
opener = make_opener()
login(opener, "citizen1@test.com", "Citizen@123", "citizen")
with opener.open(BASE + "/grievance/my") as r:
    html = r.read().decode('utf-8', errors='ignore')
grv_ids = re.findall(r'GRV-\d{4}-\d{4}', html)
print(f"\nFound grievance IDs: {grv_ids[:3]} ...")
for gid in grv_ids[:2]:
    for u in [f"/grievance/{gid}", f"/grievance/{gid}/verify"]:
        try:
            with opener.open(BASE + u) as r:
                code = r.getcode()
        except urllib.error.HTTPError as e:
            code = e.code
        print(f"  citizen access {u} -> {code}")
