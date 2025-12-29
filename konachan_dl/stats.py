import os
import json
import math
import re
from typing import Dict, Any
from colorama import Fore
from .const import STATS_FILE, README_FILE

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
| **Total Images** | `{total_files}` |
| **Total Data** | `{total_size_str}` |
| **Total Time** | `{time_str}` |
| **Current Disk** | `{disk_usage_str}` |
"""

    with open(README_FILE, "r") as f:
        content = f.read()

    if "## Statistics" in content:
        # Replace existing section
        content = re.sub(r'## Statistics[\s\S]*?(?=\n## |$)', stats_section.strip(), content)
    else:
        # Append section
        content += "\n" + stats_section

    with open(README_FILE, "w") as f:
        f.write(content)
    print(f"{Fore.MAGENTA}Updated {README_FILE} with latest statistics.")
