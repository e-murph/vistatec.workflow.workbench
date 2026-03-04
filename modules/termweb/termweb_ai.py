import os
from google import genai
import json
import re

def batch_ai_term_review(terms_to_review, lang1, lang2):
    """
    Takes a batch of imperfect term matches and missing definitions, 
    and uses Gemini to evaluate semantics and generate definitions.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {} 

    client = genai.Client(api_key=api_key)

    # Prepare the payload for the prompt
    payload = ""
    for idx, row in enumerate(terms_to_review):
        t1 = row.get('t1', '')
        t2 = row.get('t2', '')
        missing_def = row.get('missing_def', False)
        payload += f"ID:{idx} | {lang1}: {t1} | {lang2}: {t2} | Needs Definition: {missing_def}\n"

    prompt = f"""
    You are an expert localization terminologist. Review this batch of terminology data.
    Some pairs have low lexical match scores. Tell me if they are actually valid synonyms or accurate translations.
    If 'Needs Definition' is True, provide a concise, professional, 1-sentence dictionary definition for the {lang1} term.
    
    Respond STRICTLY in valid JSON format using the ID as the key.
    Example:
    {{
        "0": "AI: Valid Synonym. Def: A global computer network.",
        "1": "AI: Incorrect translation. Def: N/A"
    }}

    Data to review:
    {payload}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        
        # JSON extraction using Regex
        response_text = response.text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            ai_insights = json.loads(json_match.group(0))
            return ai_insights
        else:
            print("AI Error: No JSON block found in response.")
            return {}
            
    except Exception as e:
        print(f"AI Error: {e}")
        return {}