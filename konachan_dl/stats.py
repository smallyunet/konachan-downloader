import os
import json
import math
from typing import Dict, Any
from colorama import Fore
from .const import STATS_FILE

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


