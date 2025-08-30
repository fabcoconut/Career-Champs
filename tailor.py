from typing import Dict, Any
from openai import OpenAI
from utils_secrets import get_secret

LOCAL_TEMPLATE = """
**Tailored CV Bullets**
- Led {top_skill} initiatives impacting {impact_area}, delivering {outcome}.
- Built {tooling} to {action}, improving {metric}%.
- Partnered with {stakeholders} to {verb} {domain} strategy.

**Cover Letter**
Dear Hiring Manager,

I'm excited to apply for the {title} role at {company}. With a background in {bg}, I have delivered {key_win}. This aligns with your need for {need}.

In previous roles, I:
{bullets}

I’d love to bring this to {company}.

Best,
{your_name}
"""

def extract_simple_skills(cv_text: str):
    t = (cv_text or "").lower()
    skills = []
    for k in ["python","sql","excel","tableau","power bi","financial modeling","valuation","dcf","market research","portfolio","regression","ml","data visualization"]:
        if k in t: skills.append(k)
    return skills[:8] or ["analysis","modeling"]

def local_tailor(cv_text: str, job: Dict[str, Any], your_name: str="Candidate"):
    skills = extract_simple_skills(cv_text)
    bullets = [
        f"Delivered measurable impact using {skills[0]} on {job.get('title','the role')} requirements",
        "Built automated workflows that cut manual effort by 30%+",
        "Produced exec-ready insights that informed investment decisions"
    ]
    return LOCAL_TEMPLATE.format(
        top_skill=skills[0], impact_area="growth", outcome="double-digit improvements",
        tooling=skills[0], action="accelerate analysis", metric=30, stakeholders="investors & leadership",
        verb="shape", domain="investment", title=job.get("title","this"), company=job.get("company","the company"),
        bg="data-driven analysis and strategy", key_win="high-confidence decisions with clear ROI",
        need="analytical rigor and actionable insights", bullets="\n- " + "\n- ".join(bullets), your_name=your_name
    )

def openai_tailor(cv_text: str, job: Dict[str, Any], your_name: str="Candidate"):
    key = get_secret("OPENAI_API_KEY")
    if not key:
        return None
    client = OpenAI(api_key=key)
    prompt = f"""You are a concise career coach. Using the CV and job data, produce 3 tailored bullet points and a short, punchy cover letter (<=200 words). Avoid fluff.
CV:
{(cv_text or '')[:6000]}

JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Desc: {(job.get('description','') or '')[:2000]}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"Be specific and quant-driven."},
                  {"role":"user","content": prompt}],
        temperature=0.4
    )
    return resp.choices[0].message.content.strip()
