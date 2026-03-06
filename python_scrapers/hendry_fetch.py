from curl_cffi import requests
import json

url = "https://blogapi.myocv.com/prod/paginatedBlog/a102933935?blogKey=inmates&limit=5&sort=nameAZ&type=integration&page=1&translation=default"
try:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, impersonate="chrome120")
    data = r.json()
    print("Post Count:", len(data.get("posts", [])))
    if data.get("posts"):
        with open("hendry_post.json", "w") as f:
            json.dump(data["posts"][0], f, indent=2)
except Exception as e:
    import urllib.request
    print("curl_cffi failed, using urllib")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        if data.get("posts"):
            with open("hendry_post.json", "w") as f:
                json.dump(data["posts"][0], f, indent=2)
