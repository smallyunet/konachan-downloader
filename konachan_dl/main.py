import os
import time
import math
import argparse
import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from typing import Dict, Any, Tuple

from colorama import init, Fore
from tqdm import tqdm

from .const import (
    BASE_URL_SAFE, BASE_URL_UNSAFE, DEFAULT_DOWNLOAD_DIR,
    DEFAULT_TIMEOUT, MAX_WORKERS_DEFAULT
)
from .api import get_total_posts, fetch_image_content, get_total_count
from .stats import load_stats, save_stats, format_size

# Initialize colorama
init(autoreset=True)

def download_image(post: Dict[str, Any], download_dir: str, proxies: Dict[str, str] = None, timeout: int = 10) -> Tuple[str, int]:
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
        content = fetch_image_content(file_url, proxies=proxies, timeout=timeout)
        size = len(content)
        with open(filepath, "wb") as f:
            f.write(content)
        return f"{Fore.GREEN}Downloaded: {filename}", size
    except Exception as e:
        return f"{Fore.RED}Failed: {filename} - {e}", 0


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
    parser.add_argument("--proxy", type=str, default=None, help="Proxy URL (e.g., http://127.0.0.1:7890)")
    parser.add_argument("--stop-after-skipped", type=int, default=0, help="Stop after N consecutive pages where all images were skipped (default: 0 = disabled)")
    parser.add_argument("--smart", action="store_true", help="Smart Mode: Start from page 1 and stop after 5 skipped pages (equivalent to --start 1 --stop-after-skipped 5)")

    args = parser.parse_args()

    # Smart Mode Override
    if args.smart:
        if args.start == 0:  # Only override if not explicitly set
            args.start = 1
        if args.stop_after_skipped == 0:
            args.stop_after_skipped = 5
        print(f"{Fore.MAGENTA}Smart Mode ENABLED: Starting from page {args.start}, stop after {args.stop_after_skipped} skipped pages.")

    # Ensure download directory exists
    os.makedirs(args.dir, exist_ok=True)
    
    # Prepare proxies
    proxies = None
    if args.proxy:
        proxies = {
            "http": args.proxy,
            "https": args.proxy
        }
        print(f"{Fore.YELLOW}Using proxy: {args.proxy}")

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
    
    # Fetch total count to calculate total pages
    base_url = BASE_URL_UNSAFE if args.unsafe else BASE_URL_SAFE
    try:
        total_posts = get_total_count(base_url, args.tags, proxies=proxies, timeout=args.timeout)
        total_pages = math.ceil(total_posts / args.limit)
        print(f"{Fore.CYAN}Total posts found: {total_posts} (~{total_pages} pages)")
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Could not fetch total post count: {e}")
        total_pages = 0

    # Session Stats Tracking
    session_start_time = time.time()
    session_bytes = 0
    session_images = 0
    
    # 1. Fetch and Download Loop
    consecutive_skipped_pages = 0
    try:
        while True:
            # Check end condition
            if args.end > 0 and current_page > args.end:
                print(f"{Fore.CYAN}Reached end page {args.end}.")
                break

            base_url = BASE_URL_UNSAFE if args.unsafe else BASE_URL_SAFE
            page_str = f"page {current_page}"
            if total_pages > 0:
                page_str += f" of {total_pages}"
            print(f"{Fore.BLUE}Fetching metadata for {page_str} from {base_url}...")
            
            try:
                posts = get_total_posts(base_url, args.tags, current_page, proxies=proxies, limit=args.limit, timeout=args.timeout)
            except Exception as e:
                print(f"{Fore.RED}Failed to fetch posts: {e}")
                if "NameResolutionError" in str(e) and not args.proxy:
                    print(f"{Fore.YELLOW}TIP: If you are seeing NameResolutionError, try using the --proxy argument.")
                # We can choose to break or retry, but tenacity handles retries. 
                # If it bubbles up here, it's a permanent failure.
                break

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

            page_summary = f"Page {current_page}"
            if total_pages > 0:
                page_summary += f"/{total_pages}"
            print(f"{page_summary}: Found {len(posts)} images. Downloading...")

            # Download Images for this page immediately to save progress per page
            # Use 'wait=False' in shutdown to ensure we don't hang on exit
            executor = ThreadPoolExecutor(max_workers=args.workers)
            images_downloaded_on_this_page = 0
            futures = {}
            try:
                # Submit all tasks
                for post in posts:
                    future = executor.submit(download_image, post, args.dir, proxies=proxies, timeout=args.timeout)
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
                                    images_downloaded_on_this_page += 1
                                
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

            # Check for smart stop
            if args.stop_after_skipped > 0:
                if images_downloaded_on_this_page == 0:
                    consecutive_skipped_pages += 1
                    print(f"{Fore.YELLOW}  >> Page {current_page} skipped completely. ({consecutive_skipped_pages}/{args.stop_after_skipped} consecutive)")
                    if consecutive_skipped_pages >= args.stop_after_skipped:
                        print(f"{Fore.MAGENTA}  >> Reached limit of {args.stop_after_skipped} skipped pages. Smart stop triggered.")
                        break
                else:
                    consecutive_skipped_pages = 0
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
        
        print(f"{Fore.CYAN}Job finished!")


if __name__ == "__main__":
    main()
