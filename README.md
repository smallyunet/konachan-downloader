# Konachan Downloader

![License](https://img.shields.io/badge/license-MIT-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/konachan-downloader)](https://pypi.org/project/konachan-downloader/)
[![Homebrew](https://img.shields.io/badge/homebrew-tap-orange)](https://github.com/smallyunet/homebrew-tap)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

![Screenshot](docs/screenshot.png)

A high-performance CLI tool designed for efficiently downloading images from **konachan.net**. It features a smart update system, resumable downloads, and multi-threading support.

## ✨ Key Features

- **🔄 Smart Update & Resume**: The ultimate workflow. It checks page 1-5 for new uploads. If no new images are found, it **automatically jumps** to your last saved "deep" progress (e.g., Page 400) and continues archiving.
- **⚡ High Performance**: Multi-threaded downloader utilizes full bandwidth.
- **⏯️ Resumable**: Skips existing files and remembers your last position.
- **🛡️ Secure**: Defaults to Safe Mode. Unsafe Mode supports Cloudflare bypass logic.
- **🔍 Robust**: Built-in retries for network stability.

## 🚀 Quick Usage

### The "Best Practice" Way
Use **Smart Mode** for everything. It handles both **checking for updates** and **resuming deep downloads**.
1. Scans recent pages for new content.
2. If fully caught up, it **auto-jumps** to your history (e.g., Page 400) to fill old gaps.

```bash
konachan-dl --tags "hatsune_miku" --smart
```

### Other Commands

**Download Everything (First Run)**
```bash
# Resume automatically from where you left off
konachan-dl --tags "hatsune_miku"
```

**Unsafe Mode (NSFW)**
```bash
# Switches to konachan.com
konachan-dl --tags "scenery" --unsafe
```

**Custom Range**
```bash
konachan-dl --tags "vocaloid" --start 1 --end 10
```

## ⚙️ Installation

### Homebrew (Recommended for macOS)
```bash
brew tap smallyunet/tap
brew install konachan-downloader
```

### PyPI
```bash
pip install konachan-downloader
```

### From Source (Developers)
```bash
git clone https://github.com/smallyunet/konachan-downloader.git
cd konachan-downloader
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 📊 Statistics

| Metric | Value |
| :--- | :--- |
| **Total Images** | `22089` |
| **Total Data** | `142.09 GB` |
| **Total Time** | `06:13:19` |
| **Current Disk** | `143.29 GB` |

