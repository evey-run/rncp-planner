#!/usr/bin/env python3
"""gen_html.py — Generate a minimalist, compact RNCP planner HTML.

Features:
  • Comparison matrix across all 4 RNCP tracks × options
  • Inline dependency badges (bricoles) per project row
  • Minimalist, dark-first design — everything fits one screen
"""
import json, os, html

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load data ────────────────────────────────────────────────────────────────
with open(os.path.join(SCRIPT_DIR, "projects_data.json")) as f:
    projects_data = json.load(f)
with open(os.path.join(SCRIPT_DIR, "rncp_data.json")) as f:
    rncp_data = json.load(f)

proj_map = {p["id"]: p for p in projects_data["projects"]}

# XP display helper
def fmt_xp(xp):
    if xp >= 1000:
        return f"{xp/1000:g}k"
    return f"{xp:g}"

def fmt_dur(d):           # d is in seconds (42 uses hours actually; treat as weeks)
    if d and d > 0:
        w = d / (3600 * 24 * 7)
        return f"{w:.1f}w"
    return ""

def fmt_diff(d):
    return f"{d/1000:g}k" if d and d >= 1000 else str(int(d)) if d else "0"

# ── Collect unique project IDs across all tracks ─────────────────────────────
def get_all_ids():
    ids = set()
    for track in rncp_data["rncp"]:
        for opt in track["options"]:
            ids.update(opt["projects"])
    ids.update(rncp_data["suite"]["projects"])
    ids.update(rncp_data["experience"]["projects"])
    return ids

all_ids = get_all_ids()

# ── Build comparison matrix data ─────────────────────────────────────────────
# For each project, show which option-groups it belongs to
option_groups = []  # (label, [ids])
suite_ids = rncp_data["suite"]["projects"]
exp_ids = rncp_data["experience"]["projects"]

for track in rncp_data["rncp"]:
    for opt in track["options"]:
        option_groups.append((f"{track['title']} › {opt['title']}", opt["projects"], track["type"]))

# ── Generate comparison matrix: which projects are added/removed between options ──
# Compare adjacent options within the same track
def build_comparison():
    rows = []  # (name, [presence_in_each_group])
    # Unique projects in each group
    group_sets = [(label, set(ids), tid) for label, ids, tid in option_groups]
    
    # All projects across all options (sorted by name)
    all_proj_ids = sorted(set().union(*[s for _, s, _ in group_sets if s]), 
                          key=lambda pid: (proj_map.get(pid, {}).get("name", "")).lower())
    
    for pid in all_proj_ids:
        p = proj_map.get(pid, {})
        name = p.get("name", "???")
        row = {
            "id": pid,
            "name": name,
            "xp": p.get("difficulty", 0),
            "presence": [],
        }
        for label, gset, tid in group_sets:
            row["presence"].append("✓" if pid in gset else "—")
        rows.append(row)
    
    return rows, group_sets

comp_rows, group_sets = build_comparison()

# ── Build combination comparisons ─────────────────────────────────────────────
# Combinations: choose one option per RNCP track
def get_combinations():
    comps = []
    for track in rncp_data["rncp"]:
        opts = track["options"]
        if not comps:
            for opt in opts:
                comps.append(set(opt["projects"]))
        else:
            new_comps = []
            for existing in comps:
                for opt in opts:
                    new_comps.append(existing | set(opt["projects"]))
            comps = new_comps
    return comps

combinations = get_combinations()

# Score combinations by total XP (higher = better)
combo_xp = []
for i, proj_set in enumerate(combinations):
    xp = sum(proj_map.get(pid, {}).get("difficulty", 0) for pid in proj_set)
    combo_xp.append((i, proj_set, xp))

# Sort by XP descending, get best and 2nd best
combo_xp.sort(key=lambda x: x[2], reverse=True)
best_combo = combo_xp[0][1] if len(combo_xp) > 0 else set()
second_combo = combo_xp[1][1] if len(combo_xp) > 1 else set()

# Build comparison rows for best vs second best
common_proj = best_combo & second_combo
unique_to_best = best_combo - second_combo
unique_to_second = second_combo - best_combo

def fmt_date(d):
    """Format duration in weeks to 'X w' string."""
    if not d or d <= 0:
        return ""
    w = d / (3600 * 24 * 7)
    return f"{w:.0f}w"

combo_rows = []
# Row 1: Common projects
combo_rows.append({
    "name": "Commun (dans les 2 combinaisons)",
    "in_best": "✓",
    "in_second": "✓",
    "comment": "+ shared",
    "total_xp": sum(proj_map.get(pid, {}).get("difficulty", 0) for pid in common_proj),
    "total_proj": len(common_proj),
})
# Rows for projects unique to best combo
for pid in sorted(unique_to_best, key=lambda p: fmt_xp(proj_map.get(p, {}).get("difficulty", 0)), reverse=True):
    p = proj_map.get(pid, {})
    combo_rows.append({
        "name": p.get("name", "??"),
        "in_best": "✓",
        "in_second": "—",
        "comment": "+ added",
        "total_xp": p.get("difficulty", 0),
        "total_proj": 1,
    })
# Rows for projects unique to second combo
for pid in sorted(unique_to_second, key=lambda p: fmt_xp(proj_map.get(p, {}).get("difficulty", 0)), reverse=True):
    p = proj_map.get(pid, {})
    combo_rows.append({
        "name": p.get("name", "??"),
        "in_best": "—",
        "in_second": "✓",
        "comment": "+ added (2nd)",
        "total_xp": p.get("difficulty", 0),
        "total_proj": 1,
    })
# Total row
combo_rows.append({
    "name": "TOTAL",
    "in_best": "",
    "in_second": "",
    "comment": f"{combo_xp[0][2]//1000}k XP • {len(best_combo)} proj • {combo_xp[1][2]//1000}k XP • {len(second_combo)} proj",
    "total_xp": combo_xp[0][2],
    "total_proj": len(best_combo) + len(second_combo),
})

# ── HTML generation ───────────────────────────────────────────────────────────
CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  background: #0a0a12;
  color: #d0d0e0;
  line-height: 1.4;
  padding: 12px;
  font-size: 12px;
  max-width: 1400px;
  margin: 0 auto;
}
/* Header */
header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #1a1a2e;
}
header h1 { 
  font-size: 16px; 
  font-weight: 600; 
  display: flex;
  align-items: center;
  gap: 8px;
}
header h1 .dot { width: 8px; height: 8px; border-radius: 50%; background: #4a9eff; }
.tabs { display: flex; gap: 2px; flex-wrap: wrap; }
.tabs button {
  background: #14141f;
  color: #8080a0;
  border: 1px solid #1a1a2e;
  padding: 4px 10px;
  font-size: 11px;
  cursor: pointer;
  transition: all .15s;
}
.tabs button:hover { background: #1a1a28; color: #a0a0c0; }
.tabs button.active { background: #4a9eff; color: #050508; font-weight: 600; }
/* Section */
section { margin-bottom: 16px; }
section h2 {
  font-size: 13px;
  font-weight: 600;
  color: #a0a0b0;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}
section h2 .g { width: 6px; height: 6px; border-radius: 50%; }
/* Comparison matrix */
.matrix {
  overflow-x: auto;
  border: 1px solid #1a1a2e;
  border-radius: 4px;
  background: #0d0d14;
}
.matrix table { border-collapse: collapse; width: 100%; font-size: 11px; }
.matrix th {
  background: #14141f;
  color: #606080;
  padding: 4px 6px;
  text-align: center;
  font-weight: 500;
  border-bottom: 1px solid #1a1a2e;
  position: sticky;
  top: 0;
  white-space: nowrap;
}
.matrix th.col-name { 
  position: sticky; 
  left: 0; 
  background: #1a1a2e; 
  color: #8080a0;
  font-weight: 500;
  text-align: left;
}
.matrix td {
  padding: 3px 6px;
  text-align: center;
  border-bottom: 1px solid #14141f;
  font-size: 11px;
  white-space: nowrap;
}
.matrix td.col-name {
  text-align: left;
  color: #b0b0c0;
  font-weight: 500;
  position: sticky;
  left: 0;
  background: #0d0d14;
  border-right: 1px solid #1a1a2e;
}
.matrix tr:hover td { background: #12121a; }
.matrix .yes { color: #4a9eff; font-weight: 600; }
.matrix .no { color: #303040; }
/* Legend */
.legend { display: flex; gap: 12px; margin-bottom: 6px; flex-wrap: wrap; }
.legend span { font-size: 11px; color: #606080; display: flex; align-items: center; gap: 4px; }
.legend .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
/* Project list */
.projs { 
  border: 1px solid #1a1a2e; 
  border-radius: 4px; 
  background: #0d0d14;
  overflow: hidden;
}
.projs table { border-collapse: collapse; width: 100%; font-size: 11px; }
.projs th {
  background: #14141f;
  color: #606080;
  padding: 4px 8px;
  text-align: left;
  font-weight: 500;
  border-bottom: 1px solid #1a1a2e;
  font-size: 11px;
}
.projs td {
  padding: 2px 8px;
  border-bottom: 1px solid #14141f;
  font-size: 11px;
}
.projs tr:hover td { background: #12121a; }
.projs .name { color: #b0b0c0; font-weight: 500; }
.projs .deps { font-family: inherit; }
.badge {
  display: inline-block;
  background: #1a1a2e;
  color: #80a0ff;
  border: 1px solid #2a2a4e;
  border-radius: 3px;
  padding: 0 4px;
  font-size: 10px;
  margin-right: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}
.badge.more { color: #8080a0; font-style: italic; }
.tag {
  display: inline-block;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: 600;
  line-height: 1.4;
}
.tag-exam { background: #3a2a0a; color: #e0c060; border: 1px solid #5a3e10; }
.tag-norm { background: #1a2a1a; color: #60d080; border: 1px solid #2a5a30; }
.tag-proj { background: #1a1a2e; color: #80a0ff; border: 1px solid #2a2a4e; }
.tag-shared { background: #2a1a1a; color: #ff8080; border: 1px solid #5a2a30; }
.tag-exp { background: #2a2a1a; color: #80d0d0; border: 1px solid #3a5a5a; }
.meta { color: #606080; }
/* Summary cards */
.summary { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.card {
  background: #14141f;
  border: 1px solid #1a1a2e;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 11px;
  flex: 1;
  min-width: 120px;
}
.card .v { font-size: 16px; font-weight: 600; color: #4a9eff; }
.card .l { color: #606080; font-size: 10px; }
/* Responsive */
@media (max-width: 800px) {
  body { padding: 6px; font-size: 11px; }
  .matrix th, .projs th { font-size: 10px; padding: 2px 4px; }
  .projs td { padding: 2px 4px; }
}
"""

def badge(name, color_class="badge"):
    return f'<span class="{color_class}">{html.escape(name)}</span>'

def get_deps(pid):
    """Get all dependency project names (ancestors via parent chain)."""
    deps = []
    p = proj_map.get(pid)
    if not p:
        return deps
    visited = set()
    # Direct parent
    parent_id = p.get("parent_id")
    while parent_id and parent_id not in visited and parent_id in proj_map:
        visited.add(parent_id)
        parent = proj_map[parent_id]
        deps.append(parent["name"])
        parent_id = parent.get("parent_id")
    # Children (projects that depend on this one)
    children = p.get("children", [])
    for cid in children[:2]:  # limit to 2 children
        cp = proj_map.get(cid)
        if cp:
            deps.append(f"→{cp['name']}")
    return deps

def generate_html():
    out = []
    out.append("<!DOCTYPE html>")
    out.append('<html lang="en"><head><meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    out.append(f"<title>42 RNCP Planner</title>")
    out.append(f"<style>{CSS}</style></head><body>")
    
    # Header
    out.append('<header>')
    out.append('<h1><span class="dot"></span> 42 RNCP Planner — Speedrun Edition</h1>')
    out.append('<div class="tabs">')
    for i, track in enumerate(rncp_data["rncp"]):
        active = "active" if i == 0 else ""
        out.append(f'<button class="{active}" onclick="showTrack({i})">{track["title"]}</button>')
    out.append('</div>')
    out.append('</header>')
    
    # Summary cards
    total_proj = len(set().union(*[set(opt["projects"]) for track in rncp_data["rncp"] for opt in track["options"]]))
    total_xp = sum(proj_map[pid]["difficulty"] for pid in all_ids if pid in proj_map)
    out.append('<section>')
    out.append(f'<h2><span class="g" style="background:#4a9eff"></span> Overview</h2>')
    out.append('<div class="summary">')
    out.append(f'<div class="card"><div class="v">{total_proj}</div><div class="l">Projects</div></div>')
    out.append(f'<div class="card"><div class="v">{len(rncp_data["rncp"])}</div><div class="l">RNCP Tracks</div></div>')
    out.append(f'<div class="card"><div class="v">{len([x for x in group_sets])}</div><div class="l">Total Options</div></div>')
    out.append(f'<div class="card"><div class="v">{len(suite_ids)}</div><div class="l">Shared Projects</div></div>')
    out.append(f'<div class="card"><div class="v">4</div><div class="l">Possible Combinations</div></div>')
    out.append('</div>')
    
    # Legend
    out.append('<div class="legend">')
    out.append('<span><span class="dot" style="background:#4a9eff"></span> In this option</span>')
    out.append('<span><span class="dot" style="background:#303040"></span> Not included</span>')
    out.append('<span><span class="badge">dependency</span> = prerequisite</span>')
    out.append('<span><span class="tag tag-exam">exam</span></span>')
    out.append('<span><span class="tag tag-shared">shared</span></span>')
    out.append('</div>')
    out.append('</section>')
    
    # Comparison Matrix
    out.append('<section>')
    out.append('<h2><span class="g" style="background:#606080"></span> Comparison Matrix</h2>')
    
    # Matrix legend
    out.append('<div style="margin-bottom:6px;font-size:10px;color:#505060">')
    out.append('Green ✓ = project included in this option | — = not in this option')
    out.append('</div>')
    
    out.append('<div class="matrix"><table><thead><tr>')
    out.append('<th class="col-name" style="min-width:140px">Project</th>')
    out.append('<th style="width:60px">XP</th>')
    for label, _, _ in group_sets:
        out.append(f'<th>{html.escape(label)}</th>')
    out.append('</tr></thead><tbody>')
    
    for row in comp_rows:
        xp = fmt_xp(row["xp"])
        out.append('<tr>')
        out.append(f'<td class="col-name">{html.escape(row["name"])}</td>')
        out.append(f'<td class="meta">{xp}</td>')
        for j, p in enumerate(row["presence"]):
            cls = "yes" if p == "✓" else "no"
            out.append(f'<td class="{cls}">{p}</td>')
        out.append('</tr>')
    out.append('</tbody></table></div>')
    out.append('</section>')
    
    # Combination Comparison (Best vs 2nd Best)
    if combo_rows:
        out.append('<section>')
        out.append('<h2><span class="g" style="background:#ff6060"></span> Meilleure vs 2e Combinaison</h2>')
        out.append('<div style="margin-bottom:6px;font-size:10px;color:#505060">')
        out.append('✓ = inclut ce projet | — = ne l\'inclut pas')
        out.append('</div>')
        out.append('<table style="width:100%;border-collapse:collapse;font-size:11px;border:1px solid #1a1a2e;border-radius:4px;overflow:hidden">')
        out.append('<thead><tr style="background:#14141f">')
        out.append('<th style="padding:4px 8px;text-align:left;color:#606080;border-bottom:1px solid #1a1a2e">Projet</th>')
        out.append('<th style="padding:4px 8px;text-align:center;color:#606080;border-bottom:1px solid #1a1a2e">Meilleure</th>')
        out.append('<th style="padding:4px 8px;text-align:center;color:#606080;border-bottom:1px solid #1a1a2e">2e Combinaison</th>')
        out.append('<th style="padding:4px 8px;text-align:center;color:#606080;border-bottom:1px solid #1a1a2e">Commentaire</th>')
        out.append('</tr></thead><tbody>')
        for row in combo_rows:
            out.append(f'<tr style="border-bottom:1px solid #14141f">')
            out.append(f'<td style="padding:3px 8px;color:#b0b0c0;font-weight:500">{html.escape(row["name"])}</td>')
            out.append(f'<td style="padding:3px 8px;text-align:center">{row["in_best"]}</td>')
            out.append(f'<td style="padding:3px 8px;text-align:center">{row["in_second"]}</td>')
            out.append(f'<td style="padding:3px 8px;text-align:center;color:#8080a0;font-size:10px">{row["comment"]}</td>')
            out.append('</tr>')
        out.append('</tbody></table>')
        out.append('</section>')
    
    # Project lists per track (with tabs)
    for ti, track in enumerate(rncp_data["rncp"]):
        out.append(f'<section id="track-{ti}" style="display:{"block" if ti==0 else "none"}">')
        out.append(f'<h2>{html.escape(track["title"])} — Option Detail</h2>')
        
        for oi, opt in enumerate(track["options"]):
            opt_ids = opt["projects"]
            out.append('<div class="projs" style="margin-bottom:8px">')
            out.append('<table><thead><tr>')
            out.append('<th style="min-width:120px">Project</th>')
            out.append('<th style="width:60px">XP</th>')
            out.append('<th style="width:50px">Dur</th>')
            out.append('<th>Deps (bricoles)</th>')
            out.append('<th>Type</th>')
            out.append('</tr></thead><tbody>')
            
            # Sort by XP descending (most important first)
            sorted_ids = sorted(opt_ids, key=lambda pid: proj_map.get(pid, {}).get("difficulty", 0), reverse=True)
            
            for pid in sorted_ids:
                p = proj_map.get(pid, {"name": "??", "difficulty": 0, "duration": 0, "exam": False})
                name = p["name"]
                deps = get_deps(pid)
                dep_html = "".join(badge(d) for d in deps[:3])
                if len(deps) > 3:
                    dep_html += f'<span class="badge more">+{len(deps)-3} more</span>'
                
                # Determine type tags
                tags = []
                if name in ["Work Experience I", "Work Experience II", "Part-Time I", "Part-Time II", "Startup Experience"]:
                    tags.append('<span class="tag tag-exp">exp</span>')
                elif p.get("exam"):
                    tags.append('<span class="tag tag-exam">exam</span>')
                else:
                    tags.append('<span class="tag tag-norm">cursus</span>')
                
                # Check if shared (in suite)
                if pid in suite_ids:
                    tags.append('<span class="tag tag-shared">shared</span>')
                
                tags_html = " ".join(tags)
                
                out.append(f'<tr>'
                f'<td class="name">{html.escape(name)}</td>'
                f'<td class="meta">{fmt_xp(p.get("difficulty", 0))}</td>'
                f'<td class="meta">{fmt_dur(p.get("duration", 0))}</td>'
                f'<td class="deps">{dep_html}</td>'
                f'<td>{tags_html}</td>'
                f'</tr>')
            
            out.append('</tbody></table>')
            out.append(f'<div style="background:#14141f;padding:3px 8px;font-size:10px;color:#505060;border-top:1px solid #1a1a2e">')
            total_xp = sum(proj_map.get(pid, {}).get("difficulty", 0) for pid in opt_ids)
            out.append(f'{opt["title"]}: {len(opt_ids)} projects • {fmt_xp(total_xp)} XP • {opt.get("experience", 42000)//1000}k req • min {opt.get("number_of_projects", 0)} projects</div>')
            out.append('</div>')
        
        out.append('</section>')
    
    # JS for tab switching
    out.append(f'''<script>
function showTrack(i) {{
  document.querySelectorAll('section[id^="track-"]').forEach((s,idx) => {{
    s.style.display = idx === i ? '' : 'none';
  }});
  document.querySelectorAll('.tabs button').forEach((b,idx) => {{
    b.classList.toggle('active', idx === i);
  }});
}}
</script>''')
    
    out.append('</body></html>')
    
    html_content = "\n".join(out)
    outpath = os.path.join(SCRIPT_DIR, "rncp-final.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {outpath} ({len(html_content)} chars)")

if __name__ == "__main__":
    generate_html()
