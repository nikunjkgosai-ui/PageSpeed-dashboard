import streamlit as st
import os
from datetime import date, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
from fetchers import fetch_pagespeed
import numpy as np

st.set_page_config(page_title="PageSpeed Dashboard", layout="wide")

st.title("PageSpeed Insights Dashboard")

# Use API key from environment; do not expose it in the frontend
pagespeed_key = os.environ.get("PAGESPEED_API_KEY", "")

# URL input and Analyse button under the title (no sidebar)
# use a form with two columns so the Analyse button is vertically centered with the input
with st.form("analyse_form"):
    cols = st.columns([10, 1])
    with cols[0]:
        site_url = st.text_input("Website URL", value=os.environ.get("SITE_URL", "https://allelitecfc.com/"))
    with cols[1]:
        # Add vertical spacing to center the button
        st.markdown("<div style='height: 2.2em'></div>", unsafe_allow_html=True)
        analyse = st.form_submit_button("Analyse")


def normalize_score(s):
    if s is None:
        return None
    try:
        f = float(s)
    except Exception:
        return None
    # Lighthouse returns 0..1 in many cases; convert to 0..100
    if f <= 1:
        return round(f * 100, 1)
    return round(f, 1)


def build_comparison_table(mobile, desktop):
    keys = set()
    keys.update(mobile.get("metrics", {}).keys())
    keys.update(desktop.get("metrics", {}).keys())
    rows = []
    for k in sorted(keys):
        mv = mobile.get("metrics", {}).get(k)
        dv = desktop.get("metrics", {}).get(k)
        rows.append({"metric": k, "mobile": mv, "desktop": dv})
    import pandas as pd
    df = pd.DataFrame(rows)
    return df


def fetch_both(url, key, cache_bust=False):
    mobile = fetch_pagespeed(url, api_key=key or None, strategy="mobile", cache_bust=cache_bust)
    desktop = fetch_pagespeed(url, api_key=key or None, strategy="desktop", cache_bust=cache_bust)
    return mobile, desktop


def show_results(mobile, desktop):
    # raw scores are 0..1 (or sometimes 0..100). Show raw for debugging and normalize for display.
    raw_m = mobile.get("performance_score")
    raw_d = desktop.get("performance_score")
    m_score = normalize_score(raw_m)
    d_score = normalize_score(raw_d)
    delta = None
    if m_score is not None and d_score is not None:
        delta = d_score - m_score

    st.subheader("Performance Scores")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Mobile Performance", f"{m_score if m_score is not None else 'N/A'}", delta=f"{(d_score-m_score) if delta is not None else ''}")
        st.caption(f"raw: {raw_m}")
    with c2:
        st.metric("Desktop Performance", f"{d_score if d_score is not None else 'N/A'}")
        st.caption(f"raw: {raw_d}")
    with c3:
        if delta is not None:
            st.write(f"Desktop − Mobile = {delta:+.1f}")
        else:
            st.write("")

    st.markdown("---")
    st.subheader("Key Metrics")
    # display each metric in clean boxes for mobile and desktop
    keys = sorted(set(list(mobile.get("metrics", {}).keys()) + list(desktop.get("metrics", {}).keys())))
    for key in keys:
        label = key.replace("-", " ").title()
        m_val = mobile.get("metrics", {}).get(key, {})
        d_val = desktop.get("metrics", {}).get(key, {})
        m_num = m_val.get("numeric_ms") if isinstance(m_val, dict) else None
        d_num = d_val.get("numeric_ms") if isinstance(d_val, dict) else None
        m_disp = m_val.get("display") if isinstance(m_val, dict) else m_val
        d_disp = d_val.get("display") if isinstance(d_val, dict) else d_val

        # format numbers: show ms as '1234 ms' or if None show display or 'N/A'
        def fmt(numeric, display):
            if numeric is not None:
                # show seconds if >1000ms
                if numeric >= 1000:
                    return f"{numeric/1000:.2f} s"
                else:
                    return f"{int(round(numeric))} ms"
            if display:
                return display
            return "N/A"

        col_label, col_m, col_d = st.columns([1, 1, 1])
        with col_label:
            st.write(f"**{label}**")
        with col_m:
            st.metric("Mobile", fmt(m_num, m_disp))
        with col_d:
            st.metric("Desktop", fmt(d_num, d_disp))

    # Insights: Opportunities and Diagnostics
    st.markdown("---")
    st.subheader("Opportunities (Top Savings)")
    ops = []
    for op in mobile.get("opportunities", []) + desktop.get("opportunities", []):
        ops.append({
            "title": op.get("title"),
            "savings_ms": op.get("savings_ms"),
            "description": op.get("description"),
            "display": op.get("display"),
        })
    # dedupe by title
    seen = {}
    for o in ops:
        key = o["title"]
        if key in seen:
            # prefer larger savings
            if (o.get("savings_ms") or 0) > (seen[key].get("savings_ms") or 0):
                seen[key] = o
        else:
            seen[key] = o
    ops_list = list(seen.values())
    ops_list = sorted(ops_list, key=lambda x: (x.get("savings_ms") or 0), reverse=True)

    if ops_list:
        for o in ops_list[:10]:
            s = o.get("savings_ms")
            s_str = f"{int(round(s))} ms" if s is not None else o.get("display") or ""
            with st.expander(f"{o.get('title')} — Savings: {s_str}"):
                st.write(o.get("description"))
    else:
        st.write("No opportunities detected.")

    st.markdown("---")
    st.subheader("Diagnostics")
    diag = []
    for d in mobile.get("diagnostics", []) + desktop.get("diagnostics", []):
        diag.append(d)
    # dedupe by title
    dseen = {}
    for d in diag:
        key = d.get("title")
        if key not in dseen:
            dseen[key] = d
    dlist = list(dseen.values())
    if dlist:
        for d in dlist[:20]:
            val = d.get("numeric")
            val_str = f"{val}" if val is not None else d.get("display") or ""
            with st.expander(f"{d.get('title')} — {val_str}"):
                st.write(d.get("description"))
    else:
        st.write("No diagnostics available.")


if analyse:
    if not site_url:
        st.error("Please provide a site URL to test.")
    else:
        # perform fetch (no cache-bust by default)
        with st.spinner("Fetching PageSpeed Insights for mobile and desktop..."):
            try:
                mobile, desktop = fetch_both(site_url, pagespeed_key, cache_bust=False)
            except Exception as e:
                st.error(f"Error fetching PageSpeed Insights: {e}")
                st.stop()
        show_results(mobile, desktop)
