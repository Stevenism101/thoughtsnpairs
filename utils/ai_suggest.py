import json
import os

def analyze_pairing(item_1, item_2, description):
    """
    Call Claude API to get tag suggestions, flags, and affiliate suggestions for a pairing.
    Returns dict with keys: flags, tags, affiliate_suggestions
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or api_key == 'your-anthropic-api-key-here':
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Review this food pairing submission for a community platform.
Pairing: {item_1} + {item_2}
Description: {description}

Flag if: spam, inappropriate, not food-related, or plagiarized-sounding.
Also suggest 3 relevant tags from this list: [sweet, salty, sour, bitter, umami, crunchy, creamy, chewy, rich, light, spicy, acidic, dessert, snack, meal, drink].
Also suggest affiliate search queries for the items.

Return only valid JSON in this exact format:
{{
  "flags": [],
  "tags": ["tag1", "tag2", "tag3"],
  "affiliate_suggestions": [
    {{"item": "{item_1}", "retailer": "amazon", "search_query": "{item_1} food product"}},
    {{"item": "{item_2}", "retailer": "walmart", "search_query": "{item_2} food product"}}
  ]
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        content = message.content[0].text
        # Extract JSON from response
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception as e:
        print(f"AI suggestion error: {e}")

    return None
