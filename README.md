# Konachan Downloader

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

![Screenshot](docs/screenshot.png)

A professional, multi-threaded Python CLI tool to download images from [konachan.net](https://konachan.net). It supports downloading the latest uploads or filtering by specific tags.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Examples](#examples)
  - [Options](#options)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Statistics](#statistics)

## Features

- **Multi-threaded**: Fast downloading with concurrent workers.
- **Resumable**: Skips files that already exist and remembers last page per tag.
- **Smart Filtering**: Safe mode enabled by default; NSFW switches to Cloudflare-aware engine.
- **Robust**: Automatic retries and rate limiting to respect server load.

## Project Structure

```text
.
├── main.py            # Entry point, CLI handling & download orchestrator
├── api.py             # Network logic (Cloudscraper, tenacity retries)
├── stats.py           # Statistics calculation and README formatting
├── const.py           # Shared constants and configurations
├── update_readme.py   # Standalone maintenance script for stats
├── progress.json      # PERSISTENT: Tracks last downloaded page per tag
└── stats.json         # PERSISTENT: Lifetime download statistics
```

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/konachan-downloader.git
    cd konachan-downloader
    ```

2.  **Set up environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

## Usage

### Examples

**Standard Download (Safe only):**
```bash
python main.py --tags "hatsune_miku"
```

**Unsafe Mode (NSFW):**
```bash
python main.py --tags "scenery" --unsafe
```

**Specific Range:**
```bash
python main.py --tags "vocaloid" --start 1 --end 5
```

### Options

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--tags` | `""` | Tags to search for (space separated). |
| `--start` | `0` | Start page. `0` = Auto-resume. |
| `--end` | `0` | End page. `0` = Until empty. |
| `--workers` | `5` | Concurrent threads. |
| `--dir` | `downloads` | Save directory. |
| `--unsafe` | `False` | Enable NSFW content (switches to konachan.com). |
| `--proxy` | `None` | Proxy URL (e.g., http://127.0.0.1:7890). |

## Maintenance

To keep your `README.md` statistics up to date, run the maintenance script after downloads:

```bash
python update_readme.py
```

## Troubleshooting

- **403 Forbidden**: Usually occurs on `konachan.com` (Unsafe mode) due to Cloudflare protection. Ensure `cloudscraper` is up to date.
- **Connection Errors**: If you encounter `NameResolutionError` or timeouts, try using a proxy with the `--proxy` flag.

## License

MIT - See [LICENSE](LICENSE) for details.

## Statistics

| Metric | Value |
| :--- | :--- |
| **Total Images Downloaded** | `6397` |
| **Total Data Downloaded** | `45.71 GB` |
| **Total Time Spent** | `02:04:57` |
| **Average Download Speed** | `6.24 MB/s` |
| **Current Disk Usage** | `46.65 GB` |
