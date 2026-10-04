import asyncio
import json
from dataclasses import replace
import httpx
import pytest
from fastapi.testclient import TestClient
from hatti.app import create_app
from hatti.config import Settings
from hatti.content import WORD_BY_ID, public_word
from hatti.evaluation import guard_checks, retrieval_scores
from hatti.providers import ProviderError, Providers
from hatti.rag import FINGERPRINT, RagService, StoryRequest, fuse, validate_draft

def config(tmp_path, live=False):
    return Settings(live=live, nebius_key="test-nebius", pinecone_key="test-pinecone",
                    pinecone_host="https://example.pinecone.io", data_dir=tmp_path)

def draft(ids=("mother", "father", "grandmother")):
    return {"title": "A little moon mission", "scenes": [{"word_id": wid,
        "text": "The little explorers pack a word from home. They set off on a friendly moon mission."} for wid in ids],
        "family_activity": "Look at a family photograph and name two people together."}

def transport(output=None, broken=False):
    def handle(request):
        payload = json.loads(request.content)
        if request.url.path.endswith("embeddings"):
            return httpx.Response(200, json={"data": [{"index":0,"embedding":[0.1]*(255 if broken else 256)}], "usage":{"prompt_tokens":12}})
        if request.url.path.endswith("query"):
            assert payload["namespace"] == "hatti-quest-v1"
            return httpx.Response(200, json={"matches":[{"id":"hq:"+wid,"score":.8,
                "metadata":{"word_id":wid,"fingerprint":FINGERPRINT,"pack":"bfq-v1"}}
                for wid in ("mother","father","grandmother")],"usage":{"read_units":1}})
        return httpx.Response(200, json={"choices":[{"message":{"content":json.dumps(output or draft())}}],
            "usage":{"prompt_tokens":220,"completion_tokens":130}})
    return httpx.MockTransport(handle)

def test_live_story_is_grounded_in_local_source_forms(tmp_path):
    service = RagService(config(tmp_path, True), transport())
    result = asyncio.run(service.story(StoryRequest()))
    assert result["mode"] == "live"
    assert result["evidence"]["retrieval_mode"] == "hybrid"
    assert result["evidence"]["input_tokens"] == 232
    assert result["evidence"]["output_tokens"] == 130
    assert result["evidence"]["cost_usd"] is None
    assert [s["word"]["badaga"] for s in result["scenes"]] == [WORD_BY_ID[i].badaga for i in ("mother","father","grandmother")]
    assert result["family_audio_sent"] is False and result["child_profile_sent"] is False

def test_cached_live_story_reports_no_new_usage(tmp_path):
    service = RagService(config(tmp_path, True), transport())
    first = asyncio.run(service.story(StoryRequest()))
    second = asyncio.run(service.story(StoryRequest()))
    assert second["mode"] == "cached-live"
    assert second["evidence"]["input_tokens"] == second["evidence"]["output_tokens"] == 0
    assert second["evidence"]["origin_run_id"] == first["evidence"]["id"]
    assert second["evidence"]["stages"] == []

def test_invented_reference_falls_back_and_preserves_billed_tokens(tmp_path):
    service = RagService(config(tmp_path, True), transport(draft(("invented", "father", "grandmother"))))
    result = asyncio.run(service.story(StoryRequest()))
    assert result["mode"] == "fallback" and result["evidence"]["schema_rejected"]
    assert result["evidence"]["output_tokens"] == 130
    assert all(s["word"]["id"] in WORD_BY_ID for s in result["scenes"])
    assert service.ledger.cached("missing") is None

def test_no_keys_needed_for_authored_adventure(tmp_path):
    result = asyncio.run(RagService(Settings(data_dir=tmp_path)).story(StoryRequest(focus="garden",theme="animals")))
    assert result["mode"] == "authored"
    assert result["evidence"]["model"] is None
    assert result["evidence"]["input_tokens"] == 0

def test_stale_or_poisoned_vector_metadata_is_not_trusted(tmp_path):
    def handle(request):
        if request.url.path.endswith("embeddings"):
            return httpx.Response(200,json={"data":[{"index":0,"embedding":[.1]*256}]})
        return httpx.Response(200,json={"matches":[{"id":"hq:father","score":1,"metadata":{
            "word_id":"father","fingerprint":"wrong","pack":"bfq-v1","badaga":"invented"}}]})
    result = asyncio.run(RagService(config(tmp_path,True),httpx.MockTransport(handle)).retrieve("father"))
    assert result["mode"] == "bm25"
    assert result["semantic_ids"] == []
    assert result["matches"][0]["word"]["badaga"] == "Appa"

def test_vector_dimension_mismatch_is_a_degraded_retrieval(tmp_path):
    service = RagService(config(tmp_path,True),transport(broken=True))
    result = asyncio.run(service.retrieve("father"))
    assert result["mode"] == "bm25" and result["degraded_reason"] == "embedding-shape"

def test_provider_circuit_breaker_stops_repeated_failures(tmp_path):
    calls=[]
    def bad(request):
        calls.append(request)
        return httpx.Response(503,json={"error":"service unavailable"})
    async def run():
        provider=Providers(config(tmp_path,True),httpx.MockTransport(bad))
        for _ in range(3):
            with pytest.raises(ProviderError):
                await provider.embed(["father"])
        with pytest.raises(ProviderError,match="circuit-open"):
            await provider.embed(["father"])
    asyncio.run(run())
    assert len(calls)==3

def test_remote_ops_requires_token_and_secrets_are_never_returned(tmp_path):
    cfg=replace(config(tmp_path),ops_token="private-ops-token")
    with TestClient(create_app(cfg)) as client:
        assert client.get('/api/ai/status').status_code==403
        response=client.get('/api/ai/status',headers={'Authorization':'Bearer private-ops-token'})
        assert response.status_code==200
        for key in ('test-nebius','test-pinecone','private-ops-token'):
            assert key not in response.text
        assert client.get('/metrics').status_code==200

def test_live_endpoint_rejects_profile_audio_and_unknown_words(tmp_path):
    with TestClient(create_app(config(tmp_path))) as client:
        assert client.post('/api/ai/story',json={'focus':'family','theme':'space','child_name':'Private'}).status_code==422
        assert client.post('/api/ai/story',json={'focus':'family','theme':'space','audio':'bytes'}).status_code==422
        assert client.post('/api/ai/story',json={'focus':'family','review_word_ids':['milk']}).status_code==422

def test_global_story_budget(tmp_path):
    with TestClient(create_app(config(tmp_path))) as client:
        for _ in range(6):
            assert client.post('/api/ai/story',json={}).status_code==200
        assert client.post('/api/ai/story',json={}).status_code==429

def test_review_priority_is_inspectable(tmp_path):
    result=asyncio.run(RagService(config(tmp_path)).story(StoryRequest(review_word_ids=['grandmother'])))
    assert result['scenes'][0]['word']['id']=='grandmother'
    assert result['evidence']['candidates'][0]['reason']=='requested-review'

def test_fusion_and_evaluation_use_rank_metrics():
    words=[public_word(WORD_BY_ID[i]) for i in ('father','mother')]
    result=fuse(words,[{'id':'mother','score':.9},{'id':'grandmother','score':.8}])
    assert result[0]['id']=='mother' and result[0]['lexical_rank']==2 and result[0]['semantic_rank']==1
    assert retrieval_scores(['cat','dog','father'],['father'])=={'recall_at_5':1,'mrr':1/3}
    assert all(case['passed'] for case in guard_checks())
