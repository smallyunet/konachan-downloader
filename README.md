# Konachan Downloader

A simple, multi-threaded Python script to download images from [konachan.net](https://konachan.net) based on tags.

## Prerequisites

- **Python 3.8+** must be installed on your system.

## Installation

1.  **Clone or download** this repository.
2.  **Open a terminal** in the project directory.
3.  **Create a virtual environment** (recommended to avoid dependency conflicts):

    ```bash
    python3 -m venv .venv
    ```

4.  **Activate the virtual environment**:

    -   **macOS / Linux**:
        ```bash
        source .venv/bin/activate
        ```
    -   **Windows**:
        ```bash
        .venv\Scripts\activate
        ```

5.  **Install the required dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Configure the script** (optional):
    Open `main.py` in a text editor and update the `Configuration` section at the top to change tags, page limits, or download settings:

    ```python
    # Configuration
    TAGS = ""            # e.g., "hatsune_miku vocaloid"
    START_PAGE = 1
    END_PAGE = 5
    MAX_WORKERS = 5      # Number of concurrent downloads
    ```

2.  **Run the script**:

    ```bash
    python main.py
    ```

    The script will fetch metadata and start downloading images to the `downloads` directory (or whichever directory you configured).
# konachan-downloader
