import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY", "")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.1,
        max_output_tokens=2048,
    )
)


test_prompt = """
You are a web analyst. Return ONLY valid JSON, no markdown, no extra text.

Analyze this fake webpage data:
- Word Count: 901
- H1 Count: 0
- CTA Count: 10
- Missing Alt Text: 72.9%

Return exactly this structure:
{
  "seo_analysis": "your analysis here",
  "messaging_clarity": "your analysis here",
  "cta_analysis": "your analysis here",
  "content_depth": "your analysis here",
  "ux_concerns": "your analysis here"
}
"""

print("Sending test prompt to Gemini...")
print("=" * 50)

response = model.generate_content(test_prompt)
raw_text = response.text

print("RAW RESPONSE FROM GEMINI:")
print(raw_text)
print("=" * 50)


raw_clean = re.sub(r"```json\s*", "", raw_text)
raw_clean = re.sub(r"```\s*", "", raw_clean)
raw_clean = raw_clean.strip()

start = raw_clean.find("{")
end = raw_clean.rfind("}") + 1
if start != -1 and end > start:
    raw_clean = raw_clean[start:end]

try:
    parsed = json.loads(raw_clean)
    print("✅ JSON PARSED SUCCESSFULLY!")
    print(json.dumps(parsed, indent=2))
except json.JSONDecodeError as e:
    print(f"❌ PARSE FAILED: {e}")
    print("Cleaned text was:")
    print(raw_clean)