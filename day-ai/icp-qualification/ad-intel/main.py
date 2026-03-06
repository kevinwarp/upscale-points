import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from orchestrator import run_pipeline
from utils.json_formatter import print_summary, save_report


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

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    headless = not args.no_headless

    # Run the async pipeline
    report = asyncio.run(
        run_pipeline(
            domain=args.domain,
            headless=headless,
        )
    )

    # Display summary
    print_summary(report)

    # Save JSON if requested
    if args.save_json:
        filepath = save_report(report, filename=args.output)
        print(f"Report saved to: {filepath}")

    # Exit code: 0 if any ads found, 1 if none
    sys.exit(0 if report.running_any_ads else 1)


if __name__ == "__main__":
    main()
