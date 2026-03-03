"""CLI entry point for the BDS web scraping system.

Usage:
    python -m src.scrapers.cli_scrape projects --city hcmc
    python -m src.scrapers.cli_scrape listings --project "vinhomes-grand-park"
    python -m src.scrapers.cli_scrape office --city hcmc --max-pages 10
    python -m src.scrapers.cli_scrape status
    python -m src.scrapers.cli_scrape promote --job-id 5 --period-id 1
    python -m src.scrapers.cli_scrape promote --job-id 5 --period-id 1 --type office
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone

from src.collectors.cli_utils import (
    Colors,
    format_duration,
    format_timestamp,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
    print_table,
    print_warning,
)
from src.db.connection import get_session
from src.db.models import ScrapeJob, ScrapedListing
from src.scrapers.browser import BrowserManager
from src.scrapers.config import BDS_BASE_URL, BDS_OFFICE_LEASE_URL, CITY_SLUGS
from src.scrapers.listing_scraper import ListingScraper
from src.scrapers.office_pipeline import OfficePipeline
from src.scrapers.office_scraper import OfficeScraper
from src.scrapers.pipeline import ScrapePipeline
from src.scrapers.project_list_scraper import ProjectListScraper
from src.scrapers.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


async def cmd_scrape_projects(args: argparse.Namespace) -> None:
    """Scrape project listings from BDS."""
    print_header("BDS Project Scraper")
    city = args.city
    max_pages = args.max_pages

    if city not in CITY_SLUGS:
        print_error(f"Unknown city: {city}. Available: {', '.join(CITY_SLUGS)}")
        return

    print_info(f"City: {city} ({CITY_SLUGS[city]})")
    print_info(f"Max pages: {max_pages}")

    session = get_session()
    pipeline = ScrapePipeline(session)
    rate_limiter = RateLimiter()

    job = pipeline.create_job(
        job_type="project_list",
        target_url=f"{BDS_BASE_URL}/ban-can-ho-chung-cu-{CITY_SLUGS[city]}",
    )
    session.commit()
    print_info(f"Created scrape job #{job.id}")

    try:
        async with BrowserManager(headless=not args.headed) as browser:
            scraper = ProjectListScraper(
                browser=browser,
                rate_limiter=rate_limiter,
                city=city,
                max_pages=max_pages,
            )
            raw_items = await scraper.scrape()

        print_info(f"Found {len(raw_items)} items")

        valid_count, saved_count = pipeline.process_listings(raw_items, job)
        result = pipeline.complete_job(job, len(raw_items), saved_count)
        session.commit()

        print_success(f"Job #{job.id} completed")
        print_info(f"Items found: {result.items_found}")
        print_info(f"Items saved: {result.items_saved}")
        if result.duration_sec:
            print_info(f"Duration: {format_duration(result.duration_sec)}")

        if scraper.errors:
            print_warning(scraper.get_error_summary())

    except Exception as e:
        pipeline.complete_job(job, 0, 0, str(e))
        session.commit()
        print_error(f"Scrape failed: {e}")
    finally:
        session.close()


async def cmd_scrape_listings(args: argparse.Namespace) -> None:
    """Scrape listings for a specific project."""
    print_header("BDS Listing Scraper")
    project_slug = args.project
    max_pages = args.max_pages

    search_url = f"{BDS_BASE_URL}/ban-can-ho-chung-cu-{project_slug}"
    print_info(f"Project: {project_slug}")
    print_info(f"URL: {search_url}")

    session = get_session()
    pipeline = ScrapePipeline(session)
    rate_limiter = RateLimiter()

    job = pipeline.create_job(job_type="listing", target_url=search_url)
    session.commit()
    print_info(f"Created scrape job #{job.id}")

    try:
        async with BrowserManager(headless=not args.headed) as browser:
            scraper = ListingScraper(
                browser=browser,
                rate_limiter=rate_limiter,
                search_url=search_url,
                max_pages=max_pages,
            )
            raw_items = await scraper.scrape()

        print_info(f"Found {len(raw_items)} listings")

        valid_count, saved_count = pipeline.process_listings(raw_items, job)
        result = pipeline.complete_job(job, len(raw_items), saved_count)
        session.commit()

        print_success(f"Job #{job.id} completed")
        print_info(f"Listings found: {result.items_found}")
        print_info(f"Listings saved: {result.items_saved}")
        if result.duration_sec:
            print_info(f"Duration: {format_duration(result.duration_sec)}")

    except Exception as e:
        pipeline.complete_job(job, 0, 0, str(e))
        session.commit()
        print_error(f"Scrape failed: {e}")
    finally:
        session.close()


async def cmd_scrape_office(args: argparse.Namespace) -> None:
    """Scrape office lease listings from batdongsan.com.vn."""
    print_header("BDS Office Lease Scraper")
    city = args.city
    max_pages = args.max_pages

    if city not in CITY_SLUGS:
        print_error(f"Unknown city: {city}. Available: {', '.join(CITY_SLUGS)}")
        return

    target_url = BDS_OFFICE_LEASE_URL.format(city_slug=CITY_SLUGS[city])
    print_info(f"City: {city} ({CITY_SLUGS[city]})")
    print_info(f"URL: {target_url}")
    print_info(f"Max pages: {max_pages}")

    session = get_session()
    pipeline = OfficePipeline(session)
    rate_limiter = RateLimiter()

    job = pipeline.create_job(target_url=target_url)
    session.commit()
    print_info(f"Created scrape job #{job.id} (office_listing)")

    try:
        async with BrowserManager(headless=not args.headed) as browser:
            scraper = OfficeScraper(
                browser=browser,
                rate_limiter=rate_limiter,
                city=city,
                max_pages=max_pages,
            )
            raw_items = await scraper.scrape()

        print_info(f"Found {len(raw_items)} items")

        valid_count, saved_count = pipeline.process_listings(raw_items, job)
        result = pipeline.complete_job(job, len(raw_items), saved_count)
        session.commit()

        print_success(f"Job #{job.id} completed")
        print_info(f"Items found: {result.items_found}")
        print_info(f"Items saved to staging: {result.items_saved}")

        # Show matching stats
        from src.db.models import ScrapedOfficeListing
        matched = (
            session.query(ScrapedOfficeListing)
            .filter(
                ScrapedOfficeListing.scrape_job_id == job.id,
                ScrapedOfficeListing.matched_office_project_id.isnot(None),
            )
            .count()
        )
        print_info(f"Matched to office projects: {matched}/{saved_count}")

        if result.duration_sec:
            print_info(f"Duration: {format_duration(result.duration_sec)}")

        if scraper.errors:
            print_warning(scraper.get_error_summary())

    except Exception as e:
        pipeline.complete_job(job, 0, 0, str(e))
        session.commit()
        print_error(f"Office scrape failed: {e}")
    finally:
        session.close()


def cmd_status(args: argparse.Namespace) -> None:
    """Show scrape job history."""
    print_header("Scrape Job History")

    session = get_session()
    try:
        jobs = (
            session.query(ScrapeJob)
            .order_by(ScrapeJob.id.desc())
            .limit(args.limit)
            .all()
        )

        if not jobs:
            print_info("No scrape jobs found.")
            return

        headers = ["ID", "Type", "Status", "Found", "Saved", "Started", "Duration"]
        rows = []
        for job in jobs:
            duration = ""
            if job.started_at and job.completed_at:
                secs = (job.completed_at - job.started_at).total_seconds()
                duration = format_duration(secs)

            rows.append([
                str(job.id),
                job.job_type,
                job.status,
                str(job.items_found or 0),
                str(job.items_saved or 0),
                format_timestamp(job.started_at),
                duration,
            ])

        print_table(headers, rows)

        # Show matched vs unmatched stats
        print_section("Matching Stats")
        total = session.query(ScrapedListing).count()
        matched = session.query(ScrapedListing).filter(
            ScrapedListing.matched_project_id.isnot(None)
        ).count()
        promoted = session.query(ScrapedListing).filter(
            ScrapedListing.promoted == True  # noqa: E712
        ).count()

        print_info(f"Total staged listings: {total}")
        print_info(f"Matched to projects: {matched}")
        print_info(f"Promoted to price_records: {promoted}")

    finally:
        session.close()


def cmd_promote(args: argparse.Namespace) -> None:
    """Promote staged listings to price_records or office_leasing_records."""
    promote_type = getattr(args, "type", "residential")
    print_header(f"Promote Staged Listings ({promote_type})")

    session = get_session()
    try:
        job = session.get(ScrapeJob, args.job_id)
        if not job:
            print_error(f"Job #{args.job_id} not found")
            return

        print_info(f"Job #{job.id}: {job.job_type} ({job.status})")

        if promote_type == "office":
            from src.db.models import ScrapedOfficeListing
            eligible = (
                session.query(ScrapedOfficeListing)
                .filter(
                    ScrapedOfficeListing.scrape_job_id == args.job_id,
                    ScrapedOfficeListing.matched_office_project_id.isnot(None),
                    ScrapedOfficeListing.promoted == False,  # noqa: E712
                )
                .count()
            )

            if eligible == 0:
                print_warning("No eligible office listings to promote")
                return

            print_info(f"Eligible office listings: {eligible}")

            pipeline = OfficePipeline(session)
            summary = pipeline.promote_job(args.job_id, args.period_id)
            print_success(f"Promoted {summary['promoted']} listings to office_leasing_records")
            if summary["skipped_no_match"]:
                print_warning(f"{summary['skipped_no_match']} skipped (no matching office project)")
            if summary["skipped_no_price"]:
                print_warning(f"{summary['skipped_no_price']} skipped (no rent data)")
            if summary["skipped_duplicate"]:
                print_info(f"{summary['skipped_duplicate']} skipped (already promoted)")

        else:
            # Residential promote
            eligible = (
                session.query(ScrapedListing)
                .filter(
                    ScrapedListing.scrape_job_id == args.job_id,
                    ScrapedListing.matched_project_id.isnot(None),
                    ScrapedListing.price_per_sqm.isnot(None),
                    ScrapedListing.promoted == False,  # noqa: E712
                )
                .count()
            )

            if eligible == 0:
                print_warning("No eligible listings to promote")
                return

            print_info(f"Eligible listings: {eligible}")

            pipeline = ScrapePipeline(session)
            report = pipeline.promote_job(args.job_id, args.period_id)
            print_success(f"Promoted {report.promoted} listings to price_records")
            if report.conflicted:
                print_warning(
                    f"{report.conflicted} listings held (BDS vs NHO price conflict > 15%)"
                )
            if report.anomalous:
                print_warning(
                    f"{report.anomalous} listings promoted with anomaly flag (> 2.5σ from batch mean)"
                )
            if report.total_flagged:
                print(report.summary())

    finally:
        session.close()


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="bds-scraper",
        description="BatDongSan.com.vn web scraper for real estate data",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # projects command
    p_projects = subparsers.add_parser("projects", help="Scrape project listings")
    p_projects.add_argument(
        "--city", default="hcmc", choices=list(CITY_SLUGS.keys()),
        help="City to scrape (default: hcmc)",
    )
    p_projects.add_argument(
        "--max-pages", type=int, default=5, help="Max pages to scrape (default: 5)"
    )
    p_projects.add_argument(
        "--headed", action="store_true", help="Run browser in headed mode"
    )

    # listings command
    p_listings = subparsers.add_parser("listings", help="Scrape unit listings")
    p_listings.add_argument(
        "--project", required=True, help="Project slug (e.g., vinhomes-grand-park)"
    )
    p_listings.add_argument(
        "--max-pages", type=int, default=5, help="Max pages to scrape (default: 5)"
    )
    p_listings.add_argument(
        "--headed", action="store_true", help="Run browser in headed mode"
    )

    # status command
    p_status = subparsers.add_parser("status", help="Show scrape job history")
    p_status.add_argument(
        "--limit", type=int, default=20, help="Max jobs to show (default: 20)"
    )

    # office command
    p_office = subparsers.add_parser("office", help="Scrape office lease listings")
    p_office.add_argument(
        "--city", default="hcmc", choices=list(CITY_SLUGS.keys()),
        help="City to scrape (default: hcmc)",
    )
    p_office.add_argument(
        "--max-pages", type=int, default=10, help="Max pages to scrape (default: 10)"
    )
    p_office.add_argument(
        "--headed", action="store_true", help="Run browser in headed mode"
    )

    # promote command
    p_promote = subparsers.add_parser("promote", help="Promote staged data to price_records")
    p_promote.add_argument(
        "--job-id", type=int, required=True, help="Scrape job ID to promote"
    )
    p_promote.add_argument(
        "--period-id", type=int, required=True, help="Report period ID for promoted records"
    )
    p_promote.add_argument(
        "--type", default="residential", choices=["residential", "office"],
        help="Data type to promote (default: residential)",
    )

    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.command == "projects":
        asyncio.run(cmd_scrape_projects(args))
    elif args.command == "listings":
        asyncio.run(cmd_scrape_listings(args))
    elif args.command == "office":
        asyncio.run(cmd_scrape_office(args))
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "promote":
        cmd_promote(args)


if __name__ == "__main__":
    main()
