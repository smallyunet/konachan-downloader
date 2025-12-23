import os
import argparse
import requests
import json
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from tqdm import tqdm
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

# Default Constants
DEFAULT_BASE_URL = "https://konachan.net/post.json"
DEFAULT_DOWNLOAD_DIR = "downloads"
DEFAULT_TIMEOUT = 10  # Seconds
MAX_WORKERS_DEFAULT = 5


class DownloadError(Exception):
    pass


def get_total_posts(base_url: str, tags: str, page: int, limit: int = 100, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch posts from the API.
    """
    params = {
        "tags": tags,
        "page": page,
        "limit": limit
    }
    try:
        response = requests.get(base_url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"{Fore.RED}Error fetching metadata for page {page}: {e}")
        return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True
)
def fetch_image_content(url: str, timeout: int = 10) -> bytes:
    """
    Fetch image content with retries.
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def download_image(post: Dict[str, Any], download_dir: str, timeout: int = 10) -> str:
    """
    Download a single image.
    """
    file_url = post.get("file_url")
    if not file_url:
        return "skipped (no url)"

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
        return f"{Fore.YELLOW}Skipped (already exists): {filename}"

    try:
        content = fetch_image_content(file_url, timeout=timeout)
        with open(filepath, "wb") as f:
            f.write(content)
        return f"{Fore.GREEN}Downloaded: {filename}"
    except Exception as e:
        return f"{Fore.RED}Failed: {filename} - {e}"


def main():
    parser = argparse.ArgumentParser(description="Konachan Image Downloader")
    parser.add_argument("--tags", type=str, default="", help="Tags to search for (space separated, e.g., 'hatsune_miku vocaloid')")
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

    all_posts = []
    
    current_page = start_page
    
    # 1. Fetch and Download Loop
    while True:
        # Check end condition
        if args.end > 0 and current_page > args.end:
            print(f"{Fore.CYAN}Reached end page {args.end}.")
            break

        print(f"{Fore.BLUE}Fetching metadata for page {current_page}...")
        posts = get_total_posts(DEFAULT_BASE_URL, args.tags, current_page, limit=args.limit, timeout=args.timeout)
        
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
        try:
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {executor.submit(download_image, post, args.dir, args.timeout): post for post in posts}
                
                with tqdm(total=len(posts), unit="img") as pbar:
                     for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if "Failed" in result:
                            pbar.write(result)
                        pbar.update(1)
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Download interrupted by user. Exiting...")
            # Note: The executor context manager in python < 3.9 will wait for threads.
            # But the user is on 3.10, so it will try to exit cleanly if we break.
            # To be safe, we can just return or exit, but threading might hang if not daemon.
            # ThreadPoolExecutor threads are NOT daemon by default. 
            # We will forcefully exit.
            executor.shutdown(wait=False, cancel_futures=True)
            return

        # Update progress after page is complete
        save_progress(args.tags, current_page)
        current_page += 1

    print(f"{Fore.CYAN}Job finished!")


if __name__ == "__main__":
    main()
