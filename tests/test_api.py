def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_recommend_standards(client):
    r = client.post(
        "/api/recommend-standards",
        json={"query": "Portland cement 53 grade for building works", "top_k": 3},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["recommendations"]) <= 3
    assert data["latency_ms"] < 30000
    first = data["recommendations"][0]
    assert "certification_info" in first
    assert "allied_standards" in first
    assert "version_info" in first
