

import json
import os
import re
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

from rag_retriever import retrieve_relevant_rules, format_rules_for_prompt


PROMPT_LOGS_DIR = Path(__file__).parent / "prompt_logs"
PROMPT_LOGS_DIR.mkdir(exist_ok=True)


def configure_gemini(api_key: str):

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            max_output_tokens=8192,
        )
    )



SYSTEM_PROMPT = """You are a senior web marketing analyst at a digital agency specializing in SEO, conversion rate optimization (CRO), and content strategy.

Your role is to analyze webpage audit data and provide specific, actionable insights.

STRICT RULES — follow these without exception:
1. ONLY reference data provided in the METRICS and KNOWLEDGE BASE sections
2. Never invent statistics, scores, or data points not provided to you
3. Every insight must cite a specific metric value (e.g., "With only 1 CTA for 1,243 words...")
4. Never give generic advice — be specific to this exact page's numbers
5. If a metric was not measured, say "not measured" — do not assume
6. Return ONLY valid JSON — no markdown, no explanations, no preamble

You ground all analysis in retrieved industry best practices from the knowledge base.
You are precise, direct, and always tie recommendations to measurable impact.
CRITICAL: Return raw JSON only. No backticks. No ```json. No markdown. Just the { } object.
"""


def build_analysis_prompt(metrics: dict, retrieved_rules_text: str) -> str:

    metrics_display = json.dumps(
        {k: v for k, v in metrics.items() if k != "content"},
        indent=2
    )

    return f"""Analyze this webpage audit. Return a JSON object only.

== FACTUAL METRICS (Extracted from page) ==
{metrics_display}

Word Count: {metrics['content']['word_count']}
Page Content Sample (first 3000 chars):
{metrics['content']['page_text_sample']}

{retrieved_rules_text}

== TASK: PASS 1 — ANALYSIS ==
Return ONLY this exact JSON structure:

{{
  "seo_analysis": "Specific analysis of SEO structure referencing exact metric values",
  "messaging_clarity": "Analysis of content clarity and messaging effectiveness",
  "cta_analysis": "Analysis of CTA usage referencing cta_count and word_count",
  "content_depth": "Analysis of content quality referencing word_count and heading structure",
  "ux_concerns": "Structural or UX issues observed from the metrics",
  "issues_found": [
    {{
      "domain": "SEO/CTA/Content/UX/Links/Images",
      "issue": "Specific issue description with metric value",
      "severity": "CRITICAL/HIGH/MEDIUM/LOW",
      "metric_reference": "The exact metric that flagged this issue"
    }}
  ]
}}"""


def build_recommendation_prompt(pass1_output: dict, metrics: dict) -> str:

    return f"""You previously analyzed a webpage and found these issues:

== PASS 1 ANALYSIS OUTPUT ==
{json.dumps(pass1_output, indent=2)}

== ORIGINAL METRICS (Reference) ==
Word Count: {metrics['content']['word_count']}
CTA Count: {metrics['cta']['cta_count']}
H1 Count: {metrics['seo']['h1_count']}
Missing Alt Text: {metrics['images']['missing_alt_pct']}%
Meta Title Length: {metrics['seo']['meta_title_length']} chars
Meta Description Length: {metrics['seo']['meta_description_length']} chars

== TASK: PASS 2 — PRIORITIZED RECOMMENDATIONS ==
Based on the analysis above, generate 3-5 prioritized recommendations.
Return ONLY this exact JSON structure:

{{
  "recommendations": [
    {{
      "priority": 1,
      "priority_level": "HIGH/MEDIUM/LOW",
      "action": "Specific actionable step (what to do exactly)",
      "reasoning": "Why this matters — reference the specific metric",
      "expected_impact": "What improvement this will create",
      "effort": "LOW/MEDIUM/HIGH"
    }}
  ],
  "overall_summary": "2-3 sentence executive summary of the page's audit health"
}}

Order recommendations by: severity first, then effort (quick wins before hard fixes)."""


def run_analysis(metrics: dict, api_key: str) -> dict:

    model = configure_gemini(api_key)

    retrieved_rules = retrieve_relevant_rules(metrics)
    retrieved_rules_text = format_rules_for_prompt(retrieved_rules)

    user_prompt_pass1 = build_analysis_prompt(metrics, retrieved_rules_text)

    full_prompt_pass1 = f"{SYSTEM_PROMPT}\n\n{user_prompt_pass1}"
    raw_response_pass1 = model.generate_content(full_prompt_pass1)
    raw_text_pass1 = raw_response_pass1.text
    
    #print("=== PASS 1 RAW RESPONSE ===")
    #print(raw_text_pass1)
    #print("===========================")

    pass1_output = safe_json_parse(raw_text_pass1)


    user_prompt_pass2 = build_recommendation_prompt(pass1_output, metrics)
    full_prompt_pass2 = f"{SYSTEM_PROMPT}\n\n{user_prompt_pass2}"
    raw_response_pass2 = model.generate_content(full_prompt_pass2)
    raw_text_pass2 = raw_response_pass2.text

    pass2_output = safe_json_parse(raw_text_pass2)

    combined = {**pass1_output, **pass2_output}

    log = {
        "timestamp": datetime.now().isoformat(),
        "url": metrics["url"],
        "rag_retrieved_rules_count": len(retrieved_rules),
        "rag_violated_rules_count": sum(1 for r in retrieved_rules if r.get("is_violated")),
        "pass1": {
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt_pass1,
            "raw_response": raw_text_pass1,
            "parsed_output": pass1_output,
        },
        "pass2": {
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt_pass2,
            "raw_response": raw_text_pass2,
            "parsed_output": pass2_output,
        },
        "retrieved_rules": retrieved_rules,
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = PROMPT_LOGS_DIR / f"audit_{timestamp}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    return combined, str(log_path), log

def safe_json_parse(text: str) -> dict:

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    text = text.strip()
    

    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "parse_error": True,
            "raw_output": text,
            "seo_analysis": "Could not parse AI response. See raw output.",
            "messaging_clarity": "",
            "cta_analysis": "",
            "content_depth": "",
            "ux_concerns": "",
            "issues_found": [],
            "recommendations": [],
            "overall_summary": "Parse error — check prompt logs for raw output.",
        }