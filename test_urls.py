
import cloudscraper

def test_konachan_urls():
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    try:
        print("Fetching from konachan.com...")
        resp = scraper.get("https://konachan.com/post.json?tags=rating:safe&limit=5")
        resp.raise_for_status()
        data = resp.json()
        if not data:
            print("No data returned")
            return
        
        print(f"Got {len(data)} posts.")
        for post in data:
            file_url = post.get('file_url')
            print(f"ID: {post.get('id')} - File URL: {file_url}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_konachan_urls()
