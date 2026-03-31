#!/usr/bin/env python3
"""
Equi Content Engine — Production Entry Point

Runs both workflows (or individually) with CLI arguments.

Usage:
    python run_production.py                     # Run both workflows
    python run_production.py --workflow 1         # Quick content only
    python run_production.py --workflow 2         # Video content only
    python run_production.py --dry-run            # Preview without saving
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from db import get_connection, init_db


def main():
    parser = argparse.ArgumentParser(
        description="Equi CEO Content Repurposing & Distribution Engine",
    )
    parser.add_argument(
        "--workflow", type=int, choices=[1, 2], default=None,
        help="Run specific workflow (1=quick content, 2=video content). Default: both.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview mode — generates content but doesn't save to database.",
    )
    args = parser.parse_args()

    print("\n🦞 Equi Content Engine\n")

    # Check for API key
    if config.ANTHROPIC_API_KEY:
        print(f"  Claude API: ✅ configured (model: {config.CLAUDE_MODEL})")
    else:
        print("  Claude API: ⚠️  no API key — using template fallbacks")

    # Initialize database
    conn = get_connection()
    init_db(conn)
    conn.close()
    print(f"  Database: ✅ {config.DB_PATH}")
    print(f"  Output: {config.OUTPUT_DIR}/\n")

    if args.workflow in (None, 1):
        from demo_workflow1 import run_workflow1_demo
        run_workflow1_demo()

    if args.workflow in (None, 2):
        from demo_workflow2 import run_workflow2_demo
        run_workflow2_demo()

    print("\nDone.")


if __name__ == "__main__":
    main()
