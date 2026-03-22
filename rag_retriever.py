
import json
import os
from pathlib import Path


KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"


def load_knowledge_base() -> list[dict]:
    all_rules = []
    for json_file in KNOWLEDGE_BASE_DIR.glob("*.json"):
        with open(json_file, "r") as f:
            kb = json.load(f)
            for rule in kb.get("rules", []):
                rule["domain"] = kb["domain"]
            all_rules.extend(kb.get("rules", []))
    return all_rules


def retrieve_relevant_rules(metrics: dict) -> list[dict]:

    all_rules = load_knowledge_base()
    retrieved = []

    flat_metrics = {
        "h1_count": metrics["seo"]["h1_count"],
        "h2_count": metrics["seo"]["h2_count"],
        "h3_count": metrics["seo"]["h3_count"],
        "meta_title_length": metrics["seo"]["meta_title_length"],
        "meta_description_length": metrics["seo"]["meta_description_length"],
        "missing_alt_pct": metrics["seo"]["missing_alt_pct"],
        "word_count": metrics["content"]["word_count"],
        "cta_count": metrics["cta"]["cta_count"],
        "cta_density": metrics["cta"]["cta_density"],
        "internal_links": metrics["links"]["internal_count"],
        "external_links": metrics["links"]["external_count"],
        "image_count": metrics["images"]["total_count"],
    }

    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

    for rule in all_rules:
        prop = rule.get("property")
        good_range = rule.get("good_range", [])
        actual_value = flat_metrics.get(prop)

        if actual_value is not None and len(good_range) == 2:
            min_val, max_val = good_range
            is_violated = not (min_val <= actual_value <= max_val)

            retrieved.append({
                **rule,
                "actual_value": actual_value,
                "is_violated": is_violated,
                "status": " VIOLATED" if is_violated else " OK",
            })
        else:
            retrieved.append({
                **rule,
                "actual_value": actual_value,
                "is_violated": False,
                "status": "ℹ️ INFO",
            })

    retrieved.sort(
        key=lambda r: (
            0 if r["is_violated"] else 1,
            severity_order.get(r.get("severity", "LOW"), 3),
        )
    )

    return retrieved


def format_rules_for_prompt(retrieved_rules: list[dict]) -> str:

    lines = ["=== RETRIEVED INDUSTRY BEST PRACTICES (Knowledge Base) ===\n"]
    lines.append("Use these rules to ground your analysis. Reference them specifically.\n")

    for rule in retrieved_rules:
        status = rule.get("status", "")
        severity = rule.get("severity", "")
        domain = rule.get("domain", "")
        rule_text = rule.get("rule", "")
        reasoning = rule.get("reasoning", "")
        actual = rule.get("actual_value", "N/A")

        lines.append(
            f"[{status}] [{severity}] {domain}: {rule_text}\n"
            f"  → Actual value: {actual}\n"
            f"  → Why it matters: {reasoning}\n"
        )

    return "\n".join(lines)


def get_severity_scores(metrics: dict) -> dict:

    scores = {}


    seo_issues = 0
    if metrics["seo"]["h1_count"] != 1:
        seo_issues += 3
    if metrics["seo"]["meta_title_length"] < 50 or metrics["seo"]["meta_title_length"] > 60:
        seo_issues += 2
    if metrics["seo"]["meta_description_length"] < 150:
        seo_issues += 2
    if metrics["seo"]["missing_alt_pct"] > 10:
        seo_issues += 1

    scores["seo"] = {
        "score": max(0, 100 - (seo_issues * 12)),
        "severity": "CRITICAL" if seo_issues >= 5 else "WARNING" if seo_issues >= 2 else "GOOD",
    }


    wc = metrics["content"]["word_count"]
    content_score = 100 if wc >= 800 else 70 if wc >= 300 else 30
    scores["content"] = {
        "score": content_score,
        "severity": "GOOD" if content_score >= 80 else "WARNING" if content_score >= 50 else "CRITICAL",
    }


    cta = metrics["cta"]["cta_count"]
    cta_score = 100 if 1 <= cta <= 3 else 60 if cta > 3 else 0
    scores["cta"] = {
        "score": cta_score,
        "severity": "GOOD" if cta_score >= 80 else "WARNING" if cta_score >= 40 else "CRITICAL",
    }

    internal = metrics["links"]["internal_count"]
    link_score = 100 if internal >= 3 else 60 if internal >= 1 else 20
    scores["links"] = {
        "score": link_score,
        "severity": "GOOD" if link_score >= 80 else "WARNING" if link_score >= 40 else "CRITICAL",
    }

    missing_pct = metrics["images"]["missing_alt_pct"]
    img_score = 100 if missing_pct <= 10 else 60 if missing_pct <= 50 else 20
    scores["images"] = {
        "score": img_score,
        "severity": "GOOD" if img_score >= 80 else "WARNING" if img_score >= 40 else "CRITICAL",
    }

    overall = round(sum(v["score"] for v in scores.values()) / len(scores))
    scores["overall"] = {
        "score": overall,
        "severity": "GOOD" if overall >= 75 else "WARNING" if overall >= 50 else "CRITICAL",
    }

    return scores
