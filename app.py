

import streamlit as st
import json
import os
from dotenv import load_dotenv

from scraper import extract_metrics
from ai_analysis import run_analysis
from rag_retriever import get_severity_scores, retrieve_relevant_rules

load_dotenv()

st.set_page_config(
    page_title="WebAudit AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'Space Grotesk', sans-serif; }
code, .mono { font-family: 'JetBrains Mono', monospace; }

.main { background: #0a0a0f; }
.block-container { padding: 2rem 3rem; max-width: 1400px; }

/* Header */
.audit-header {
    background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a0a0f 100%);
    border: 1px solid #2d1b69;
    border-radius: 16px;
    padding: 3rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.audit-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99,51,255,0.08) 0%, transparent 60%);
    pointer-events: none;
}
.audit-title {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #6333ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.audit-subtitle {
    color: #6b7280;
    font-size: 1rem;
    font-weight: 400;
}

/* Metric Cards */
.metric-card {
    background: #111118;
    border: 1px solid #1f1f2e;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #6333ff44; }
.metric-label {
    color: #6b7280;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.25rem;
}
.metric-value {
    color: #ffffff;
    font-size: 1.6rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.metric-sub {
    color: #4b5563;
    font-size: 0.8rem;
    margin-top: 0.2rem;
}

/* Score Badge */
.score-badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
}
.score-good { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.score-warning { background: #1c1400; color: #fbbf24; border: 1px solid #854d0e; }
.score-critical { background: #1c0505; color: #f87171; border: 1px solid #991b1b; }

/* Section Headers */
.section-header {
    color: #a78bfa;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1f1f2e;
}

/* Insight Cards */
.insight-card {
    background: #0d0d16;
    border: 1px solid #1f1f2e;
    border-left: 3px solid #6333ff;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}
.insight-title {
    color: #a78bfa;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.insight-text { color: #d1d5db; font-size: 0.9rem; line-height: 1.6; }

/* Recommendation Cards */
.rec-card {
    background: #0d0d16;
    border: 1px solid #1f1f2e;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 0.75rem;
}
.rec-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}
.priority-badge {
    background: #6333ff22;
    color: #a78bfa;
    border: 1px solid #6333ff44;
    border-radius: 4px;
    padding: 0.15rem 0.5rem;
    font-size: 0.7rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.rec-action { color: #ffffff; font-weight: 600; font-size: 0.95rem; }
.rec-detail { color: #9ca3af; font-size: 0.85rem; margin-top: 0.3rem; line-height: 1.5; }
.effort-tag {
    display: inline-block;
    background: #1f1f2e;
    color: #6b7280;
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    font-size: 0.7rem;
    margin-top: 0.5rem;
}

/* RAG Tag */
.rag-tag {
    display: inline-block;
    background: #0c1a0c;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 4px;
    padding: 0.1rem 0.5rem;
    font-size: 0.65rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    vertical-align: middle;
    margin-left: 0.4rem;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid #1f1f2e;
    margin: 2rem 0;
}

/* Overall Score Circle */
.score-circle {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    margin: 0 auto;
    font-family: 'JetBrains Mono', monospace;
}
</style>
""", unsafe_allow_html=True)



def severity_css(severity: str) -> str:
    mapping = {"GOOD": "score-good", "WARNING": "score-warning", "CRITICAL": "score-critical"}
    return mapping.get(severity, "score-warning")


def severity_emoji(severity: str) -> str:
    return {"GOOD": "🟢", "WARNING": "🟡", "CRITICAL": "🔴"}.get(severity, "🟡")


def render_metric_card(label: str, value, sub: str = ""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {"<div class='metric-sub'>" + sub + "</div>" if sub else ""}
    </div>
    """, unsafe_allow_html=True)


def render_score_badge(score: int, severity: str):
    css = severity_css(severity)
    emoji = severity_emoji(severity)
    return f'<span class="score-badge {css}">{emoji} {score}/100 — {severity}</span>'


st.markdown("""
<div class="audit-header">
    <div class="audit-title">🔍 WebAudit AI</div>
    <div class="audit-subtitle">
        RAG-powered website analysis · Grounded in industry best practices · Multi-pass AI reasoning
    </div>
</div>
""", unsafe_allow_html=True)




api_key = os.getenv("GEMINI_API_KEY", "")

url_input = st.text_input(
    "Website URL to Audit",
    placeholder="https://example.com",
)

analyze_btn = st.button(" Run Audit", type="primary", use_container_width=True)


if analyze_btn:
    #if not api_key:
    #    st.error("Please enter your Gemini API key.")
    if not url_input:
        st.error("Please enter a URL to analyze.")
    else:
        with st.spinner(" Extracting page metrics..."):
            try:
                metrics = extract_metrics(url_input)
                st.success(" Metrics extracted successfully")
            except Exception as e:
                st.error(f"Failed to fetch page: {e}")
                st.stop()

        scores = get_severity_scores(metrics)
        retrieved_rules = retrieve_relevant_rules(metrics)
        violated_count = sum(1 for r in retrieved_rules if r.get("is_violated"))

        with st.spinner(" Running AI analysis (Diagnosis)..."):
            try:
                ai_results, log_path, full_log = run_analysis(metrics, api_key)
                st.success(f" AI analysis complete · Prompt log saved")
            except Exception as e:
                st.error(f"AI analysis failed: {e}")
                st.stop()

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.markdown('<div class="section-header"> Audit Overview</div>', unsafe_allow_html=True)

        overview_cols = st.columns(6)
        domains = ["overall", "seo", "content", "cta", "links", "images"]
        labels = ["Overall", "SEO", "Content", "CTA", "Links", "Images"]

        for col, domain, label in zip(overview_cols, domains, labels):
            score_data = scores[domain]
            css = severity_css(score_data["severity"])
            emoji = severity_emoji(score_data["severity"])
            with col:
                st.markdown(f"""
                <div class="metric-card" style="text-align:center;">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{score_data['score']}</div>
                    <div class="metric-sub">
                        <span class="score-badge {css}">{emoji} {score_data['severity']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#0d0d16; border:1px solid #1f1f2e; border-radius:8px; padding:1rem; margin:1rem 0;">
            <span style="color:#9ca3af; font-size:0.85rem;">
                <strong style="color:#a78bfa;">RAG Knowledge Base</strong>: 
                {len(retrieved_rules)} rules retrieved · 
                <strong style="color:#f87171;">{violated_count} violations detected</strong>
                <span class="rag-tag">RAG-GROUNDED</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.markdown('<div class="section-header"> Factual Metrics </div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**SEO**")
            render_metric_card("Meta Title", metrics["seo"]["meta_title"] or "MISSING",
                               f"{metrics['seo']['meta_title_length']} chars (ideal: 50–60)")
            render_metric_card("Meta Description",
                               metrics["seo"]["meta_description"][:60] + "..." if metrics["seo"]["meta_description"] else "MISSING",
                               f"{metrics['seo']['meta_description_length']} chars (ideal: 150–160)")
            render_metric_card("H1 / H2 / H3",
                               f"{metrics['seo']['h1_count']} / {metrics['seo']['h2_count']} / {metrics['seo']['h3_count']}")

        with col2:
            st.markdown("**Content & CTAs**")
            render_metric_card("Word Count", f"{metrics['content']['word_count']:,}",
                               "Min 300 for SEO · Ideal 800–1500")
            render_metric_card("CTAs Found", metrics["cta"]["cta_count"],
                               f"Examples: {', '.join(metrics['cta']['cta_examples'][:2]) or 'None detected'}")
            render_metric_card("CTA Density", f"{metrics['cta']['cta_density']:.4f}",
                               "CTAs per word (ideal: 0.003–0.01)")

        with col3:
            st.markdown("**Links & Images**")
            render_metric_card("Internal Links", metrics["links"]["internal_count"],
                               "Should be ≥ 3")
            render_metric_card("External Links", metrics["links"]["external_count"])
            render_metric_card("Images", metrics["images"]["total_count"],
                               f"{metrics['images']['missing_alt_pct']}% missing alt text")

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="section-header">
            AI Insights Analysis
            <span class="rag-tag">RAG-GROUNDED</span>
        </div>
        """, unsafe_allow_html=True)

        if ai_results.get("overall_summary"):
            st.markdown(f"""
            <div style="background:#1a0a2e; border:1px solid #6333ff44; border-radius:10px; padding:1.2rem; margin-bottom:1.5rem;">
                <div style="color:#a78bfa; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">Executive Summary</div>
                <div style="color:#e5e7eb; font-size:0.95rem; line-height:1.7;">{ai_results.get("overall_summary", "")}</div>
            </div>
            """, unsafe_allow_html=True)

        insight_col1, insight_col2 = st.columns(2)

        insights = [
            ("SEO Structure", "seo_analysis"),
            ("Messaging Clarity", "messaging_clarity"),
            ("CTA Usage", "cta_analysis"),
            ("Content Depth", "content_depth"),
        ]

        for i, (title, key) in enumerate(insights):
            col = insight_col1 if i % 2 == 0 else insight_col2
            with col:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">{title}</div>
                    <div class="insight-text">{ai_results.get(key, "Not analyzed")}</div>
                </div>
                """, unsafe_allow_html=True)

        if ai_results.get("ux_concerns"):
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: #f59e0b;">
                <div class="insight-title"> UX & Structural Concerns</div>
                <div class="insight-text">{ai_results.get("ux_concerns", "")}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.markdown('<div class="section-header">Prioritized Recommendations</div>', unsafe_allow_html=True)

        recommendations = ai_results.get("recommendations", [])
        priority_colors = {
            "HIGH": "#f87171",
            "MEDIUM": "#fbbf24",
            "LOW": "#4ade80"
        }

        for rec in recommendations:
            priority_level = rec.get("priority_level", "MEDIUM")
            color = priority_colors.get(priority_level, "#a78bfa")

            st.markdown(f"""
            <div class="rec-card" style="border-left: 3px solid {color};">
                <div class="rec-header">
                    <span class="priority-badge">#{rec.get("priority", "?")} PRIORITY</span>
                    <span class="score-badge" style="background:#1c0505; color:{color}; border-color:{color}44;">
                        {priority_level}
                    </span>
                    <span class="effort-tag">Effort: {rec.get("effort", "?")}</span>
                </div>
                <div class="rec-action">→ {rec.get("action", "")}</div>
                <div class="rec-detail">
                    <strong style="color:#9ca3af;">Why:</strong> {rec.get("reasoning", "")}<br>
                    <strong style="color:#9ca3af;">Impact:</strong> {rec.get("expected_impact", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        with st.expander("RAG Knowledge Base — Rules Retrieved & Applied"):
            st.markdown(f"**{len(retrieved_rules)} rules retrieved · {violated_count} violations**")
            for rule in retrieved_rules:
                status_color = "#f87171" if rule.get("is_violated") else "#4ade80"
                st.markdown(f"""
                <div style="background:#0d0d16; border:1px solid #1f1f2e; border-left:3px solid {status_color}; 
                            border-radius:6px; padding:0.75rem; margin-bottom:0.5rem;">
                    <span style="color:{status_color}; font-size:0.7rem; font-family:monospace; font-weight:700;">
                        {rule.get("status","")} [{rule.get("severity","")}] {rule.get("domain","")}
                    </span><br>
                    <span style="color:#d1d5db; font-size:0.85rem;">{rule.get("rule","")}</span><br>
                    <span style="color:#6b7280; font-size:0.8rem;">Actual: {rule.get("actual_value","N/A")}</span>
                </div>
                """, unsafe_allow_html=True)


else:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; color: #4b5563;">
        <div style="font-size: 4rem; margin-bottom: 1rem;"></div>
        <div style="font-size: 1.1rem; color: #6b7280;">
            Enter a URL above and click <strong style="color:#a78bfa;">Run Audit</strong> to begin
        </div>
        <div style="margin-top: 2rem; display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
            <div style="background:#111118; border:1px solid #1f1f2e; border-radius:10px; padding:1rem 1.5rem; max-width:180px;">
                <div style="font-size:1.5rem;"></div>
                <div style="color:#d1d5db; font-size:0.85rem; margin-top:0.5rem;">7 Factual Metrics Extracted</div>
            </div>
            <div style="background:#111118; border:1px solid #1f1f2e; border-radius:10px; padding:1rem 1.5rem; max-width:180px;">
                <div style="font-size:1.5rem;"></div>
                <div style="color:#d1d5db; font-size:0.85rem; margin-top:0.5rem;">RAG Knowledge Base Grounding</div>
            </div>
            <div style="background:#111118; border:1px solid #1f1f2e; border-radius:10px; padding:1rem 1.5rem; max-width:180px;">
                <div style="font-size:1.5rem;"></div>
                <div style="color:#d1d5db; font-size:0.85rem; margin-top:0.5rem;">Multi-Pass AI Reasoning</div>
            </div>
            <div style="background:#111118; border:1px solid #1f1f2e; border-radius:10px; padding:1rem 1.5rem; max-width:180px;">
                <div style="font-size:1.5rem;"></div>
                <div style="color:#d1d5db; font-size:0.85rem; margin-top:0.5rem;">Full Prompt Logs Saved</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
