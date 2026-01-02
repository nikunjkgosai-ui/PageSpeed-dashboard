<<<<<<< HEAD
# PageSpeed-dashboard
Google Page Speed
=======
GA Dashboard
============

A small Streamlit dashboard that fetches metrics from Google Analytics 4 (GA4), Google Search Console, and PageSpeed Insights.

Requirements
------------
- Create a Google Cloud service account with the following APIs enabled in the project:
  - Analytics Data API (for GA4)
  - Search Console API
  - (Optional) Enable PageSpeed API or use an API key
- Download the service account JSON and set `SERVICE_ACCOUNT_FILE` env var or place file path in `.env`.

Quick setup
-----------
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file from `.env.example` and update values.

3. Grant the service account access to:
   - Your Google Analytics 4 property (add as Viewer/Analyst) and
   - Your Search Console site (add service account email as owner or verified user)

4. Run the dashboard:

```bash
streamlit run app.py
```

Notes
-----
- This is a starter project. You may need to adjust metrics/requests to match your GA4 schema and property setup.
- PageSpeed Insights uses `PAGESPEED_API_KEY` or can be called without key for some public endpoints.
>>>>>>> 3f15d5e (Initial commit - PageSpeed dashboard)
