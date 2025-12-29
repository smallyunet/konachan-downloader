import requests
import cloudscraper
import logging
import sys
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from .const import STATS_FILE, README_FILE

# Configure logging for tenacity
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(20),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((requests.RequestException, cloudscraper.exceptions.CloudflareException)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def get_total_posts(base_url: str, tags: str, page: int, proxies: Dict[str, str] = None, limit: int = 100, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch posts from the API with robust retries.
    """
    params = {
        "tags": tags,
        "page": page,
        "limit": limit
    }
    # Use context manager to ensure session is closed
    with cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}) as scraper:
        if proxies:
            scraper.proxies = proxies
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
def get_total_count(base_url: str, tags: str, proxies: Dict[str, str] = None, timeout: int = 10) -> int:
    """
    Fetch the total count of posts for the given tags using the XML API.
    """
    # Replace .json with .xml to get metadata
    xml_url = base_url.replace(".json", ".xml")
    params = {
        "tags": tags,
        "limit": 1
    }
    with cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}) as scraper:
        if proxies:
            scraper.proxies = proxies
        response = scraper.get(xml_url, params=params, timeout=timeout)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        count = root.get("count")
        return int(count) if count else 0


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((requests.RequestException, cloudscraper.exceptions.CloudflareException)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
def fetch_image_content(url: str, proxies: Dict[str, str] = None, timeout: int = 10) -> bytes:
    """
    Run content fetching with retries using cloudscraper.
    """
    with cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}) as scraper:
        if proxies:
            scraper.proxies = proxies
        response = scraper.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
