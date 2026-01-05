import requests
import pandas as pd
from datetime import datetime
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric


def fetch_pagespeed(url, api_key=None, strategy="mobile", cache_bust=False):
    # optionally append a cache-busting query param to the URL to force a fresh fetch
    fetch_url = url
    if cache_bust:
        import time
        sep = "&" if "?" in fetch_url else "?"
        fetch_url = f"{fetch_url}{sep}_={int(time.time())}"
    params = {"url": fetch_url, "strategy": strategy}
    if api_key:
        params["key"] = api_key
    r = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    lh = data.get("lighthouseResult", {})
    categories = lh.get("categories", {})
    audits = lh.get("audits", {})
    perf_score = None
    if categories.get("performance"):
        perf_score = categories["performance"].get("score")
    metrics = {}
    # keys we care about and friendly labels
    keys = [
        "first-contentful-paint",
        "largest-contentful-paint",
        "cumulative-layout-shift",
        "speed-index",
        "total-blocking-time",
        "interactive",
    ]
    for key in keys:
        if key in audits:
            audit = audits[key]
            display = audit.get("displayValue")
            numeric = audit.get("numericValue")
            # numericValue usually in milliseconds for timing metrics; keep as ms if present
            if numeric is not None:
                try:
                    numeric = float(numeric)
                except Exception:
                    numeric = None
            else:
                # try to parse number from display like '1.2 s' or '120 ms'
                numeric = None
                if display:
                    try:
                        # remove commas
                        txt = display.replace(",", "")
                        if "ms" in txt:
                            numeric = float(txt.replace("ms", "").strip())
                        elif "s" in txt:
                            numeric = float(txt.replace("s", "").strip()) * 1000.0
                    except Exception:
                        numeric = None
            metrics[key] = {"display": display, "numeric_ms": numeric}

    # extract opportunities and diagnostics for insights
    opportunities = []
    diagnostics = []
    for aid, audit in audits.items():
        details = audit.get("details") or {}
        dtype = details.get("type")
        title = audit.get("title") or aid
        description = audit.get("description") or audit.get("helpText") or ""
        display = audit.get("displayValue")
        numeric = audit.get("numericValue")

        if dtype == "opportunity":
            # try overallSavingsMs or sum of items
            savings = details.get("overallSavingsMs")
            if savings is None:
                items = details.get("items", []) or []
                try:
                    savings = sum(float(it.get("overallSavingsMs", 0)) for it in items)
                except Exception:
                    savings = None
            opportunities.append({
                "id": aid,
                "title": title,
                "description": description,
                "display": display,
                "savings_ms": float(savings) if savings is not None else None,
            })
        elif dtype == "diagnostic":
            diagnostics.append({
                "id": aid,
                "title": title,
                "description": description,
                "display": display,
                "numeric": float(numeric) if numeric is not None else None,
            })

    return {
        "performance_score": perf_score,
        "metrics": metrics,
        "opportunities": opportunities,
        "diagnostics": diagnostics,
        "raw": data,
    }


def ga_run_report(client, property_id, start_date, end_date, metrics=None, dimensions=None):
    if not metrics:
        metrics = [Metric(name="activeUsers"), Metric(name="sessions"), Metric(name="averageSessionDuration")]
    date_range = DateRange(start_date=start_date, end_date=end_date)
    request = RunReportRequest(property=f"properties/{property_id}", date_ranges=[date_range], metrics=metrics)
    if dimensions:
        request.dimensions.extend([Dimension(name=d) for d in dimensions])
    response = client.run_report(request)
    # build dataframe
    cols = []
    if response.dimension_headers:
        cols.extend([h.name for h in response.dimension_headers])
    if response.metric_headers:
        cols.extend([h.name for h in response.metric_headers])
    rows = []
    for row in response.rows:
        values = []
        for d in row.dimension_values:
            values.append(d.value)
        for m in row.metric_values:
            values.append(m.value)
        rows.append(values)
    df = pd.DataFrame(rows, columns=cols)
    return df


def fetch_ga4_metrics(client, property_id, start_date, end_date):
    # fetch daily sessions and users
    df = ga_run_report(client, property_id, start_date, end_date, metrics=[Metric(name="activeUsers"), Metric(name="sessions")], dimensions=["date"])
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df["activeUsers"] = pd.to_numeric(df["activeUsers"]) 
        df["sessions"] = pd.to_numeric(df["sessions"]) 
    return df


def fetch_search_console(service, site_url, start_date, end_date):
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["date"],
        "rowLimit": 25000
    }
    resp = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    rows = resp.get("rows", [])
    data = []
    for r in rows:
        date = r.get("keys", [None])[0]
        clicks = r.get("clicks", 0)
        impressions = r.get("impressions", 0)
        ctr = r.get("ctr", 0)
        position = r.get("position", 0)
        data.append({"date": date, "clicks": clicks, "impressions": impressions, "ctr": ctr, "position": position})
    df = pd.DataFrame(data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df
