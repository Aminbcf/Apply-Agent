from unittest.mock import MagicMock, patch

# pyrefly: ignore [missing-import]
import pytest
from fastapi.testclient import TestClient

from main import app
from routers.cv import DOMAINS

client = TestClient(app, base_url="https://testserver")

@pytest.fixture
def mock_embedding_manager():
    with patch("routers.cv.embedding_manager") as mock_manager:
        # Set up default mock return values
        mock_manager.get_all_domain_embeddings.return_value = {
            domain: [0.1, 0.2, 0.3] for domain in DOMAINS
        }
        mock_manager.find_best_matching_domain.return_value = ("Software Engineering", 0.95)
        import numpy as np
        mock_manager.embed_text.return_value = np.array([0.1, 0.2, 0.3])
        yield mock_manager

@pytest.fixture
def mock_cv_processor():
    with patch("routers.cv.cv_processor") as mock_processor:
        mock_processor.process_cv.return_value = {
            "name": "John Doe",
            "summary": "Experienced engineer",
            "embeddings": [0.1, 0.2, 0.3],
            "best_domain": "Software Engineering"
        }
        mock_processor.get_domain_similarity_scores.return_value = {
            "Software Engineering": 0.95,
            "Data Science": 0.85
        }
        mock_processor.parse_and_process_raw_cv.return_value = {
            "name": "Jane Doe",
            "summary": "Data Scientist",
            "best_domain": "Data Science"
        }
        yield mock_processor


@pytest.mark.unit
def test_get_domains():
    response = client.get("/domains")
    assert response.status_code == 200
    assert "domains" in response.json()
    assert len(response.json()["domains"]) > 0


@pytest.mark.unit
def test_get_domain_embeddings(mock_embedding_manager):
    response = client.get("/domain-embeddings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    # verify mocked data structure
    first_domain_key = list(data.keys())[0]
    assert isinstance(data[first_domain_key], list)


@pytest.mark.unit
def test_process_cv(mock_cv_processor):
    payload = {
        "name": "John Doe",
        "summary": "Experienced engineer",
        "skills": ["Python", "FastAPI"]
    }
    response = client.post("/process-cv", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    mock_cv_processor.process_cv.assert_called_once()


@pytest.mark.unit
def test_classify_cv_domain(mock_embedding_manager):
    payload = {
        "summary": "Experienced engineer",
        "skills": ["Python", "FastAPI"],
        "experience": "5 years building APIs"
    }
    response = client.post("/classify-cv-domain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "domain" in data
    assert "confidence" in data
    assert data["domain"] == "Software Engineering"
    assert data["confidence"] == 0.95
    mock_embedding_manager.find_best_matching_domain.assert_called_once()


@pytest.mark.unit
def test_cv_domain_scores(mock_cv_processor):
    payload = {"summary": "Experienced engineer"}
    response = client.post("/cv-domain-scores", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "domain_scores" in data
    assert isinstance(data["domain_scores"], list)
    # Check if the scores are sorted
    scores = [score for _, score in data["domain_scores"]]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.unit
def test_embed_text(mock_embedding_manager):
    response = client.post("/embed-text", params={"text": "Software Engineering is fun"})
    assert response.status_code == 200
    data = response.json()
    assert "embedding" in data
    assert "dimension" in data
    assert data["dimension"] == 3
    assert data["embedding"] == [0.1, 0.2, 0.3]


@pytest.mark.unit
def test_parse_raw_cv(mock_cv_processor):
    response = client.post("/parse-raw-cv", params={"raw_cv_text": "Jane Doe. Data Scientist. 3 years experience."})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["best_domain"] == "Data Science"
    mock_cv_processor.parse_and_process_raw_cv.assert_called_once_with("Jane Doe. Data Scientist. 3 years experience.")
