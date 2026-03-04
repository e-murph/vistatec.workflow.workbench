import os
from google import genai
import json

def batch_ai_qe_review(tu_batch):
    """
    Takes a batch of translation units (Source and Target) and uses Gemini 
    to evaluate semantic accuracy, flagging hallucinations or severe deviations.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {} 

    client = genai.Client(api_key=api_key)

    # Prepare the payload
    payload = ""
    for idx, item in enumerate(tu_batch):
        src = item.get('source', '')
        tgt = item.get('target', '')
        payload += f"ID:{idx} | Source: {src} | Target: {tgt}\n"

    prompt = f"""
    You are an expert localization Quality Assurance engineer. 
    Review this batch of translation units. 
    Identify if the Target text is a severe hallucination, drastically deviates from the Source meaning, or is pure garbage.
    Ignore minor stylistic choices; only flag severe, catastrophic translation failures.
    
    Respond STRICTLY in valid JSON format using the ID as the key.
    The value MUST be a dictionary with "action" ("Keep" or "Remove") and "reason" (a brief 1-sentence explanation if Remove, or empty if Keep).
    
    Example:
    {{
        "0": {{"action": "Keep", "reason": ""}},
        "1": {{"action": "Remove", "reason": "Target hallucinated extra instructions not present in source."}}
    }}

    Data to review:
    {payload}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # Clean and parse the JSON response
        response_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(response_text)
        
    except Exception as e:
        print(f"AI QE Error: {e}")
        return {}