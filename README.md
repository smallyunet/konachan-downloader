# Konachan Downloader

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

A professional, multi-threaded Python CLI tool to download images from [konachan.net](https://konachan.net). It supports downloading the latest uploads or filtering by specific tags.

## Features

- **Multi-threaded**: Fast downloading with concurrent workers.
- **Resumable**: Skips files that already exist.
- **Progress Tracking**: Automatically remembers the last downloaded page for each tag and resumes from there.
- **Smart Filtering**: Safe mode enabled by default.

- **Robust**: Automatic retries for network failures.
- **Polite**: Includes rate limiting to respect server load.
- **Advanced**: Uses `cloudscraper` to bypass Cloudflare protection on the unsafe domain.
- **Flexible**: Command-line arguments for full control.

## Prerequisites

- **Python 3.8+**

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/konachan-downloader.git
    cd konachan-downloader
    ```

2.  **Set up a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # .venv\Scripts\activate   # Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script using `python main.py`.

### Safe Mode by Default
By default, the script **only downloads safe images** (Rating: S) from `konachan.net`. To download NSFW content, you must use the `--unsafe` flag, which switches to `konachan.com`.

> **Note**: `konachan.com` has strict Cloudflare protection. While this script uses `cloudscraper` to attempt to bypass it, you may still encounter 403 Forbidden errors depending on your network environment.

### Progress Tracking
The script creates a `progress.json` file. If you interrupt a download, simply run the same command again, and it will **automatically resume** from the last successfully downloaded page.

### Examples

**Download all "hatsune_miku" images (Safe only):**
```bash
python main.py --tags "hatsune_miku"
```
*Note: This will start from Page 1 (or your last saved progress) and download until no more images are found.*

**Download NSFW images (Unsafe Mode):**
```bash
python main.py --tags "tagme" --unsafe
```

**Download specific pages:**
```bash
python main.py --tags "vocaloid" --start 1 --end 5
```

**Show help message:**
```bash
python main.py --help
```

### Options

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--tags` | `""` | Tags to search for (space separated). |
| `--start` | `0` | Start page. `0` = Auto-resume from `progress.json` or start at 1. |
| `--end` | `0` | End page. `0` = Download indefinitely until no images found. |
| `--workers` | `5` | Number of concurrent download threads. |
| `--dir` | `downloads` | Directory to save images. |
| `--limit` | `100` | Max posts per page. |
| `--timeout` | `10` | Network timeout in seconds. |
| `--unsafe` | `False` | **Enable NSFW content** (Disable Safe Mode). |

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.






## Statistics

| Metric | Value |
| :--- | :--- |
| **Total Images Downloaded** | `510` |
| **Total Data Downloaded** | `3.91 GB` |
| **Total Time Spent** | `00:14:38` |
| **Average Download Speed** | `4.56 MB/s` |
| **Current Disk Usage** | `4.85 GB` |
