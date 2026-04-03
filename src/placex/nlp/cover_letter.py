from __future__ import annotations

from typing import List, Optional

from huggingface_hub import InferenceClient

def generate_cover_letter(
    jd_text: str,
    resume_skills: List[str],
    missing_skills: List[str],
    hf_token: Optional[str] = None,
    model: str = "mistralai/Mistral-7B-Instruct-v0.3"
) -> str:
    """
    Generate a tailored cover letter using Hugging Face serverless inference.
    """
    client = InferenceClient(model=model, token=hf_token if hf_token else None)

    # Clean up and summarize inputs for prompt constraints
    jd_snippet = jd_text[:1000] if len(jd_text) > 1000 else jd_text
    r_skills_str = ", ".join(resume_skills[:20]) if resume_skills else "General Professional Skills"
    m_skills_str = ", ".join(missing_skills[:5]) if missing_skills else "None"

    prompt = f"""<s>[INST] You are an expert career coach and professional copywriter. 
Write a concise, compelling cover letter (around 3 paragraphs) for a candidate applying to this Job Description:
{jd_snippet}

The candidate HAS these skills: {r_skills_str}.
The candidate is MISSING these JD skills: {m_skills_str}.

Constraints:
1. Emphasize the skills they DO have and how they align with the role.
2. Directly but gracefully address the missing skills by highlighting them as areas the candidate is actively learning or capable of picking up quickly due to their core foundation.
3. Be professional, enthusiastic, and confident.
4. Use placeholders like [Your Name], [Company Name], and [Date]. 
5. Do NOT include ANY introductory or concluding conversational text (e.g. "Here is your cover letter"). Output ONLY the cover letter text.
[/INST]"""

    try:
        response = client.text_generation(
            prompt,
            max_new_tokens=600,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            do_sample=True,
            return_full_text=False
        )
        return response.strip()
    except Exception as e:
        raise RuntimeError(f"Hugging Face API error: {str(e)}")
