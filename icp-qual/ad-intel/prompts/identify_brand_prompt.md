# Brand Name Identification

## Resolution Order

1. **Store Leads API** — If `company_name` is returned from enrichment, use it as the primary search term
2. **Domain heuristic** — Strip TLD and convert hyphens/underscores to spaces: `acme-widgets.com` → `Acme Widgets`
3. **Manual override** — Future: accept `--brand` CLI flag to override both

## Known Challenges

- Legal entity names differ from brand names (e.g., "Nike, Inc." vs "Nike")
- Parent companies own multiple brands (e.g., "Procter & Gamble" owns "Tide")
- Some domains use abbreviations (e.g., `pg.com` for Procter & Gamble)

## Fallback Strategy

If the first search returns no results on any platform, the scrapers should retry with the domain root (e.g., `nike` from `nike.com`).
