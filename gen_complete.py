#!/usr/bin/env python3
"""Build rncp-data.json + projects_data.json from 42 API dumps + Excel,
then generate a minimalist rncp-final.html with comparison tables + inline deps."""
import json, os, requests, openpyxl

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 1. Load 42 API data from both GitHub datasets ──────────────────────────
URL_CALC = "https://raw.githubusercontent.com/lucas-ht/42calculator/2881a6ee16dfce614b887bbff398734e49a045af/data/projects_21.json"
URL_INS  = "https://raw.githubusercontent.com/fZpHr/42insight/4ce328eab8d4918d95a2c3dfea52bab5ba11bcd5/lib/forty-two/data/projects_21.json"

ds1 = requests.get(URL_CALC, timeout=30).json()["projects"]
ds2 = requests.get(URL_INS, timeout=30).json()["projects"]

# Merge: prefer ds1 (42Paris-specific), fill gaps from ds2
proj_by_id = {}
for p in ds1:
    proj_by_id[p["id"]] = p
for p in ds2:
    if p["id"] not in proj_by_id:
        proj_by_id[p["id"]] = p

# ── 2. Excel project-name → 42 API id mapping ───────────────────────────────
# Build slug lookup (lowercase, with and without 42cursus prefix)
slug_lookup = {}
for pid, p in proj_by_id.items():
    s = p["slug"].lower()
    slug_lookup[s] = p
    if s.startswith("42cursus-"):
        alt = s[9:]
        if alt not in slug_lookup:
            slug_lookup[alt] = p

# Name fix table: Excel name → API slug (lowercase)
NAME_FIX = {
    "Avaj_launcher": "avaj-launcher",
    "Bomberman": "bomberman",
    "Camagru": "camagru",
    "darkly": "darkly",
    "fix-me": "fix-me",
    "ft_hangouts": "ft_hangouts",
    "h42n42": "h42n42",
    "Hypertube": "hypertube",
    "Matcha": "matcha",
    "Nibbler": "nibbler",
    "Piscine Mobile": "mobile",
    "Piscine Object": "piscine-object",
    "Piscine Php Symfony": "42cursus-piscine-php-symfony",
    "Piscine Python Django": "piscine-django",
    "Piscine Ruby On Rails": "42cursus-piscine-ruby-on-rails",
    "Piscine OCaml": "42cursus-piscine-ocaml",
    "Piscine Cybersecurity": "cybersecurity",
    "Red tetris": "red-tetris",
    "Swifty_companion": "swifty-companion",
    "Swifty_proteins": "swifty-proteins",
    "Swifty": "swifty-generic",       # synthetic (not in API)
    "Swingy": "swingy",
    "42sh": "42sh",
    "BADASS": "badass",               # synthetic (not in API dumps)
    "DoomNuken": "doom-nukem",
    "HumanGL": "humangl",
    "Inception-Of-Things": "inception-of-things",
    "kfs-1": "kfs-1",
    "kfs-2": "kfs-2",
    "kfs-3": "kfs-3",
    "kfs-4": "kfs-4",
    "kfs-5": "kfs-5",
    "kfs-6": "kfs-6",
    "kfs-7": "kfs-7",
    "kfs-8": "kfs-8",
    "kfs-9": "kfs-9",
    "kfs-x": "kfs-x",
    "override": "override",
    "Pestilence": "pestilence",
    "pestilence": "pestilence",
    "rt": "rt",
    "total-perspective-vortex": "total-perspective-vortex",
    "ft_ality": "ft_ality",
    "ft_turing": "ft_turing",
    "famine": "famine",
    "ft_linux": "ft_linux",
    "ft_malcolm": "ft_malcolm",
    "ft_script": "ft_script",
    "ft_select": "ft_select",
    "ft_shield": "ft_shield",
    "ft_ssl-md5": "ft_ssl_md5",
    "lem-ipc": "lem-ipc",
    "libasm": "libasm",
    "little-penguin": "little-penguin-1",
    "malloc": "malloc",
    "matt-deamon": "matt-daemon",
    "nm": "nm",
    "rainfall": "rainfall",
    "snowcrash": "snow-crash",
    "snow-crash": "snow-crash",
    "strace": "strace",
    "taskmaster": "taskmaster",
    "woody-woodpacker": "woody-woodpacker",
    "gbmu": "gbmu",
    "zappy": "zappy",
    "ActiveConnect": "activeconnect",
    "ActiveTechTales": "activetechtales",
    "boot2root": "boot2root",
    "MicroForensX": "microforensx",
    "UnleashTheBox": "unleashthebox",
    "ft_nmap": "ft_nmap",
    "ft_ping": "ft_ping",
    "ft_traceroute": "ft_traceroute",
    "AccessibleDirectory": "accessibledirectory",
    "ActiveDiscovery": "activediscovery",
    "AdministrativeDirectory": "administrativedirectory",
    "AutomaticDirectory": "automaticdirectory",
    "cloud-1": "cloud-1",
    "dslr": "dslr",
    "cloud-1": "cloud-1",
    # Shared / experience projects
    "Part-Time I": "part_time-i",
    "Part-Time II": "part_time-ii",
    "Alternance RNCP 6 - 1 an": "fr-alternance-rncp6-1-an",
    "Alternance RNCP 6 - 2 ans": "fr-alternance-rncp6-2-ans",
    "Alternance RNCP 7 - 1 an": "fr-alternance-rncp7-1-an",
    "Alternance RNCP 7 - 2 ans": "fr-alternance-rncp7-2-ans",
    "Work Experience I": "internship-i",
    "Work Experience II": "internship-ii",
    "Startup Experience": "startup-internship",
}

# Custom projects not in any dataset
CUSTOM = {
    "swifty-generic": {"id": 9001, "slug": "42cursus-swifty", "name": "Swifty", "difficulty": 9450, "duration": 0, "exam": False, "parent": None, "children": []},
    "badass": {"id": 1503, "slug": "42cursus-badass", "name": "BADASS", "difficulty": 22450, "duration": 0, "exam": False, "parent": None, "children": []},
    "fr-alternance-rncp6-1-an": {"id": 2561, "slug": "fr-alternance-rncp6-1-an", "name": "Alternance RNCP 6 - 1 an", "difficulty": 90000, "duration": 0, "exam": False, "parent": None, "children": []},
    "fr-alternance-rncp6-2-ans": {"id": 2562, "slug": "fr-alternance-rncp6-2-ans", "name": "Alternance RNCP 6 - 2 ans", "difficulty": 150000, "duration": 0, "exam": False, "parent": None, "children": []},
    "fr-alternance-rncp7-1-an": {"id": 2563, "slug": "fr-alternance-rncp7-1-an", "name": "Alternance RNCP 7 - 1 an", "difficulty": 90000, "duration": 0, "exam": False, "parent": None, "children": []},
    "fr-alternance-rncp7-2-ans": {"id": 2564, "slug": "fr-alternance-rncp7-2-ans", "name": "Alternance RNCP 7 - 2 an", "difficulty": 180000, "duration": 0, "exam": False, "parent": None, "children": []},
}

def find_project(excel_name):
    """Return (id, slug, name, difficulty, duration, exam, parent_id) for an Excel project."""
    slug = NAME_FIX.get(excel_name)
    if not slug:
        slug = excel_name.lower().replace(" ", "-").replace("_", "-")
    # Try direct slug lookup
    if slug in slug_lookup:
        p = slug_lookup[slug]
        return _normalize(p)
    if f"42cursus-{slug}" in slug_lookup:
        p = slug_lookup[f"42cursus-{slug}"]
        return _normalize(p)
    # Try case-insensitive exact name
    for p in proj_by_id.values():
        if p["name"].lower() == slug.lower():
            return _normalize(p)
    # Try custom
    if slug in CUSTOM:
        return _normalize(CUSTOM[slug])
    # Try without 42cursus prefix
    for p in proj_by_id.values():
        pslug = p["slug"].lower()
        if pslug == slug or (pslug.startswith("42cursus-") and pslug[9:] == slug):
            return _normalize(p)
    # Last resort: fuzzy name match
    for p in proj_by_id.values():
        pn = p["name"].lower().replace(" ", "-")
        if pn == slug or p["slug"].lower() == slug:
            return _normalize(p)
    return None

def _normalize(p):
    return {
        "id": p["id"],
        "slug": p["slug"],
        "name": p["name"],
        "difficulty": p.get("difficulty", 0) or 0,
        "duration": p.get("duration", 0) or 0,
        "exam": p.get("exam", False),
        "parent_id": (p.get("parent") or {}).get("id") if p.get("parent") else None,
        "children": [],
    }

# ── 3. Parse Excel ───────────────────────────────────────────────────────────
excel_path = "/Users/spectre/Downloads/Copie de 42 Planner RNCP 7.xlsx"
wb = openpyxl.load_workbook(excel_path, data_only=True)

def extract_projects(ws, col_offset):
    """Extract (name, xp) from a column, skipping headers and totals."""
    EXCLUDE_NAMES = {"TOTAUX", "Theorique", "Actuel", "Colonne 1", "Projet de groupe",
                     "Level", "Legend", "Project Name"}
    projects = []
    for row in ws.iter_rows(min_row=2, max_col=col_offset+1, max_row=ws.max_row):
        name_cell = row[col_offset - 1]      # 1-based → 0-based
        xp_cell = row[col_offset]            # next column
        name = name_cell.value
        xp = xp_cell.value
        if not name or not isinstance(name, str):
            continue
        name = name.strip()
        if name in EXCLUDE_NAMES:
            continue
        if name.startswith("CC Level") or name.startswith("Pour calculer"):
            continue
        if xp is None or not isinstance(xp, (int, float)):
            continue
        projects.append((name, float(xp)))
    return projects

SHARED_NAMES = {"Work Experience I", "Work Experience II", "Part-Time I", "Part-Time II",
                "Alternance RNCP 6 - 1 an", "Alternance RNCP 6 - 2 ans",
                "Alternance RNCP 7 - 1 an", "Alternance RNCP 7 - 2 ans",
                "Startup Experience"}

# Extract all data
sheets_data = []
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    col_a = extract_projects(ws, 1)   # Column A
    col_j = extract_projects(ws, 10)  # Column J
    sheets_data.append((sheet_name, col_a, col_j))

# Map Excel columns to RNCP tracks:
# Sheet 1 Col A → "Web/Mobile", Col J → "Applicatif"
# Sheet 2 Col A → "SI/Réseaux", Col J → "Data"
TRACK_MAP = [
    ("rn6wm", "RNCP 6 — Web/Mobile", 0, "A"),
    ("rn6ap", "RNCP 6 — Applicatif", 0, "J"),
    ("rn7sr", "RNCP 7 — SI/Réseaux", 1, "A"),
    ("rn7da", "RNCP 7 — Data", 1, "J"),
]

# ── 4. Build projects_data.json + rncp_data.json ──────────────────────────────
all_projects = {}  # id → project dict
suite_ids = []     # shared projects
option_projects = {}  # (track_type, option_letter) → [project_ids]

for track_type, track_title, sheet_idx, col_letter in TRACK_MAP:
    sheet_name, col_a, col_j = sheets_data[sheet_idx]
    projects = col_a if col_letter == "A" else col_j
    opt_key = (track_type, col_letter)
    option_projects[opt_key] = []
    
    for name, xp in projects:
        if name in SHARED_NAMES:
            # Add to suite
            p = find_project(name)
            if p and p["id"] not in all_projects:
                all_projects[p["id"]] = p
            if p and p["id"] not in suite_ids:
                suite_ids.append(p["id"])
            continue
        
        p = find_project(name)
        if p:
            if p["id"] not in all_projects:
                all_projects[p["id"]] = p
            option_projects[opt_key].append(p["id"])
        else:
            print(f"WARNING: {name} — proj not found in API or custom!")
            # Create a placeholder
            placeholder = {"id": 9000 + len(all_projects), "slug": name.lower().replace(" ", "-"), 
                          "name": name, "difficulty": xp, "duration": 0, "exam": False, 
                          "parent_id": None, "children": [], "custom": True}
            all_projects[placeholder["id"]] = placeholder
            option_projects[opt_key].append(placeholder["id"])

# Experience projects
EXP_NAMES = ["Work Experience I", "Work Experience II", "Part-Time I", "Part-Time II", "Startup Experience"]
exp_ids = []
for name in EXP_NAMES:
    p = find_project(name)
    if p and p["id"] not in all_projects:
        all_projects[p["id"]] = p
    if p and p["id"] not in exp_ids:
        exp_ids.append(p["id"])

# Also add apprentissage sub-projects (experience sub-projects)
APPREN_IDS = [1857, 1864, 1865, 1872]
for aid in APPREN_IDS:
    if aid not in all_projects:
        if aid in proj_by_id:
            all_projects[aid] = _normalize(proj_by_id[aid])
        elif aid == 1864:
            all_projects[1864] = {"id": 1864, "slug": "apprenticeship-2y-year1-sub4", "name": "Apprentissage 2 ans - 1ère année - 4", "difficulty": 0, "duration": 0, "exam": False, "parent_id": 1857, "children": [], "custom": True}
        elif aid == 1872:
            all_projects[1872] = {"id": 1872, "slug": "apprenticeship-2y-year2-sub4", "name": "Apprentissage 2 ans - 2ème année - 4", "difficulty": 0, "duration": 0, "exam": False, "parent_id": 1857, "children": [], "custom": True}
        elif aid == 1865:
            all_projects[1865] = {"id": 1865, "slug": "apprenticeship-2y-year2-sub4", "name": "Apprentissage 2 ans - 2ème année - 4", "difficulty": 0, "duration": 0, "exam": False, "parent_id": 1857, "children": [], "custom": True}

# Build children lists (reverse parent mapping)
for pid, p in all_projects.items():
    if p["parent_id"] and p["parent_id"] in all_projects:
        if pid not in all_projects[p["parent_id"]]["children"]:
            all_projects[p["parent_id"]]["children"].append(pid)

# Add known kfs sequential dependency chain: kfs-1 → kfs-2 → kfs-3 → ... → kfs-x
kfs_ids_sorted = sorted(
    [pid for pid, p in all_projects.items() if p["slug"].startswith("42cursus-kfs")],
    key=lambda pid: (len(all_projects[pid]["slug"]), all_projects[pid]["slug"]),
)
# kfs order: kfs-1 < kfs-2 < ... < kfs-9 < kfs-x
kfs_order = ["kfs-1", "kfs-2", "kfs-3", "kfs-4", "kfs-5", "kfs-6", "kfs-7", "kfs-8", "kfs-9", "kfs-x"]
kfs_by_slug = {all_projects[pid]["slug"].replace("42cursus-", ""): pid for pid in kfs_ids_sorted}
for i in range(len(kfs_order) - 1):
    child_slug = kfs_order[i + 1]
    parent_slug = kfs_order[i]
    child_id = kfs_by_slug.get(child_slug)
    parent_id = kfs_by_slug.get(parent_slug)
    if child_id and parent_id and child_id in all_projects:
        all_projects[child_id]["parent_id"] = parent_id
        if child_id not in all_projects[parent_id]["children"]:
            all_projects[parent_id]["children"].append(child_id)

# Add known implicit dependencies for common 42cursus progression
KNOWN_DEPS = {
    # snow-crash → darkly (security progression)
    1405: 1404,  # darkly ← snow-crash
    # Security/anti-debugging chain: nm → override → woody-woodpacker
    1448: 1467,  # override ← nm
    1419: 1448,  # woody-woodpacker ← override
    # ft_linux → little-penguin (Linux kernel progression)
    1416: 1415,  # little-penguin ← ft_linux
}
for child_id, parent_id in KNOWN_DEPS.items():
    if child_id in all_projects and parent_id in all_projects:
        all_projects[child_id]["parent_id"] = parent_id
        if child_id not in all_projects[parent_id]["children"]:
            all_projects[parent_id]["children"].append(child_id)


# Build options for rncp_data.json
# RNCP 6 = Sheet 1: Col A (Option 1) + Col J (Option 2)
# RNCP 7 = Sheet 2: Col A (Option 1) + Col J (Option 2)
# Option titles come from the Excel sheet header
def get_header(ws, col_letter):
    """Read the option title from the sheet header row."""
    col_map = {"A": 1, "J": 10}
    cell = ws.cell(row=1, column=col_map.get(col_letter, 1))
    return cell.value if cell else None

def infer_option_title(sheet_idx, col_letter):
    """Infer option title from known structure."""
    titles = {
        (0, "A"): "Option 1 — Web/Mobile",
        (0, "J"): "Option 2 — Applicatif",
        (1, "A"): "Option 1 — SI/Réseaux",
        (1, "J"): "Option 2 — Data",
    }
    return titles.get((sheet_idx, col_letter), f"Option {'1' if col_letter == 'A' else '2'}")

rncp_tracks = []
# Group TRACK_MAP entries by level
for level, level_title, sheet_idx in [(6, "RNCP 6", 0), (7, "RNCP 7", 1)]:
    # Find the two track entries for this level
    level_entries = [t for t in TRACK_MAP if t[0].startswith(f"rn{level}")]
    options = []
    for track_type, track_title, t_sheet_idx, col_letter in level_entries:
        opt_projects = option_projects.get((track_type, col_letter), [])
        exp = 42000 if level == 6 else 63000
        opt_label = "1" if col_letter == "A" else "2"
        # Extract the option subtitle from track_title
        opt_sub = track_title.split("—")[-1].strip() if "—" in track_title else track_title
        options.append({
            "title": f"Option {opt_label} — {opt_sub}",
            "experience": exp,
            "number_of_projects": len(opt_projects),
            "projects": opt_projects,
        })
    rncp_tracks.append({
        "type": f"rn{level}",
        "title": level_title,
        "level": str(level),
        "options": options,
    })

# Build rncp_data.json
rncp_data = {
    "rncp": rncp_tracks,
    "suite": {"projects": suite_ids},
    "experience": {"projects": exp_ids},
}

# Build projects_data.json
projects_data = {"projects": [p for p in all_projects.values()]}

# Save data files
with open(os.path.join(SCRIPT_DIR, "projects_data.json"), "w") as f:
    json.dump(projects_data, f, indent=2)

with open(os.path.join(SCRIPT_DIR, "rncp_data.json"), "w") as f:
    json.dump(rncp_data, f, indent=2)

print(f"projects_data.json: {len(projects_data['projects'])} projects")
print(f"rncp_data.json: {len(rncp_tracks)} tracks, suite={len(suite_ids)} projects, experience={len(exp_ids)} projects")
for track in rncp_tracks:
    for opt in track["options"]:
        print(f"  {track['title']} / {opt['title']}: {len(opt['projects'])} projects")
print(f"Suite IDs: {suite_ids}")
print(f"Experience IDs: {exp_ids}")