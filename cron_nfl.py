#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NFL Automatic Daily Pipeline Script (cron_nfl.py)
Mode:
  --mode predict : Run 11.0 WUV model for 2026-27 NFL season, update nfl_data.db
  --mode score   : Fetch actual results for finished games, calculate accuracy, update nfl_data.db
"""

import sys
import argparse
import app

def main():
    parser = argparse.ArgumentParser(description="NFL Automatic Daily Pipeline Script")
    parser.add_argument("--mode", choices=["predict", "score"], default="score", help="Pipeline execution mode")
    args = parser.parse_args()

    print(f"=== [NFL PIPELINE] Running mode: {args.mode} ===")
    df = app.fetch_espn_live_data()
    print(f"Successfully processed and updated {len(df)} games into nfl_data.db!")

if __name__ == "__main__":
    main()
