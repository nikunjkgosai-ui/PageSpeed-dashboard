from dotenv import load_dotenv
import os, json
from fetchers import fetch_pagespeed

load_dotenv()

url = os.environ.get("PAGESPEED_TEST_URL") or "https://allelitecfc.com/"
api_key = os.environ.get("PAGESPEED_API_KEY")

print(f"Running PageSpeed Insights for: {url}\n(using API key from .env: {'yes' if api_key else 'no'})\n")
res = fetch_pagespeed(url, api_key=api_key, strategy="mobile")
print(json.dumps({
    "performance_score": res.get("performance_score"),
    "metrics": res.get("metrics")
}, indent=2))
