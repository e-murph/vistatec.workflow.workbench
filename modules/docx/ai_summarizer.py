import os
from google import genai

def generate_executive_summary(all_changes):
    """
    Takes a list of extracted DOCX changes and uses Google Gemini to generate a summary.
    """
    # 1. Securely load the API key
    api_key = os.getenv("GEMINI_API_KEY") 
    
    if not api_key:
        return "⚠️ **Configuration Error:** GEMINI_API_KEY not found in secrets."

    # 2. Configure the new Gemini Client
    client = genai.Client(api_key=api_key)

    # 3. Format the changes so the LLM understands them
    # Limit to the first 100 changes to keep it concise
    formatted_diffs = ""
    for i, (filename, orig, edit, html) in enumerate(all_changes[:100]):
        formatted_diffs += f"Original: {orig}\nEdited: {edit}\n---\n"

    if len(all_changes) > 100:
        formatted_diffs += f"\n...and {len(all_changes) - 100} more minor changes."

    # 4. Construct the Prompt
    prompt = f"""
    You are an expert localization Project Manager. 
    Review the following tracked changes extracted from translated documents.
    Provide a concise, 2-to-3 paragraph 'Executive Summary' of the substantive changes.
    Ignore minor stylistic edits (like punctuation or single-word grammar fixes).
    Focus on major meaning shifts, terminology updates, or structural changes.
    Format your response using Markdown bullet points.

    Here are the document changes:
    {formatted_diffs}
    """

    # 5. Call the LLM using the new syntax
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt
        )
        return response.text
        
    except Exception as e:
        return f"❌ **AI Processing Error:** {str(e)}"