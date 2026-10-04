"""Contract and behaviour checks for content, reviews and bounded AI selection."""
import asyncio
import json
from datetime import date, timedelta
import httpx
import pytest
from fastapi.testclient import TestClient
from hatti.app import create_app
from hatti.content import GUIDANCE, LESSONS, WORDS, WORD_BY_ID, SOURCES
from hatti.engine import retrieve, schedule_review, validate_selection
from hatti.guide import guidance

@pytest.fixture
def client():
    with TestClient(create_app()) as client:
        yield client

def test_curriculum_has_valid_sources_and_unique_words():
    assert len(WORDS) == len(WORD_BY_ID) == 50
    source_ids = {s["id"] for s in SOURCES}
    assert all(w.source_id in source_ids and w.review_status == "source-documented" for w in WORDS)
    assert len(LESSONS) == 5
    assert all(len(l["word_ids"]) == 5 and set(l["word_ids"]) <= set(WORD_BY_ID) for l in LESSONS)

def test_full_lesson_contract(client):
    for lesson in LESSONS:
        response = client.get(f'/api/lessons/{lesson["id"]}')
        assert response.status_code == 200
        body = response.json()
        assert len(body["words"]) == len(body["challenges"]) == 5
        for q in body["challenges"]:
            ids = [c["id"] for c in q["choices"]]
            assert len(set(ids)) == 3 and q["word_id"] in ids
    assert client.get('/api/lessons/made-up').status_code == 404

def test_retrieval_english_and_badaga():
    assert retrieve('Haalu')[0]["id"] == 'milk'
    assert retrieve('Mother')[0]["id"] == 'mother'
    assert retrieve('Eradu')[0]["id"] == 'two'
    assert retrieve('xyzxyzxyz') == []

def test_search_and_word_challenge(client):
    assert len(client.get('/api/search').json()["words"]) == 50
    words = client.get('/api/search', params={"q": "mother", "category": "family"}).json()["words"]
    assert words[0]["id"] == 'mother'
    assert all(w["category"] == 'family' for w in words)
    assert client.get('/api/search', params={"q": "x" * 121}).status_code == 422
    assert client.get('/api/words/ten/challenge').json()["word_id"] == 'ten'
    assert client.get('/api/words/invented/challenge').status_code == 404

def test_review_schedule_repeats_and_resets():
    today = date(2026, 10, 3)
    previous = None
    for wins, interval in [(1, 1), (2, 2), (3, 4), (4, 8), (5, 14), (6, 14)]:
        previous = schedule_review(previous, True, today)
        assert previous["wins"] == wins
        assert previous["due"] == (today + timedelta(days=interval)).isoformat()
    reset = schedule_review(previous, False, today)
    assert reset == {"wins": 0, "misses": 1, "due": '2026-10-04', "last": '2026-10-03'}

def test_answer_to_review_round_trip(client):
    result = client.post('/api/answer', json={"word_id": "milk", "choice_id": "milk", "today": "2026-10-03"}).json()
    assert result["correct"] and result["word"]["source"]["url"].startswith('https://badaga.co/')
    progress = {"milk": result["review"]}
    assert client.post('/api/review', json={"today": "2026-10-03", "progress": progress}).json()["words"] == []
    assert client.post('/api/review', json={"today": "2026-10-04", "progress": progress}).json()["words"][0]["id"] == 'milk'
    wrong = client.post('/api/answer', json={"word_id": "milk", "choice_id": "teeth", "today": "2026-10-04", "prior": result["review"]}).json()
    assert not wrong["correct"] and wrong["review"]["wins"] == 0

@pytest.mark.parametrize('body', [
    {"word_id": "invented", "choice_id": "milk", "today": "2026-10-03"},
    {"word_id": "milk", "choice_id": "invented", "today": "2026-10-03"},
    {"word_id": "milk", "choice_id": "milk", "today": "tomorrow"},
    {"word_id": "milk", "choice_id": "milk", "today": "2026-10-03", "prior": {"wins": -1, "misses": 0, "due": "2026-10-04", "last": "2026-10-03"}},
])
def test_answers_reject_unknown_or_invalid_state(client, body):
    assert client.post('/api/answer', json=body).status_code == 422

def test_review_rejects_unknown_words(client):
    assert client.post('/api/review', json={"today": "2026-10-04", "progress": {"fake": {"wins": 1, "misses": 0, "due": "2026-10-04", "last": "2026-10-03"}}}).status_code == 422

def test_browser_boundaries_and_no_audio_upload(client):
    assert client.get('/').status_code == 200
    response = client.get('/api/content')
    assert "script-src 'self'" in response.headers['Content-Security-Policy']
    assert response.headers['Cache-Control'] == 'no-store'
    assert client.post('/api/guide', json={"topic": "start"}, headers={"Origin": "https://other.example"}).status_code == 403
    assert client.post('/api/guide', content='x' * 33_000).status_code == 413
    assert client.post('/api/audio', content=b'private voice').status_code == 404
    assert client.get('/health').json()["status"] == 'ok'

def test_source_guide_needs_no_service_or_key(monkeypatch, client):
    monkeypatch.delenv('HATTI_ENABLE_LIVE_AI', raising=False)
    for topic in GUIDANCE:
        result = client.post('/api/guide', json={"topic": topic}).json()
        assert result["mode"] == 'source-guide'
        assert result["text"] == GUIDANCE[topic]["text"]
        assert result["words"] and not result["audio_sent"] and not result["personal_data_sent"]
    assert client.post('/api/guide', json={"topic": "invent a sentence"}).status_code == 422

@pytest.mark.parametrize('selection', [
    {"guidance_id": "family", "word_ids": ["milk"]},
    {"guidance_id": "family", "word_ids": ["mother", "mother"]},
    {"guidance_id": "start", "word_ids": ["mother"]},
    {"guidance_id": "family", "word_ids": []},
    {"guidance_id": "family", "word_ids": [["mother"]]},
    {"guidance_id": "family", "word_ids": ["mother"], "new_badaga": "invented"},
])
def test_model_cannot_select_unsubstantiated_content(selection):
    with pytest.raises(ValueError): validate_selection(selection, 'family')

def enable_test_model(monkeypatch):
    monkeypatch.setenv('HATTI_ENABLE_LIVE_AI', '1')
    monkeypatch.setenv('HATTI_AI_BASE_URL', 'https://provider.example/v1')
    monkeypatch.setenv('HATTI_AI_MODEL', 'test-model')
    monkeypatch.setenv('HATTI_AI_API_KEY', 'test-only-key')

def test_live_selection_is_bounded_and_sends_only_curriculum(monkeypatch):
    enable_test_model(monkeypatch)
    def handler(request):
        body = json.loads(request.content)
        evidence = json.loads(body["messages"][1]["content"])
        assert set(evidence) == {"topic", "evidence"}
        assert {w["id"] for w in evidence["evidence"]} == set(GUIDANCE['family']["terms"])
        assert "audio" not in body and "user" not in body
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"guidance_id": "family", "word_ids": ["grandmother", "mother"]})}}]})
    result = asyncio.run(guidance('family', transport=httpx.MockTransport(handler)))
    assert result["mode"] == 'live-selection'
    assert [w["id"] for w in result["words"]] == ['grandmother', 'mother']
    assert result["text"] == GUIDANCE['family']["text"]

@pytest.mark.parametrize('bad_content', ['not json', '{"guidance_id":"family","word_ids":["invented"]}', '{"guidance_id":"family","word_ids":[["mother"]]}'])
def test_bad_model_output_falls_back(monkeypatch, bad_content):
    enable_test_model(monkeypatch)
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"choices": [{"message": {"content": bad_content}}]}))
    result = asyncio.run(guidance('family', transport=transport))
    assert result["mode"] == 'source-guide-fallback'
    assert result["words"][0]["id"] == 'mother'

def test_provider_outage_falls_back(monkeypatch):
    enable_test_model(monkeypatch)
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    assert asyncio.run(guidance('family', transport=transport))["mode"] == 'source-guide-fallback'
