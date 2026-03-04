import os
from google import genai
import json

def batch_ai_term_review(terms_to_review, lang1, lang2):
    """
    Takes a batch of imperfect term matches and missing definitions, 
    and uses Gemini to evaluate semantics and generate definitions.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {} # Fails silently and safely if no key is found

    # NEW SDK INITIALIZATION
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
        # NEW SDK GENERATE CONTENT CALL
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        
        # Clean the response to ensure it parses as JSON
        response_text = response.text.replace("```json", "").replace("```", "").strip()
        ai_insights = json.loads(response_text)
        return ai_insights
    except Exception as e:
        print(f"AI Error: {e}")
        return {}