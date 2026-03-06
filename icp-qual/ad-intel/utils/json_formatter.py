import sys
from pathlib import Path

# Ensure ad-intel root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.ad_models import DomainAdReport

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "reports"


def save_report(report: DomainAdReport, filename: str | None = None) -> Path:
    """Save a DomainAdReport as JSON to the output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = filename or f"{report.domain}.json"
    filepath = OUTPUT_DIR / fname
    filepath.write_text(
        report.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )
    return filepath


def print_summary(report: DomainAdReport) -> None:
    """Print a human-readable summary of the ad intelligence report."""
    print(f"\n{'=' * 60}")
    print(f"  Ad Intelligence Report: {report.domain}")
    print(f"  Company: {report.company_name or 'Unknown'}")
    print(f"{'=' * 60}")
    for label, result in [
        ("iSpot (Linear)", report.ispot_ads),
        ("YouTube", report.youtube_ads),
        ("Meta", report.meta_ads),
    ]:
        status = "FOUND" if result.found else "NOT FOUND"
        count = len(result.ads)
        duration = f" ({result.scrape_duration_seconds}s)" if result.scrape_duration_seconds else ""
        print(f"  {label:20s}: {status} ({count} ads){duration}")
        if result.error:
            print(f"    Error: {result.error}")
    print(f"  Running any ads: {report.running_any_ads}")
    print(f"  Channel mix: {report.channel_mix.total_platforms} platforms, {report.channel_mix.total_ads_found} total ads")
    if report.pipeline_duration_seconds:
        print(f"  Pipeline time: {report.pipeline_duration_seconds}s")
    print(f"{'=' * 60}\n")
