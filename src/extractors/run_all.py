"""Orchestrator: run all extractors then all seeders."""

import sys
from pathlib import Path

from src.config import SEED_DIR, USER_RESOURCES_DIR


def run_extractors(source_dir: Path | None = None, output_dir: Path | None = None) -> dict[str, int]:
    """Run all extractors to produce JSON files. Returns {filename: count}."""
    from src.extractors.casestudy_extractor import CasestudyExtractor
    from src.extractors.market_pass_extractor import MarketPassExtractor
    from src.extractors.price_pass_extractor import PricePassExtractor

    source_dir = source_dir or (USER_RESOURCES_DIR / "D_colect" / "extracted")
    output_dir = output_dir or (SEED_DIR / "extracted")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results: dict[str, int] = {}

    extractors = [
        ("Case Study", CasestudyExtractor),
        ("Market Passes", MarketPassExtractor),
        ("Price Analysis", PricePassExtractor),
    ]

    for name, extractor_class in extractors:
        print(f"Extracting {name}...", end=" ")
        try:
            extractor = extractor_class(source_dir, output_dir)
            results = extractor.extract()
            total = sum(results.values())
            print(f"{total} records across {len(results)} files.")
            all_results.update(results)
        except FileNotFoundError as e:
            print(f"Skipped ({e})")
        except Exception as e:
            print(f"Error: {e}")
            raise

    print(f"\nExtraction complete. Total: {sum(all_results.values())} records.")
    return all_results


def run_all() -> dict[str, int]:
    """Run full pipeline: extract → seed."""
    print("=" * 60)
    print("Phase 1: Extract source text → JSON")
    print("=" * 60)
    extract_results = run_extractors()

    print()
    print("=" * 60)
    print("Phase 2: Seed JSON → Database")
    print("=" * 60)
    from src.seeders.run_all import run_all as run_seeders
    seed_results = run_seeders()

    return {**extract_results, **seed_results}


if __name__ == "__main__":
    run_all()
