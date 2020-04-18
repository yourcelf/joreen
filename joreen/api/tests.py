import json
import pytest

from stateparsers import AVAILABLE_STATES, get_searcher
from stateparsers.tests.test_states import facilities


def test_states(client):
    res = client.get("/api/states.json")
    data = json.loads(res.content.decode("utf-8"))
    assert sorted(data["states"].keys()) == sorted(AVAILABLE_STATES)

    for abbr, details in data["states"].items():
        assert details["minimum_search_terms"] == (
            get_searcher(abbr).minimum_search_terms
        )
    assert res["Access-Control-Allow-Origin"] == "*"


def test_options_header(client):
    res = client.options("/api/states.json")
    assert res["Access-Control-Allow-Origin"] == "*"


@pytest.mark.django_db
def test_inadequate_search_terms(facilities, client):
    res = client.get("/api/search.json", {"state": "federal", "first_name": "John"})
    data = json.loads(res.content.decode("utf-8"))
    assert res.status_code == 400
    assert data["error"] == (
        "federal requires one of [['last_name', 'first_name'], ['number']]"
    )


@pytest.mark.django_db
def test_adequate_search_terms(facilities, client):
    res = client.get(
        "/api/search.json",
        {"state": "federal", "first_name": "John", "last_name": "Smith"},
    )
    data = json.loads(res.content.decode("utf-8"))
    assert res.status_code == 200
    assert "error" not in data
    assert data["errors"] == []
    assert len(data["results"]) > 5
