from curl_cffi import requests
import json
url = "https://blogapi.myocv.com/prod/paginatedBlog/a102933935?blogKey=inmates&limit=2&sort=nameAZ&type=integration&page=1&translation=default"
try:
    r = requests.get(url, impersonate="chrome120")
    data = r.json()
    posts = data.get("posts", [])
    if posts:
        print("SUCCESS_START")
        print(json.dumps(posts[0], indent=2))
        print("SUCCESS_END")
except Exception as e:
    print("ERROR:", e)
