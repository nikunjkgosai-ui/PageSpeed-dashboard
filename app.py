import streamlit as st
import os
from datetime import date, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
from fetchers import fetch_pagespeed

st.set_page_config(page_title="PageSpeed Dashboard", layout="wide")

st.title("PageSpeed Insights Dashboard")

# Detect theme from Streamlit config
is_dark_theme = st.get_option("theme.base") == "dark"

# Define colors based on theme
if is_dark_theme:
    cwv_bg = "#0f172a"
    cwv_bg_accent = "#1e293b"
    cwv_card = "#111827"
    cwv_card_border = "#243244"
    cwv_text = "#f8fafc"
    cwv_muted = "#94a3b8"
    cwv_shadow = "0 12px 28px rgba(15, 23, 42, 0.4)"
    cwv_icon = "#cbd5f5"
else:
    cwv_bg = "#f8fbff"
    cwv_bg_accent = "#fef5ec"
    cwv_card = "#ffffff"
    cwv_card_border = "#e4e9f1"
    cwv_text = "#0f172a"
    cwv_muted = "#6b7280"
    cwv_shadow = "0 12px 24px rgba(15, 23, 42, 0.08)"
    cwv_icon = "#475569"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {{
  --cwv-bg: {cwv_bg};
  --cwv-bg-accent: {cwv_bg_accent};
  --cwv-card: {cwv_card};
  --cwv-card-border: {cwv_card_border};
  --cwv-text: {cwv_text};
  --cwv-muted: {cwv_muted};
  --cwv-shadow: {cwv_shadow};
  --cwv-icon: {cwv_icon};
}}

.stApp {{
  background: radial-gradient(1100px 520px at 8% -8%, var(--cwv-bg-accent) 0%, var(--cwv-bg) 35%, var(--cwv-card) 70%);
  color: var(--cwv-text);
  font-family: "Space Grotesk", sans-serif;
}}

.cwv-section {{
  margin-top: 6px;
  margin-bottom: 8px;
}}

.cwv-title {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--cwv-text);
}}

.cwv-grid {{
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}}

@media (max-width: 1200px) {{
  .cwv-grid {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}

@media (max-width: 700px) {{
  .cwv-grid {{
    grid-template-columns: 1fr;
  }}
}}

.cwv-card {{
  background: var(--cwv-card);
  border: 1px solid var(--cwv-card-border);
  border-radius: 18px;
  padding: 22px 22px 18px;
  box-shadow: var(--cwv-shadow);
}}

.cwv-card-header {{
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--cwv-icon);
  font-weight: 600;
  font-size: 0.95rem;
}}

.cwv-icon {{
  width: 22px;
  height: 22px;
  stroke: var(--cwv-icon);
}}

.cwv-value {{
  margin-top: 10px;
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--cwv-text);
}}

.cwv-subtitle {{
  margin-top: 6px;
  font-size: 0.86rem;
  color: var(--cwv-muted);
}}
</style>
""",
    unsafe_allow_html=True,
)

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
        st.markdown("<div style='height: 1.7em'></div>", unsafe_allow_html=True)
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

    def fmt_metric(metrics, key):
        val = metrics.get(key, {})
        numeric = val.get("numeric_ms") if isinstance(val, dict) else None
        display = val.get("display") if isinstance(val, dict) else val
        if numeric is not None:
            if numeric >= 1000:
                return f"{numeric / 1000:.2f} s"
            return f"{int(round(numeric))} ms"
        if display:
            return str(display)
        return "N/A"

    cwv_icons = {
        "clock": """
<svg class="cwv-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="9"></circle>
  <path d="M12 7v5l3 2"></path>
</svg>
""",
        "bolt": """
<svg class="cwv-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M13 2L3 14h7l-1 8 12-14h-7l-1-6z"></path>
</svg>
""",
        "grid": """
<svg class="cwv-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="3" width="7" height="7" rx="1"></rect>
  <rect x="14" y="3" width="7" height="7" rx="1"></rect>
  <rect x="3" y="14" width="7" height="7" rx="1"></rect>
  <rect x="14" y="14" width="7" height="7" rx="1"></rect>
</svg>
""",
        "pulse": """
<svg class="cwv-icon" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 12h4l2-5 4 10 2-5h6"></path>
</svg>
""",
    }

    # Show Performance Scores first
    st.subheader("Performance Scores")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Mobile Performance", f"{m_score if m_score is not None else 'N/A'}", delta=(round(delta, 1) if delta is not None else None))
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

    # Core Web Vitals & Metrics split 50/50 between Mobile and Desktop
    metric_keys = [
        ("first-contentful-paint", "First Contentful Paint", "Time until first content appears", cwv_icons["clock"]),
        ("largest-contentful-paint", "Largest Contentful Paint", "Time until main content loads", cwv_icons["bolt"]),
        ("cumulative-layout-shift", "Cumulative Layout Shift", "Visual stability score", cwv_icons["grid"]),
        ("speed-index", "Speed Index", "How quickly content is displayed", cwv_icons["pulse"]),
    ]

    st.markdown(
        f"""
<section class="cwv-section">
  <div class="cwv-title">
    <span>{cwv_icons["pulse"]}</span>
    <span>Core Web Vitals & Metrics</span>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )

    # Display metrics in two columns: Mobile and Desktop
    col_m, col_d = st.columns(2)

    with col_m:
        st.markdown("**Mobile Metrics**")
        mobile_cards = []
        for key, label, subtitle, icon in metric_keys:
            mobile_cards.append({
                "label": label,
                "value": fmt_metric(mobile.get("metrics", {}), key),
                "subtitle": subtitle,
                "icon": icon,
            })
        mobile_cards_html = "\n".join(
            [
                f"""
<div class="cwv-card">
  <div class="cwv-card-header">{card["icon"]}<span>{card["label"]}</span></div>
  <div class="cwv-value">{card["value"]}</div>
  <div class="cwv-subtitle">{card["subtitle"]}</div>
</div>
"""
                for card in mobile_cards
            ]
        )
        st.markdown(
            f"""
<div class="cwv-grid" style="grid-template-columns: repeat(2, minmax(0, 1fr));">
  {mobile_cards_html}
</div>
""",
            unsafe_allow_html=True,
        )

    with col_d:
        st.markdown("**Desktop Metrics**")
        desktop_cards = []
        for key, label, subtitle, icon in metric_keys:
            desktop_cards.append({
                "label": label,
                "value": fmt_metric(desktop.get("metrics", {}), key),
                "subtitle": subtitle,
                "icon": icon,
            })
        desktop_cards_html = "\n".join(
            [
                f"""
<div class="cwv-card">
  <div class="cwv-card-header">{card["icon"]}<span>{card["label"]}</span></div>
  <div class="cwv-value">{card["value"]}</div>
  <div class="cwv-subtitle">{card["subtitle"]}</div>
</div>
"""
                for card in desktop_cards
            ]
        )
        st.markdown(
            f"""
<div class="cwv-grid" style="grid-template-columns: repeat(2, minmax(0, 1fr));">
  {desktop_cards_html}
</div>
""",
            unsafe_allow_html=True,
        )

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
