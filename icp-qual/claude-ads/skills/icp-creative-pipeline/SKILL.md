---
name: icp-creative-pipeline
description: "Shows the AI-generated creative pipeline: brand brief, production script (scene-by-scene with visual/VO/copy breakdowns), voiceover demos, scene images, video previews, and downloadable assets (DOCX/ZIP). Use to review or share creative output for a prospect."
user-invokable: false
---

# Creative Pipeline

## Prerequisites

See `_lib/report-loader.md` for how to load the report JSON.

## Data Sources

| Report Field | What It Provides |
|---|---|
| `report.creative_pipeline` | Status, brand brief, script, images, videos, documents |
| `report.audio_files[]` | AI voiceover demos (ElevenLabs) |
| `report.company_name` | Brand name for personalization |

### Key Sub-fields

**creative_pipeline:**
- `found`: boolean
- `status`: pipeline completion status
- `brand_brief`: markdown brand intelligence brief
- `script`: raw production script text
- `image_urls[]`: scene still images
- `video_urls[]`: rendered video previews
- `docx_url`: downloadable Word document
- `zip_url`: downloadable asset package
- `job_id`: pipeline job identifier
- `elapsed_seconds`: generation time

**audio_files[]:**
- `voice`: voice name/style
- `script`: VO script text
- `url`: audio file URL
- `voice_id`: ElevenLabs voice ID

## Process

1. **Load report** for the given domain
2. **Status badge**: show pipeline completion status
3. **Brand brief**: render markdown to formatted text
4. **Production script**: parse into scenes by detecting "SCENE N" headings
5. **Per scene**: separate Visual, VO, On-Screen Copy, and Notes sections
6. **Voiceover demos**: audio players for each voice with script text
7. **Scene images**: grid of AI-generated scene stills
8. **Video previews**: embedded video players
9. **Download links**: DOCX and ZIP asset packages

### Script Parsing Logic

The raw script is split into scenes by detecting `SCENE N` headings. Within each scene:
- Lines starting with `VISUAL:` → visual direction
- Lines starting with `VO:` → voiceover copy
- Lines starting with `ON-SCREEN:` or `COPY:` → on-screen text
- Lines starting with `NOTE:` → production notes
- Duration extracted from `DURATION:` lines

## Output

```markdown
## Creative Pipeline — {company_name}

**Status:** {status} | Generated in {elapsed}s

### Brand Brief
{brief_content}

### Production Script
#### Scene 1 — {duration}
**Visual:** {description}
**VO:** "{voiceover_text}"
**On-Screen:** {copy}

#### Scene 2 — {duration}
...

### Voiceover Demos
- {voice_name}: [Play]({url})
  "{script_text}"

### Scene Images
{image_grid}

### Downloads
- [Brand Brief (DOCX)]({docx_url})
- [Full Asset Package (ZIP)]({zip_url})
```

## Notes

- Script may contain markdown formatting (bold, italic) — strip `**` artifacts in output
- Duration badges should be clean: "0-5 seconds", "5-10 seconds"
- Images are AI-generated scene stills, not final production assets
