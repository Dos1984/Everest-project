# Everest Prototype

A structured visit-capture app for treat-to-target (T2T) care in rheumatoid arthritis, built around the measures used in the EVEREST quality-improvement initiative. It is an independent prototype, not an AbbVie product.

**Live app:** https://dos1984.github.io/everest-project/

## What it records

Each visit is captured in five steps:

1. **Visit** – date, visit type (clinic, telehealth, nurse-led, self-report), current csDMARD / b/tsDMARD / glucocorticoid dose, adherence, side effects.
2. **Joints** – 28-joint tender and swollen count, tapped on a body figure (shoulders, elbows, wrists, knees) and the backs of both hands (MCP 1–5, PIP 1–5).
3. **Patient** – patient global, pain and fatigue (0–10), morning stiffness, HAQ-DI, flares, and what matters most to the patient.
4. **Clinician & labs** – evaluator global, CRP, ESR.
5. **Plan** – DAS28-CRP, DAS28-ESR, CDAI, SDAI and ACR/EULAR Boolean remission calculated automatically, checked against the agreed target; treatment decision, shared decision-making confirmation, next review date, notes.

Each patient has a DAS28-CRP trend chart over the disease activity bands. The Records tab lists every visit and exports the full dataset as CSV or JSON.

## Storage

- **This GitHub Pages build** saves records in the browser on the device being used (localStorage). Nothing is sent to a server. Clearing site data deletes the records, so export regularly.
- **The version hosted in Claude** saves to a shared record store for everyone the app is shared with.

Two clearly marked example patients are loaded on first use.

> Prototype only. Not a validated medical device. Do not enter identifiable patient information; use study codes.

## Score formulas

| Score | Formula | Remission | Low | Moderate | High |
|---|---|---|---|---|---|
| DAS28-CRP | 0.56√TJC + 0.28√SJC + 0.36 ln(CRP mg/L + 1) + 0.014·PtGA(0–100) + 0.96 | < 2.6 | ≤ 3.2 | ≤ 5.1 | > 5.1 |
| DAS28-ESR | 0.56√TJC + 0.28√SJC + 0.70 ln(ESR) + 0.014·PtGA(0–100) | < 2.6 | ≤ 3.2 | ≤ 5.1 | > 5.1 |
| CDAI | TJC + SJC + PtGA + EvGA (0–10) | ≤ 2.8 | ≤ 10 | ≤ 22 | > 22 |
| SDAI | CDAI + CRP (mg/dL) | ≤ 3.3 | ≤ 11 | ≤ 26 | > 26 |
| Boolean 2.0 | TJC ≤ 1, SJC ≤ 1, CRP ≤ 1 mg/dL, PtGA ≤ 2 | | | | |

## Figures

- `assets/body.png` – full-body figure (markers removed from the reference illustration).
- `assets/hands.png` – backs of both hands, rendered in Blender from the CC0 MakeHuman base mesh; joint targets come from the mesh's own finger-joint markers.
- `tools/` – the Blender and OpenCV scripts used to produce them.

The images are embedded in `index.html`, so the app is a single self-contained file.
