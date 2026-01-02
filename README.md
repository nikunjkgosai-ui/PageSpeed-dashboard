<<<<<<< HEAD
PageSpeed Insights Dashboard
===========================

This Streamlit app runs PageSpeed Insights (mobile & desktop) for a given URL and shows a clean comparison of key metrics, performance scores, and actionable opportunities/diagnostics.

Quick Start (local)
-------------------
1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Provide your PageSpeed API key (optional but recommended):

- Create a `.env` file in the project root with:

```
PAGESPEED_API_KEY=YOUR_API_KEY_HERE
SITE_URL=https://example.com
```

- Or set the env var in PowerShell for the session:

```powershell
$env:PAGESPEED_API_KEY="YOUR_API_KEY_HERE"
```

3. Run the app:

```powershell
cd ga_dashboard
.\.venv\Scripts\activate
streamlit run app.py
```

4. Open http://localhost:8501 in your browser.

Notes
-----
- The app is focused on PageSpeed Insights only (GA4 and Search Console integrations were removed).
- Keep `.env` and `service-account.json` out of source control; `.gitignore` already excludes them.

Deploying to Streamlit Cloud
----------------------------
1. Push this repo to GitHub.
2. In Streamlit Community Cloud (share.streamlit.io) create a new app pointing to this repo and `app.py`.
3. In the app's Settings → Secrets, add the following keys (replace values):

```
PAGESPEED_API_KEY="YOUR_API_KEY_HERE"
SITE_URL="https://example.com"
```

Secrets added in Streamlit are exposed as environment variables; no further code changes are required.

Want help pushing this repo to GitHub or configuring Streamlit Secrets? Open a prompt and I can do it for you.
-----
- This is a starter project. You may need to adjust metrics/requests to match your GA4 schema and property setup.
- PageSpeed Insights uses `PAGESPEED_API_KEY` or can be called without key for some public endpoints.
>>>>>>> 3f15d5e (Initial commit - PageSpeed dashboard)
