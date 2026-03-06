#!/usr/bin/env python3
from curl_cffi import requests
import json
import sys

def dump():
    url = "https://blogapi.myocv.com/prod/paginatedBlog/a102933935?blogKey=inmates&limit=2&sort=nameAZ&type=integration&page=1&translation=default"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome120")
        data = r.json()
        
        posts = data.get("posts", [])
        if posts:
            print(json.dumps(posts[0], indent=2))
        else:
            print("No posts found. Keys:", data.keys())
    except Exception as e:
        print("Error:", e)
        
if __name__ == "__main__":
    dump()
