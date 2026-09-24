from app.schemas.query import QueryResponse


def test_query_response_model_fields():
    payload = QueryResponse(
        answer="Not found in the document.",
        sources=[],
        latency_ms=10.0,
        retrieval_time_ms=3.0,
        generation_time_ms=7.0,
        retrieved_chunks_count=0,
    )
    assert payload.answer.startswith("Not found")
    assert payload.retrieved_chunks_count == 0
