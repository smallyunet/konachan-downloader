import argparse
from konachan_dl.const import DEFAULT_DOWNLOAD_DIR
from konachan_dl.stats import load_stats, update_readme

def main():
    parser = argparse.ArgumentParser(description="Update README.md with download statistics")
    parser.add_argument("--dir", type=str, default=DEFAULT_DOWNLOAD_DIR, help=f"Directory where images are saved (default: {DEFAULT_DOWNLOAD_DIR})")
    
    args = parser.parse_args()
    
    print("Loading statistics...")
    stats = load_stats()
    
    print(f"Updating README.md using statistics and download directory: {args.dir}")
    update_readme(stats, args.dir)
    print("Done.")

if __name__ == "__main__":
    main()
