import json
from curl_cffi import requests

def run():
    url = "https://blogapi.myocv.com/prod/paginatedBlog/a102933935?blogKey=inmates&limit=5&sort=nameAZ&type=integration&page=1&translation=default"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    print("Fetching URL:", url)
    r = requests.get(url, headers=headers, impersonate="chrome120", timeout=10)
    data = r.json()

    print("Status:", r.status_code)
    print("Keys:", data.keys())
    
    posts = data.get("posts", [])
    print("Posts count:", len(posts))
    
    if posts:
        post = posts[0]
        print("Sample Post keys:", post.keys())
        
        with open("hendry_api.json", "w") as f:
            json.dump(post, f, indent=2)
if __name__ == "__main__":
    run()
