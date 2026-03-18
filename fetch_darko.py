#!/usr/bin/env python3
"""
fetch_darko.py — Auto-download DARKO daily projections CSV

The DARKO website is a Shiny app that requires a live browser session
to generate download URLs. This script uses Playwright to:
1. Open the DARKO page in a headless browser
2. Wait for the Shiny app to initialize
3. Click the download button
4. Save the CSV with today's date

Setup (first time only):
  pip install playwright
  python -m playwright install chromium

Usage:
  python3 fetch_darko.py
  python3 fetch_darko.py --output-dir /path/to/parlaybudv3/

The output file will be named: DARKO_daily_projections_YYYY-MM-DD.csv
"""

import os
import sys
import glob
import argparse
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


DARKO_URL = "https://apanalytics.shinyapps.io/DARKO/"


def fetch_darko(output_dir: str = ".", timeout_ms: int = 60000) -> str:
    """
    Download DARKO CSV using headless Chromium.
    Returns the path to the downloaded file, or empty string on failure.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    output_name = f"DARKO_daily_projections_{today}.csv"
    output_path = os.path.join(output_dir, output_name)

    # Check if already downloaded today
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        print(f"   ✅ Already have today's DARKO: {output_name}")
        return output_path

    print(f"🌐 Fetching DARKO projections...")
    print(f"   Opening {DARKO_URL} in headless browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # Navigate to DARKO — use 'load' instead of 'networkidle'
            # Shiny apps keep a WebSocket open forever so networkidle never triggers
            page.goto(DARKO_URL, timeout=timeout_ms, wait_until="load")
            print("   ✅ Page loaded")

            # Wait for the Shiny app to fully initialize
            print("   ⏳ Waiting for Shiny app to initialize...")
            page.wait_for_timeout(10000)

            # Click the "Daily Player Per-Game Projections" tab
            print("   📑 Navigating to Daily Projections tab...")
            daily_tab = page.query_selector('a:has-text("Daily Player Per-Game Projections")')
            if not daily_tab:
                daily_tab = page.query_selector('a[href="#tab-8435-5"]')
            if daily_tab:
                daily_tab.click()
                print("   ✅ Clicked Daily Projections tab")
                page.wait_for_timeout(10000)  # Wait for table to render
            else:
                print("   ❌ Could not find Daily Projections tab")
                browser.close()
                return ""

            # Now look for the download button on this tab
            # Debug: print all links/buttons visible now
            download_btn = None

            # Try multiple selectors
            selectors = [
                'a#download_daily',
                'a[id*="download"]',
                'a.shiny-download-link',
                'button[id*="download"]',
                'a:has-text("Download")',
                'a:has-text("CSV")',
                'a:has-text("download")',
            ]

            for sel in selectors:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        download_btn = el
                        print(f"   ✅ Found download button: {sel}")
                        break
                except:
                    continue

            if not download_btn:
                # Last resort: find any link with "download" in href
                links = page.query_selector_all('a[href*="download"]')
                if links:
                    download_btn = links[0]
                    print(f"   ✅ Found download link via href")

            if not download_btn:
                print("   ❌ Could not find download button")
                # Debug: print all visible links AND buttons
                all_links = page.query_selector_all('a')
                all_buttons = page.query_selector_all('button')
                print(f"   Debug: {len(all_links)} links, {len(all_buttons)} buttons on page:")
                print("   --- Links ---")
                for link in all_links[:20]:
                    txt = (link.text_content() or '').strip()[:50]
                    href = link.get_attribute('href') or ''
                    lid = link.get_attribute('id') or ''
                    cls = link.get_attribute('class') or ''
                    if txt or 'download' in href.lower() or 'download' in lid.lower() or 'download' in cls.lower():
                        print(f"     id='{lid}' class='{cls[:40]}' text='{txt}' href='{href[:60]}'")
                print("   --- Buttons ---")
                for btn in all_buttons[:15]:
                    txt = (btn.text_content() or '').strip()[:50]
                    bid = btn.get_attribute('id') or ''
                    cls = btn.get_attribute('class') or ''
                    print(f"     id='{bid}' class='{cls[:40]}' text='{txt}'")
                browser.close()
                return ""

            # Click download and capture the file
            print("   📥 Clicking download...")
            with page.expect_download(timeout=30000) as download_info:
                download_btn.click()

            download = download_info.value
            download.save_as(output_path)

            # Verify it's a valid CSV
            size = os.path.getsize(output_path)
            if size < 500:
                print(f"   ❌ Downloaded file too small ({size} bytes)")
                os.remove(output_path)
                browser.close()
                return ""

            # Quick sanity check — should have Player column
            with open(output_path, 'r') as f:
                header = f.readline()
                if 'Player' not in header and 'player' not in header.lower():
                    print(f"   ❌ File doesn't look like DARKO CSV: {header[:100]}")
                    os.remove(output_path)
                    browser.close()
                    return ""

            # Count rows
            with open(output_path, 'r') as f:
                rows = sum(1 for _ in f) - 1  # subtract header

            print(f"   ✅ Saved: {output_name} ({rows} players, {size:,} bytes)")
            browser.close()
            return output_path

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            browser.close()
            return ""


def cleanup_old_files(output_dir: str, keep_days: int = 7):
    """Remove DARKO CSVs older than keep_days."""
    pattern = os.path.join(output_dir, "DARKO_daily_projections_*.csv")
    files = sorted(glob.glob(pattern))
    if len(files) > keep_days:
        for old in files[:-keep_days]:
            os.remove(old)
            print(f"   🗑️  Removed old: {os.path.basename(old)}")


def main():
    parser = argparse.ArgumentParser(description="Fetch DARKO daily projections")
    parser.add_argument('--output-dir', default='.', help='Directory to save CSV')
    parser.add_argument('--timeout', type=int, default=60000, help='Page load timeout (ms)')
    parser.add_argument('--cleanup', type=int, default=7, help='Keep last N days of CSVs')
    args = parser.parse_args()

    if not HAS_PLAYWRIGHT:
        print("❌ Install Playwright:")
        print("   pip install playwright")
        print("   python -m playwright install chromium")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    path = fetch_darko(args.output_dir, args.timeout)

    if path:
        cleanup_old_files(args.output_dir, args.cleanup)
        print(f"\n✅ DARKO CSV ready: {path}")
    else:
        # Check if we have yesterday's file as fallback
        pattern = os.path.join(args.output_dir, "DARKO_daily_projections_*.csv")
        files = sorted(glob.glob(pattern))
        if files:
            print(f"\n⚠️  Using most recent DARKO: {os.path.basename(files[-1])}")
        else:
            print("\n❌ No DARKO CSV available")
            sys.exit(1)


if __name__ == "__main__":
    main()
