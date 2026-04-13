import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from models.ad_models import ClayEnrichment, DomainAdReport
from orchestrator import run_pipeline
from utils.call_tracker import CallTracker
from utils.json_formatter import print_summary, save_report
from utils.status_reporter import StatusReporter
from scoring.upscale_fit import calculate_upscale_fit
from reports.publisher import publish_reports
from utils.slack_delivery import build_slack_messages, post_to_slack


def _merge_clay_data(report: DomainAdReport, clay_path: str) -> None:
    """Load Clay MCP enrichment from a JSON file and merge into the report.

    Expected JSON format (from Clay find-and-enrich-company):
    {
        "logo_url": "...",
        "headquarters": "Montclair, NJ",
        "competitors": ["Ilia", "Kosas", "RMS Beauty"],
        "revenue_model": "DTC eCommerce",
        "target_audience": "Women 25-55...",
        "founders": ["Bobbi Brown"],
        "investors": ["Sequoia"],
        "latest_funding": "Series B - $15M",
        "headcount_growth": "12%",
        "recent_news": ["Launched new product line..."],
        "raw_data": { ... }
    }
    """
    path = Path(clay_path)
    if not path.exists():
        logging.warning(f"Clay JSON file not found: {clay_path}")
        return

    data = json.loads(path.read_text(encoding="utf-8"))

    report.clay = ClayEnrichment(
        enriched=True,
        logo_url=data.get("logo_url"),
        headquarters=data.get("headquarters"),
        competitors=data.get("competitors", []),
        revenue_model=data.get("revenue_model"),
        target_audience=data.get("target_audience"),
        founders=data.get("founders", []),
        investors=data.get("investors", []),
        latest_funding=data.get("latest_funding"),
        headcount_growth=data.get("headcount_growth"),
        recent_news=data.get("recent_news", []),
        raw_data=data.get("raw_data"),
    )

    # Also merge key Clay fields into brand_intel for backward compatibility
    intel = report.brand_intel
    if report.clay.logo_url:
        intel.logo_url = report.clay.logo_url
    if report.clay.headquarters:
        intel.headquarters = report.clay.headquarters
    if report.clay.competitors:
        intel.competitors = report.clay.competitors
    if report.clay.target_audience:
        intel.target_audience = report.clay.target_audience
    if report.clay.founders:
        intel.founders = report.clay.founders
    if report.clay.investors:
        intel.investors = report.clay.investors
    if report.clay.latest_funding:
        intel.total_funding = report.clay.latest_funding

    logging.info(f"Clay data merged: {len(report.clay.competitors)} competitors, "
                 f"{len(report.clay.founders)} founders, HQ={report.clay.headquarters}")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Ad Intelligence Pipeline — scrape ad data for a domain",
    )
    parser.add_argument(
        "--domain",
        "-d",
        required=True,
        help="Domain to analyze (e.g. brand.com)",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save report to output/reports/{domain}.json",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in headful (visible) mode for debugging",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Custom output filename (overrides default)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Generate internal ICP + pitch HTML reports and upload to upscale-reports platform",
    )
    parser.add_argument(
        "--reports-only",
        action="store_true",
        help="Generate HTML reports locally without uploading (no API key needed)",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Print Upscale Fit score breakdown",
    )
    parser.add_argument(
        "--clay-json",
        type=str,
        default=None,
        help="Path to Clay MCP enrichment JSON file to override auto-fetched Clay data",
    )
    parser.add_argument(
        "--from-report",
        type=str,
        default=None,
        help="Load an existing JSON report instead of running the pipeline (for re-generating reports with Clay data)",
    )
    parser.add_argument(
        "--status-dir",
        type=str,
        default=None,
        help="Directory for real-time status JSONL files (default: output/status/)",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    headless = not args.no_headless

    # Initialize status reporter
    status = StatusReporter(args.domain, output_dir=args.status_dir)

    call_tracker = CallTracker(domain=args.domain)

    if args.from_report:
        # Load existing report instead of running pipeline
        report_path = Path(args.from_report)
        if not report_path.exists():
            print(f"Error: report file not found: {args.from_report}")
            sys.exit(1)
        status.pipeline_start(f"Loading existing report for {args.domain}")
        status.step_start("load_report", f"Loading {report_path.name}...", progress=5)
        report = DomainAdReport.model_validate_json(report_path.read_text(encoding="utf-8"))
        status.step_complete("load_report", f"Report loaded: {report.company_name or report.domain}", progress=10)
    else:
        # Run the async pipeline
        report, call_tracker = asyncio.run(
            run_pipeline(
                domain=args.domain,
                headless=headless,
                status=status,
            )
        )

    # Merge Clay data from file if provided (overrides auto-fetched Clay data)
    if args.clay_json:
        status.clay_start()
        logging.info("Overriding auto-fetched Clay data with --clay-json file")
        _merge_clay_data(report, args.clay_json)
        status.clay_complete(data={
            "competitors": report.clay.competitors,
            "founders": report.clay.founders,
            "headquarters": report.clay.headquarters,
            "revenue_model": report.clay.revenue_model,
        })

    # Display summary
    print_summary(report)

    # Save JSON if requested
    if args.save_json:
        filepath = save_report(report, filename=args.output)
        print(f"Report saved to: {filepath}")

    # Upscale Fit scoring
    if args.score or args.publish or args.reports_only:
        status.step_start("scoring", "Calculating Upscale Fit score...", progress=75)
        fit = calculate_upscale_fit(report)
        status.step_complete("scoring", f"Fit Score: {fit.total_score}/100 ({fit.grade})", progress=78, data={
            "score": fit.total_score,
            "grade": fit.grade,
        })
        print(f"\n{'=' * 60}")
        print(f"  Upscale Fit Score: {fit.total_score}/100 (Grade: {fit.grade})")
        print(f"{'=' * 60}")
        for cat in fit.categories:
            print(f"  {cat.name:25s}  {cat.score:5.0f} x {cat.weight:.0%} = {cat.weighted:5.1f}")
            for note in cat.notes:
                print(f"    * {note}")
        print(f"\n  Recommendation: {fit.recommendation}")
        print(f"{'=' * 60}\n")

    # Generate and/or publish reports
    if args.publish or args.reports_only:
        status.reports_start()
        result = asyncio.run(
            publish_reports(
                report,
                upload=args.publish,
                save_local=True,
            )
        )

        internal_url = result.internal.share_url if result.internal else None
        pitch_url = result.pitch.share_url if result.pitch else None
        status.reports_complete(internal_url=internal_url, pitch_url=pitch_url)

        if result.internal:
            print(f"\n  Internal ICP Report:")
            print(f"    URL: {result.internal.url}")
            print(f"    Passcode: {result.internal.passcode}")
            print(f"    Share: {result.internal.share_url}")
        if result.pitch:
            print(f"\n  Pitch Report:")
            print(f"    URL: {result.pitch.url}")
            print(f"    Passcode: {result.pitch.passcode}")
            print(f"    Share: {result.pitch.share_url}")
        if not result.internal and not result.pitch and not args.reports_only:
            print("\n  Reports generated locally but upload skipped (no API key?)")
        if result.error:
            print(f"\n  Errors: {result.error}")

        # Post to Slack when publishing
        if args.publish:
            try:
                status.step_start("slack", "Posting to Slack...", progress=95)
                slack_main, slack_threads = build_slack_messages(
                    report, fit,
                    internal_url=internal_url,
                    pitch_url=pitch_url,
                    call_tracker=call_tracker,
                    pitch_failed_sections=result.pitch_failed_sections if result.pitch_failed_sections else None,
                )
                slack_url = asyncio.run(post_to_slack(slack_main, slack_threads))
                if slack_url:
                    status.step_complete("slack", f"Posted to Slack", progress=98, data={"url": slack_url})
                    print(f"\n  Slack: {slack_url}")
                else:
                    status.step_complete("slack", "Slack delivery skipped (no bot token)", progress=98)
            except Exception as e:
                logging.warning(f"Slack delivery failed: {e}")
                status.step_complete("slack", f"Slack delivery failed: {e}", progress=98)

        # Final pipeline complete status
        status.pipeline_complete(
            fit_score=fit.total_score,
            fit_grade=fit.grade,
            internal_url=internal_url,
            pitch_url=pitch_url,
        )
    else:
        status.pipeline_complete()

    # Also save JSON after Clay merge if requested
    if args.save_json and args.clay_json:
        filepath = save_report(report, filename=args.output)
        print(f"Report (with Clay) saved to: {filepath}")

    # Exit code: 0 if any ads found, 1 if none
    sys.exit(0 if report.running_any_ads else 1)


if __name__ == "__main__":
    main()
