#  WebAudit AI — RAG-Powered Website Audit Tool

#  Live Demo

> https://webaudit-ai.streamlit.app/



#  Architecture 

                    USER INPUT (URL)                        

                         │|
                         \/

 LAYER 1 — scraper.py - data extraction                            
                                                             
  • Fetches raw HTML using requests                           
  • Parses HTML with BeautifulSoup                            
  • Extracts 7 factual metric categories                      
  • Organizes metrics by domain (SEO, Content, CTA,Links, Images)                 
  • Returns a clean structured Python dict                    

                            │|
                            ||
                            \/

  LAYER 2a — rag_retriever.py - Lightweight RAG + Rule-Based Pre-Scoring.                   
                                                              
  • Loads 3 knowledge base JSON files                         
    (seo_rules, cta_rules, content_ux_rules)                  
  • Matches rules to extracted metrics                        
  • Flags violated rules with severity levels                 
  • Pre-scores each domain (CRITICAL / WARNING / GOOD)        
  • Formats retrieved rules for prompt injection              

                            │|
                            ||
                            \/

  LAYER 2b — ai_analysis.py - Multi-Pass LLM Analysis using Google Gemini 2.5 Flash       
                                                              
  PASS 1                                           
  Input:  Metrics + RAG-retrieved best practice rules         
  Output: Structured JSON with 5 domain insights + list of flagged issues                              
                            │|
                            ||
                            \/                               
  PASS 2                                       
  Input:  Pass 1 output + original metrics                    
  Output: 3-5 prioritized recommendations with effort ratings + executive summary                  
  Every run saves a full prompt log to prompt_logs/         

                            │|
                            ||
                            \/

  LAYER 3 — app.py - Streamlit UI.                                                                  
  • URL input field                                           
  • Domain score overview       
  • Factual metrics display       
  • AI insights                           
  • Prioritized recommendations              
  • RAG rules applied                           



# AI Design Decisions

# 1. Used Lightweight RAG System

I have used a simple lightweight rag system with the help of knowledge based and inject them into prompt. Because we cannot audit based on trainig data.
we have to follow the rules and guidelines. Therefore i have takes different guidlines and rules from different organization which are industry standards
for auditing.
Also another reason im using this kind of knowlege based is according to your organization we can edit or changed the rules and guidlines. So I think 
this would be great for a organization like EIGHT25MEDIA

these are the some of the standard guidelines i found :
- Meta description should be 150–160 characters — **Google Search Central documentation**
- Alt text on images — **WCAG 2.1 Accessibility Standards**
- Minimum 300 words — **Yoast SEO + Google thin content guidelines**
- 800–1500 words for optimal traffic — **HubSpot research**
- 1 CTA per 300 words — **Nielsen Norman Group UX research**


# this is how it works
Knowledge Base (3 JSON files)
├── seo_rules.json       → 6 rules with numeric thresholds + sources
├── cta_rules.json       → 3 CTA benchmarks
└── content_ux_rules.json → 5 content and UX standards

Retrieval Step:
*For each rule, compare actual metric value against good_range
*Flag rules where actual value is outside the good range
*Sort by: violated first, then by severity (CRITICAL → HIGH → MEDIUM → LOW)

Augmentation Step:
*Inject retrieved rules into the prompt as context
*AI reasons against real benchmarks, not training data guesses


# 2. Multi-Pass Prompting 

Instead of one large prompt asking for everything at once, I have uses two sequential AI layer.

# Pass 1
The AI gets the extracted metrics and the RAG-retrieved rules. Its only job is to analyze and find issues across 5 domains — SEO structure, messaging clarity, CTA usage, content depth, and UX concerns. It is going to just diagnose them.

# Pass 2

The AI gets the full Pass 1 analysis as its input. Now its only job is to prioritize those issues into actionable recommendations, each with an effort rating 
(LOW / MEDIUM / HIGH) and expected impact.

in simple terms what happening here is first AI is reasoning about the problem and then produce the recommendations

# 3. Rule-Based Pre-Scoring 

Before any AI call, each metric domain is scored using the logic in `rag_retriever.py`. Each domain gets a score out of 100 and a severity label 
(GOOD / WARNING / CRITICAL).

This pre-scoring serves two purposes:
- First it gives the user an instant visual overview of the page health
- This prevents the AI from downplaying serious issues or exaggerating minor ones.



# 4. Structured JSON Output

Both AI passes are instructed to return only a valid JSON object — no introduction, no explanation, no markdown formatting.
The reason is , If the AI returns free text I cannot reliably display it in the Streamlit UI. I need to know exactly where the SEO analysis ends and where the CTA analysis begins. JSON gives me that structure predictably every time. Once parsed I can loop through each field and render it cleanly in the correct section of the UI.


# 5. Low Temperature (0.1)

Temperature controls how creative vs consistent the AI is.  A temperature of 1.0 means the AI will give you a different response every time you ask the same question. A temperature of 0.0 means it gives you almost the same response every time.
For analytical tasks like this, a low temperature (0.1) is appropriate because:

- An audit tool should give consistent results. If you run the same URL twice you should get similar findings, not completely different ones
- Factual analysis should not vary based on randomness
- Higher temperatures increase the risk of the AI inventing numbers or drifting away from the metrics it was given


# 6. Multi-Layer Strategy for hallucination prevention

# Layer 1 — RAG Grounding
The AI only sees metrics that were actually extracted from the page. Real benchmarks are injected directly into the prompt so the AI references those instead of making up its own.
# Layer 2 — System Prompt Constraints
The AI is explicitly told: "Only use data provided to you. Never invent numbers. If something wasn't measured, say 'not measured'."
# Layer 3 — Rule-Based Pre-Scoring
Severity levels (CRITICAL / WARNING / GOOD) are calculated by Python code before the AI is involved. The AI cannot override or contradict these — they are set by logic, not by the AI's judgment.
# Layer 4 — Low Temperature (0.1)
A low temperature setting keeps the AI consistent and factual. The higher the temperature, the more creative and unpredictable the AI becomes — which is the last thing you want in an audit tool.
# Layer 5 — Prompt Logging
Every prompt sent and every response received is saved as a JSON file. If the AI ever does hallucinate something, it can be traced and audited immediately.



#  Trade-offs

1. Used Python tool called BeautifulSoup over Selenium - Fast and simple but Cannot scrape JavaScript-heavy websites
2. JSON Knowledge Base over Vector Database - No extra setup needed, fully transparent but cannot do smart semantic search,only exact rule matching
3. Gemini 2.5 Flash over GPT-4 - Completely free but GPT-4 gives slightly better quality analysis
4. Page Text Truncated to 3000 Characters - Keeps the prompt clean and within limits but Very long pages may have content that gets cut off
5. Two AI Passes over One - Better quality analysis and recommendations but Takes twice as long and uses more API tokens
6. Rule-Based RAG over Embeddings - Simple, explainable, no infrastructure needed but Cannot match rules by meaning only by exact metric name

# What I Would Improve With More Time

1. Selenium or Playwright Support
BeautifulSoup cannot read websites built with JavaScript frameworks like React or Vue. Adding a headless browser would allow the scraper to read any modern website correctly.
2. Semantic Embeddings in RAG
Currently rules are matched by exact metric names. With embeddings, rules would be matched by meaning — making retrieval smarter and more flexible even when there is no exact match.
3. Add More Knowledge Base Rules
Just add more rules to the JSON files then it will becomes better and more detailed recommendations.
4. Score History With CSV
Append each audit score to a CSV file and display a trend chart in Streamlit this will track how a page improves over time.
5. Google PageSpeed API
One free API call that adds page speed and Core Web Vitals to the audit.
6. Compare Two URLs
Add a second URL input and show both audit scores side by side.this will useful for comparing a client site against a competitor.
7. Better CTA Detection
Improve the CTA keyword list to catch more button types accurately. 


