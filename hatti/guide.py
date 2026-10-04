"""Bounded live selection with an authored, source-linked local fallback."""
import json
import os
from urllib.parse import urlparse
import httpx
from .content import GUIDANCE, WORD_BY_ID, public_word
from .engine import retrieve, validate_selection

async def guidance(topic, transport=None):
    authored = GUIDANCE[topic]
    selected = authored["terms"][:4]
    mode = "source-guide"
    live = os.getenv("HATTI_ENABLE_LIVE_AI") == "1"
    base = os.getenv("HATTI_AI_BASE_URL", "").rstrip("/")
    key = os.getenv("HATTI_AI_API_KEY", "")
    model = os.getenv("HATTI_AI_MODEL", "")
    if live and base and key and model and urlparse(base).scheme == "https":
        evidence = [public_word(WORD_BY_ID[i]) for i in authored["terms"]]
        try:
            async with httpx.AsyncClient(timeout=15, transport=transport, follow_redirects=False) as client:
                response = await client.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "temperature": 0, "max_tokens": 200,
                          "response_format": {"type": "json_object"},
                          "messages": [
                              {"role": "system", "content": "Select 1 to 4 supplied word IDs relevant to the topic. Return ONLY JSON with guidance_id and word_ids. Keep guidance_id identical to the supplied topic. Do not generate or translate any language."},
                              {"role": "user", "content": json.dumps({"topic": topic, "evidence": evidence})}]})
                response.raise_for_status()
                selection = json.loads(response.json()["choices"][0]["message"]["content"])
                selected = validate_selection(selection, topic)
                mode = "live-selection"
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            mode = "source-guide-fallback"
    return {"title": authored["title"], "text": authored["text"],
            "words": [public_word(WORD_BY_ID[i]) for i in selected],
            "retrieval": [w["id"] for w in retrieve(" ".join(selected).replace("-", " "))],
            "mode": mode, "audio_sent": False, "personal_data_sent": False}
