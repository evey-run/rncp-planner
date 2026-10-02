# 42 RNCP Planner — Speedrun Edition

A minimalist, compact web app for planning 42 school RNCP paths.
Compare options across RNCP 6 (Web/Mobile vs Applicatif) and RNCP 7 (SI/Réseaux vs Data).

## Features

- **Comparison Matrix** — see which projects are in which option side-by-side
- **Inline dependency badges (bricoles)** — each project row shows its prerequisites
  and dependents inline, no separate column
- **Minimalist dark design** — everything visible on one screen
- **Kfs chain visualization** — kfs-1 → kfs-2 → ... → kfs-x dependency chain
- **Security progression** — nm → override → woody-woodpacker, snow-crash → darkly

## Regenerate

```bash
python3 gen_complete.py    # Rebuild data from Excel + GitHub API dumps
python3 gen_html.py        # Generate rncp-final.html
```

## Files

- `rncp-final.html` — the app (single file, no dependencies)
- `gen_html.py` — HTML generator
- `gen_complete.py` — data pipeline (Excel → JSON)
- `projects_data.json` — all 89 42 projects with deps
- `rncp_data.json` — RNCP track/option structure

Built with ❤️ by SHIVA
