import json
import subprocess

path = "test_hendry_dump.py"
with open(path, "w") as f:
    f.write('''
from curl_cffi import requests
import json
url = "https://blogapi.myocv.com/prod/paginatedBlog/a102933935?blogKey=inmates&limit=2&sort=nameAZ&type=integration&page=1&translation=default"
r = requests.get(url, impersonate="chrome120")
print(json.dumps(r.json()["posts"][0], indent=2))
''')

try:
    result = subprocess.run(
        ["python3", path],
        capture_output=True,
        text=True,
        check=True
    )
    print("SUCCESS_START")
    print(result.stdout)
    print("SUCCESS_END")
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'stdout'):
        print("STDOUT:", e.stdout)
    if hasattr(e, 'stderr'):
        print("STDERR:", e.stderr)
