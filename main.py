import os
import time
import argparse
import requests
import json
import concurrent.futures
import math
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import cloudscraper
from typing import List, Dict, Any, Tuple

from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential, retry_if_exception_type, before_sleep_log
import logging
import sys

# Configure logging for tenacity
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)
from tqdm import tqdm
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

# Default Constants
BASE_URL_SAFE = "https://konachan.net/post.json"
BASE_URL_UNSAFE = "https://konachan.com/post.json"
DEFAULT_DOWNLOAD_DIR = "downloads"
DEFAULT_TIMEOUT = 10  # Seconds
MAX_WORKERS_DEFAULT = 5
STATS_FILE = "stats.json"
README_FILE = "README.md"


class DownloadError(Exception):
    pass


@retry(
    stop=stop_after_attempt(20),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((requests.RequestException, cloudscraper.exceptions.CloudflareException)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def get_total_posts(base_url: str, tags: str, page: int, limit: int = 100, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch posts from the API with robust retries.
    """
    params = {
        "tags": tags,
        "page": page,
        "limit": limit
    }
    # No internal try-except here so tenacity can catch the error
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    response = scraper.get(base_url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.RequestException, cloudscraper.exceptions.CloudflareException)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def fetch_image_content(url: str, timeout: int = 10) -> bytes:
    """
    Run content fetching with retries using cloudscraper.
    """
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    response = scraper.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def download_image(post: Dict[str, Any], download_dir: str, timeout: int = 10) -> Tuple[str, int]:
    """
    Download a single image. Returns (status_message, downloaded_bytes).
    """
    file_url = post.get("file_url")
    if not file_url:
        return "skipped (no url)", 0

    post_id = post.get("id")
    # Determine extension from URL or default to .jpg if unknown
    parsed_url = urlparse(file_url)
    ext = os.path.splitext(parsed_url.path)[1]
    if not ext:
        ext = ".jpg"  # Fallback

    filename = f"{post_id}{ext}"
    filepath = os.path.join(download_dir, filename)

    # Resume capability: Check if file exists
    if os.path.exists(filepath):
        return f"{Fore.YELLOW}Skipped (already exists): {filename}", 0

    try:
        content = fetch_image_content(file_url, timeout=timeout)
        size = len(content)
        with open(filepath, "wb") as f:
            f.write(content)
        return f"{Fore.GREEN}Downloaded: {filename}", size
    except Exception as e:
        return f"{Fore.RED}Failed: {filename} - {e}", 0


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def load_stats() -> Dict[str, Any]:
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "total_downloaded_bytes": 0,
        "total_time_seconds": 0,
        "total_images_downloaded": 0
    }


def save_stats(stats: Dict[str, Any]):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)


def get_disk_usage(directory: str) -> str:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return format_size(total_size)


def update_readme(stats: Dict[str, Any], download_dir: str):
    if not os.path.exists(README_FILE):
        return

    # Calculate readable metrics
    total_files = stats.get("total_images_downloaded", 0)
    total_bytes = stats.get("total_downloaded_bytes", 0)
    total_time = stats.get("total_time_seconds", 0)
    
    total_size_str = format_size(total_bytes)
    disk_usage_str = get_disk_usage(download_dir)
    
    # Format time
    hours, remainder = divmod(int(total_time), 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    # Average speed
    if total_time > 0:
        avg_speed = total_bytes / total_time
        speed_str = f"{format_size(avg_speed)}/s"
    else:
        speed_str = "0 B/s"

    stats_section = f"""
## Statistics

| Metric | Value |
| :--- | :--- |
| **Total Images Downloaded** | `{total_files}` |
| **Total Data Downloaded** | `{total_size_str}` |
| **Total Time Spent** | `{time_str}` |
| **Average Download Speed** | `{speed_str}` |
| **Current Disk Usage** | `{disk_usage_str}` |
"""

    with open(README_FILE, "r") as f:
        content = f.read()

    if "## Statistics" in content:
        # Replace existing section
        # Finds the start of the section and assumes it ends at the next ## or EOF
        parts = content.split("## Statistics")
        pre_stats = parts[0]
        # Check if there is anything after the stats section (likely not, or maybe just EOF)
        # We will just append the new stats to the pre_stats part if it was at the end
        # But if there were other sections after, we need to be careful.
        # Simple approach: Assume Statistics is at the end or replace until next header
        
        # NOTE: This regex replacement is safer
        import re
        content = re.sub(r'## Statistics[\s\S]*?(?=\n## |$)', stats_section.strip(), content)
    else:
        # Append section
        content += "\n" + stats_section

    with open(README_FILE, "w") as f:
        f.write(content)
    print(f"{Fore.MAGENTA}Updated {README_FILE} with latest statistics.")


def main():
    parser = argparse.ArgumentParser(description="Konachan Image Downloader")
    parser.add_argument("--tags", type=str, default="", help="Tags to search for (space separated)")
    parser.add_argument("--start", type=int, default=0, help="Start page number (default: auto-resume or 1)")
    parser.add_argument("--end", type=int, default=0, help="End page number (default: 0 = download until empty)")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS_DEFAULT, help=f"Number of concurrent download threads (default: {MAX_WORKERS_DEFAULT})")
    parser.add_argument("--dir", type=str, default=DEFAULT_DOWNLOAD_DIR, help=f"Directory to save images (default: {DEFAULT_DOWNLOAD_DIR})")
    parser.add_argument("--limit", type=int, default=100, help="Max posts per page (default: 100)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"Network timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--unsafe", action="store_true", help="Allow NSFW content (unsafe mode)")

    args = parser.parse_args()

    # Ensure download directory exists
    os.makedirs(args.dir, exist_ok=True)

    # Progress Tracking
    progress_file = "progress.json"
    
    def load_progress():
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_progress(tags, last_page):
        data = load_progress()
        data[tags] = last_page
        with open(progress_file, "w") as f:
            json.dump(data, f, indent=4)

    # Determine start page
    start_page = args.start
    if start_page <= 0:
        progress = load_progress()
        start_page = progress.get(args.tags, 0) + 1
        print(f"{Fore.YELLOW}Resuming from page {start_page} for tags '{args.tags}'")
    
    print(f"{Fore.CYAN}Starting Konachan Downloader...")
    
    if args.unsafe:
        print(f"{Fore.RED}UNSAFE MODE: NSFW content enabled.")
    else:
        print(f"{Fore.GREEN}Safe Mode ENABLED (Default). Use --unsafe to disable.")

    current_page = start_page
    
    # Session Stats Tracking
    session_start_time = time.time()
    session_bytes = 0
    session_images = 0
    
    # 1. Fetch and Download Loop
    try:
        while True:
            # Check end condition
            if args.end > 0 and current_page > args.end:
                print(f"{Fore.CYAN}Reached end page {args.end}.")
                break

            base_url = BASE_URL_UNSAFE if args.unsafe else BASE_URL_SAFE
            print(f"{Fore.BLUE}Fetching metadata for page {current_page} from {base_url}...")
            posts = get_total_posts(base_url, args.tags, current_page, limit=args.limit, timeout=args.timeout)
            
            if not posts:
                print(f"{Fore.YELLOW}No more posts found on page {current_page}. Stopping.")
                break
            
            # Filter for safe mode (default)
            if not args.unsafe:
                original_count = len(posts)
                posts = [p for p in posts if p.get("rating") == "s"]
                filtered_count = original_count - len(posts)
                if filtered_count > 0:
                    print(f"Page {current_page}: Filtered {filtered_count} NSFW post(s).")
                    
            if not posts:
                 print(f"{Fore.YELLOW}Page {current_page}: No image to download after filtering. Moving next.")
                 save_progress(args.tags, current_page)
                 current_page += 1
                 continue

            print(f"Page {current_page}: Found {len(posts)} images. Downloading...")

            # Download Images for this page immediately to save progress per page
            # Use 'wait=False' in shutdown to ensure we don't hang on exit
            executor = ThreadPoolExecutor(max_workers=args.workers)
            futures = {}
            try:
                # Submit all tasks
                for post in posts:
                    future = executor.submit(download_image, post, args.dir, args.timeout)
                    futures[future] = post

                # Process results with a timeout for each completion
                # We expect at least one image to finish within (timeout + 5) seconds normally.
                # If cloudscraper hangs, this helps us bail out.
                # With 5 retries and exponential backoff, max wait could be around 60s+
                batch_timeout = 60 + args.timeout

                with tqdm(total=len(posts), unit="img") as pbar:
                    done_count = 0
                    try:
                        for future in concurrent.futures.as_completed(futures, timeout=batch_timeout):
                            try:
                                msg, size = future.result()
                                if size > 0:
                                    session_bytes += size
                                    session_images += 1
                                
                                if "Failed" in msg:
                                    pbar.write(msg)
                                elif "Downloaded" in msg:
                                    pass
                            except Exception as e:
                                pbar.write(f"{Fore.RED}Error in worker: {e}")
                            
                            pbar.update(1)
                            done_count += 1
                    except concurrent.futures.TimeoutError:
                        pbar.write(f"{Fore.RED}Batch timed out! {len(futures) - done_count} images were stuck.")
                        # Cancel remaining
                        for f in futures:
                            f.cancel()
            
            except KeyboardInterrupt:
                print(f"\n{Fore.RED}Download interrupted by user. Exiting immediately...")
                executor.shutdown(wait=False, cancel_futures=True)
                # Re-raise to exit the main loop
                raise
            finally:
                 # Ensure executor is cleaned up, but don't wait forever if stuck
                 executor.shutdown(wait=False, cancel_futures=True)

            # Update progress after page is complete
            save_progress(args.tags, current_page)
            current_page += 1
            
            # Polite delay
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Download interrupted by user.")
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {e}")
    finally:
        # Save Stats
        session_duration = time.time() - session_start_time
        print(f"\n{Fore.CYAN}Session Summary:")
        print(f"  Images: {session_images}")
        print(f"  Data: {format_size(session_bytes)}")
        print(f"  Time: {session_duration:.2f}s")
        
        all_stats = load_stats()
        all_stats["total_downloaded_bytes"] += session_bytes
        all_stats["total_time_seconds"] += session_duration
        all_stats["total_images_downloaded"] += session_images
        
        save_stats(all_stats)
        update_readme(all_stats, args.dir)
        
        print(f"{Fore.CYAN}Job finished!")


if __name__ == "__main__":
    main()
