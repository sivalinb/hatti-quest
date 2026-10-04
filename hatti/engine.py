"""Learning and review decisions live in Python; the browser holds progress."""
import math
import random
import re
from collections import Counter
from datetime import date, timedelta
from .content import GUIDANCE, LESSON_BY_ID, WORD_BY_ID, WORDS, public_word

def tokens(text):
    return re.findall(r"[\w]+", text.casefold())

def retrieve(query, limit=4):
    """Small BM25 index over source forms, English glosses and teaching notes."""
    docs = [tokens(f"{w.badaga} {w.english} {w.category} {w.note}") for w in WORDS]
    average = sum(map(len, docs)) / len(docs)
    query_tokens = tokens(query)
    scores = []
    for w, doc in zip(WORDS, docs):
        counts = Counter(doc)
        score = 0.0
        for term in query_tokens:
            frequency = sum(term in candidate for candidate in docs)
            idf = math.log(1 + (len(docs) - frequency + 0.5) / (frequency + 0.5))
            tf = counts[term]
            denominator = tf + 1.5 * (0.25 + 0.75 * len(doc) / average)
            score += idf * tf * 2.5 / denominator if denominator else 0
        if score > 0:
            scores.append((score, w))
    scores.sort(key=lambda item: (-item[0], item[1].id))
    return [public_word(w) for _, w in scores[:limit]]

def lesson_payload(lesson_id):
    lesson = LESSON_BY_ID[lesson_id]
    challenges = [quiz_payload(word_id) for word_id in lesson["word_ids"]]
    return {**lesson, "words": [public_word(WORD_BY_ID[i]) for i in lesson["word_ids"]], "challenges": challenges}

def quiz_payload(word_id):
    w = WORD_BY_ID[word_id]
    distractors = [other for other in WORDS if other.id != w.id and other.english != w.english]
    rng = random.Random(f"hatti-quest-v1:{word_id}")
    choices = [w, *rng.sample(distractors, 2)]
    rng.shuffle(choices)
    return {"word_id": word_id, "prompt": f"Which means “{w.english}”?",
            "choices": [{"id": c.id, "label": c.badaga} for c in choices]}

def grade(word_id, choice_id):
    w = WORD_BY_ID[word_id]
    return {"correct": word_id == choice_id, "word": public_word(w),
            "message": "You found it!" if word_id == choice_id else "A word to come back to. Let's try it together."}

def schedule_review(prior, correct, today):
    wins = int((prior or {}).get("wins", 0))
    misses = int((prior or {}).get("misses", 0))
    wins = min(wins + 1, 50) if correct else 0
    misses = min(misses + (not correct), 1000)
    interval = min(2 ** max(0, wins - 1), 14) if correct else 1
    return {"wins": wins, "misses": misses, "due": (today + timedelta(days=interval)).isoformat(), "last": today.isoformat()}

def due_review(progress, today, limit=5):
    pending = [(date.fromisoformat(item["due"]), id) for id, item in progress.items()
               if id in WORD_BY_ID and date.fromisoformat(item["due"]) <= today]
    pending.sort()
    return [public_word(WORD_BY_ID[id]) for _, id in pending[:limit]]

def validate_selection(selection, topic):
    """A model selects only existing content; it cannot author Badaga."""
    if not isinstance(selection, dict) or set(selection) != {"guidance_id", "word_ids"}:
        raise ValueError("Invalid selection fields")
    if selection["guidance_id"] != topic:
        raise ValueError("Selection changed the requested topic")
    allowed = set(GUIDANCE[topic]["terms"])
    ids = selection["word_ids"]
    if not isinstance(ids, list) or not 1 <= len(ids) <= 4 or any(not isinstance(id, str) for id in ids):
        raise ValueError("Invalid word selection")
    if len(ids) != len(set(ids)):
        raise ValueError("Invalid word selection")
    if any(not isinstance(id, str) or id not in allowed for id in ids):
        raise ValueError("Unsubstantiated word")
    return ids
