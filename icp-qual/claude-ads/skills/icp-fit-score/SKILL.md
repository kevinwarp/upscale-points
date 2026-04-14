---
name: icp-fit-score
description: "Calculates and displays the Upscale Fit Score: total score (0-100), grade (A-F), recommendation text, and per-category breakdown with weighted score bars and notes. Uses the scoring.upscale_fit module. Use for qualification decisions and pipeline routing."
user-invokable: false
---

# Upscale Fit Score

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON and fit score.

## Data Sources

| Source | What It Provides |
|---|---|
| `fit.grade` | A-F overall grade |
| `fit.total_score` | 0-100 numeric score |
| `fit.recommendation` | Qualification recommendation text |
| `fit.categories[]` | Per-category breakdown |

### Category Fields

Each category in `fit.categories[]`:
- `name`: category label (e.g., "Revenue Scale", "Digital Maturity")
- `weight`: percentage weight in total score (e.g., 0.25 = 25%)
- `score`: 0-100 score for this category
- `notes[]`: explanatory bullets for the score

## Fit Score Calculation

```python
from scoring.upscale_fit import calculate_upscale_fit
fit = calculate_upscale_fit(report)
```

## Process

1. **Load report** and calculate fit score
2. **Hero ring**: large circular display with total score and grade letter
3. **Recommendation text**: qualification recommendation
4. **Category bars**: horizontal bars for each category showing:
   - Category name
   - Weight as percentage
   - Score with colored fill bar
   - Note bullets explaining the score

### Score Bar Colors

| Score Range | Color |
|------------|-------|
| 80-100 | #027A48 (green) |
| 60-79 | #0A6D86 (teal) |
| 40-59 | #B54708 (amber) |
| 0-39 | #B42318 (red) |

### Grade Scale

| Grade | Score Range |
|-------|-----------|
| A | 90-100 |
| B | 75-89 |
| C | 60-74 |
| D | 40-59 |
| F | <40 |

## Output

```markdown
## Upscale Fit Score — {company_name}

### Overall: {grade} ({score}/100)
{recommendation}

### Category Breakdown
| Category | Weight | Score | Notes |
|----------|--------|-------|-------|
| {name} | {weight}% | {score}/100 | {note} |
| ... | ... | ... | ... |
```

## Qualification Thresholds

- **A (90+)**: Tier 1 prospect — immediate outreach, personalized pitch
- **B (75-89)**: Strong fit — prioritize for outreach this quarter
- **C (60-74)**: Moderate fit — add to nurture sequence
- **D (40-59)**: Weak fit — monitor for trigger events
- **F (<40)**: Not qualified — do not pursue
