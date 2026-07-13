"""Tests for the RAG pipeline.

Coverage
--------
1. Chunking    — chunk_text produces correct chunks, metadata, and overlap.
2. Embeddings  — generate_embedding / generate_embeddings call Gemini correctly.
3. ChromaDB    — add, delete, query, and empty-collection guard.
4. Retrieval   — retrieve_relevant_job_descriptions groups chunks by JD.

All Gemini calls are mocked so no real API key is needed.
All ChromaDB operations use a temporary local directory so the real vector_db
is never touched.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.rag.embeddings import (
    CHUNK_TARGET_CHARS,
    OVERLAP_CHARS,
    chunk_text,
    generate_embedding,
    generate_embeddings,
)
from app.rag.retriever import EmbeddingError, retrieve_relevant_job_descriptions
from app.rag.store import (
    ChromaDBError,
    EmptyCollectionError,
    add_documents,
    delete_documents,
    get_collection,
    query,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_JD_TEXT = """\
Software Engineer

Job Title: Software Engineer

About the Role
We are looking for a Software Engineer to build scalable backend APIs.
Experience with Python and FastAPI is required.

Requirements
- 2+ years of professional software development experience
- Strong knowledge of Python and FastAPI
- Experience with PostgreSQL or other relational databases
- Familiarity with Docker and CI/CD pipelines

Responsibilities
- Design, build, and maintain efficient, reusable, and reliable Python code
- Collaborate with cross-functional teams to define, design, and ship new features
- Write unit tests and integration tests for all code changes
- Participate in code reviews and contribute to team-wide engineering discussions

Nice to Have
- Experience with React or another modern JavaScript framework
- Knowledge of cloud platforms such as AWS or GCP
- Experience with message queues (Redis, RabbitMQ)
"""

SAMPLE_JD_METADATA = {
    "job_description_id": "1",
    "filename": "software_engineer.txt",
    "role_title": "Software Engineer",
}

# A fake embedding vector returned by gemini-embedding-001.
FAKE_EMBEDDING: list[float] = [0.01] * 768


@pytest.fixture()
def chroma_tmp(tmp_path, monkeypatch):
    """Redirect ChromaDB to a temp directory for the duration of each test."""
    monkeypatch.setattr("app.rag.store.settings.chroma_persist_dir", str(tmp_path))
    yield tmp_path


# ---------------------------------------------------------------------------
# 1. Chunking tests
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_produces_at_least_one_chunk(self):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        assert len(chunks) >= 1

    def test_chunk_contains_text_and_metadata(self):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        for chunk in chunks:
            assert "text" in chunk
            assert "metadata" in chunk
            assert chunk["text"].strip()

    def test_metadata_fields_are_preserved(self):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        for i, chunk in enumerate(chunks):
            meta = chunk["metadata"]
            assert meta["job_description_id"] == "1"
            assert meta["filename"] == "software_engineer.txt"
            assert meta["role_title"] == "Software Engineer"
            assert meta["chunk_index"] == i
            assert meta["source_type"] == "job_description"

    def test_chunk_indices_are_sequential(self):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        for i, chunk in enumerate(chunks):
            assert chunk["metadata"]["chunk_index"] == i

    def test_chunk_size_stays_near_target(self):
        # All chunks except possibly the last should be close to target size.
        long_text = (SAMPLE_JD_TEXT + "\n") * 10
        chunks = chunk_text(
            long_text,
            **SAMPLE_JD_METADATA,
            chunk_target_chars=CHUNK_TARGET_CHARS,
            overlap_chars=OVERLAP_CHARS,
        )
        assert len(chunks) > 1
        # No chunk should be more than 2× the target (overlap included).
        for chunk in chunks[:-1]:
            assert len(chunk["text"]) <= CHUNK_TARGET_CHARS * 2

    def test_overlap_carries_text_across_chunks(self):
        long_text = (SAMPLE_JD_TEXT + "\n") * 10
        chunks = chunk_text(long_text, **SAMPLE_JD_METADATA)
        if len(chunks) < 2:
            pytest.skip("Text too short to produce multiple chunks.")
        # The tail of chunk N should appear at the start of chunk N+1.
        tail = chunks[0]["text"][-100:]
        assert any(tail[:50] in chunks[1]["text"] for _ in [1])

    def test_empty_text_returns_no_chunks(self):
        assert chunk_text("", **SAMPLE_JD_METADATA) == []
        assert chunk_text("   \n\t  ", **SAMPLE_JD_METADATA) == []

    def test_integer_jd_id_is_cast_to_string(self):
        meta = {**SAMPLE_JD_METADATA, "job_description_id": 99}
        chunks = chunk_text(SAMPLE_JD_TEXT, **meta)
        assert chunks[0]["metadata"]["job_description_id"] == "99"

    def test_source_type_is_always_job_description(self):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        assert all(c["metadata"]["source_type"] == "job_description" for c in chunks)


# ---------------------------------------------------------------------------
# 2. Embedding tests (Gemini mocked)
# ---------------------------------------------------------------------------


class TestGenerateEmbedding:
    def test_returns_embedding_vector(self):
        mock_response = _mock_embedding_response([FAKE_EMBEDDING])

        with patch("app.rag.embeddings.genai.Client") as MockClient:
            instance = MockClient.return_value
            instance.models.embed_content.return_value = mock_response

            result = generate_embedding("Software Engineer resume text")

        assert result == FAKE_EMBEDDING
        instance.models.embed_content.assert_called_once_with(
            model="gemini-embedding-001",
            contents="Software Engineer resume text",
        )

    def test_generate_embeddings_batches_all_texts(self):
        texts = ["chunk one", "chunk two", "chunk three"]
        mock_response = _mock_embedding_response([FAKE_EMBEDDING] * len(texts))

        with patch("app.rag.embeddings.genai.Client") as MockClient:
            instance = MockClient.return_value
            instance.models.embed_content.return_value = mock_response

            result = generate_embeddings(texts)

        assert len(result) == 3
        assert result[0] == FAKE_EMBEDDING
        instance.models.embed_content.assert_called_once_with(
            model="gemini-embedding-001",
            contents=texts,
        )

    def test_generate_embeddings_empty_list_returns_empty(self):
        result = generate_embeddings([])
        assert result == []

    def test_generate_embedding_propagates_gemini_error(self):
        with patch("app.rag.embeddings.genai.Client") as MockClient:
            instance = MockClient.return_value
            instance.models.embed_content.side_effect = RuntimeError("API error")
            with pytest.raises(RuntimeError, match="API error"):
                generate_embedding("some text")


def _mock_embedding_response(vectors: list[list[float]]) -> MagicMock:
    response = MagicMock()
    response.embeddings = []
    for vector in vectors:
        item = MagicMock()
        item.values = vector
        response.embeddings.append(item)
    return response


# ---------------------------------------------------------------------------
# 3. ChromaDB store tests
# ---------------------------------------------------------------------------


class TestChromaDBStore:
    def test_get_collection_returns_collection(self, chroma_tmp):
        collection = get_collection()
        assert collection is not None
        assert collection.name == "job_descriptions"

    def test_get_collection_is_idempotent(self, chroma_tmp):
        c1 = get_collection()
        c2 = get_collection()
        assert c1.name == c2.name

    def test_add_documents_stores_chunks(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        embeddings = [FAKE_EMBEDDING] * len(chunks)
        add_documents(chunks, embeddings)

        collection = get_collection()
        assert collection.count() == len(chunks)

    def test_add_documents_upserts_on_duplicate(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        embeddings = [FAKE_EMBEDDING] * len(chunks)
        add_documents(chunks, embeddings)
        count_first = get_collection().count()

        # Second add with same ids should upsert, not raise.
        add_documents(chunks, embeddings)
        assert get_collection().count() == count_first

    def test_add_documents_empty_list_is_noop(self, chroma_tmp):
        add_documents([], [])
        assert get_collection().count() == 0

    def test_add_documents_raises_on_mismatch(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        with pytest.raises(ChromaDBError, match="(?i)mismatch"):
            add_documents(chunks, [])

    def test_delete_documents_removes_correct_chunks(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        embeddings = [FAKE_EMBEDDING] * len(chunks)
        add_documents(chunks, embeddings)

        # Add a second JD.
        meta2 = {**SAMPLE_JD_METADATA, "job_description_id": "2", "role_title": "Data Scientist"}
        chunks2 = chunk_text(
            "Data Scientist\nJob Title: Data Scientist\nAnalyze datasets and build ML models.\n",
            **meta2,
        )
        add_documents(chunks2, [FAKE_EMBEDDING] * len(chunks2))

        count_before = get_collection().count()
        delete_documents("1")
        count_after = get_collection().count()

        assert count_after == count_before - len(chunks)

    def test_delete_nonexistent_id_is_noop(self, chroma_tmp):
        delete_documents("nonexistent-999")
        assert get_collection().count() == 0

    def test_query_returns_results(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        embeddings = [FAKE_EMBEDDING] * len(chunks)
        add_documents(chunks, embeddings)

        result = query(FAKE_EMBEDDING, n_results=3)
        assert "documents" in result
        assert len(result["documents"][0]) > 0

    def test_query_empty_collection_raises_empty_collection_error(self, chroma_tmp):
        with pytest.raises(EmptyCollectionError):
            query(FAKE_EMBEDDING, n_results=3)

    def test_query_n_results_capped_at_collection_size(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        embeddings = [FAKE_EMBEDDING] * len(chunks)
        add_documents(chunks, embeddings)

        # Request more than available — should not raise.
        result = query(FAKE_EMBEDDING, n_results=9999)
        assert len(result["documents"][0]) == len(chunks)

    def test_metadata_is_preserved_in_query_results(self, chroma_tmp):
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        embeddings = [FAKE_EMBEDDING] * len(chunks)
        add_documents(chunks, embeddings)

        result = query(FAKE_EMBEDDING, n_results=len(chunks))
        metadatas = result["metadatas"][0]
        for meta in metadatas:
            assert meta["source_type"] == "job_description"
            assert meta["job_description_id"] == "1"


# ---------------------------------------------------------------------------
# 4. Retrieval tests
# ---------------------------------------------------------------------------


class TestRetrieveRelevantJobDescriptions:
    def _mock_embedding(self, monkeypatch):
        monkeypatch.setattr(
            "app.rag.retriever.generate_embedding",
            lambda text: FAKE_EMBEDDING,
        )

    def test_returns_grouped_results(self, chroma_tmp, monkeypatch):
        self._mock_embedding(monkeypatch)

        # Index two JDs.
        chunks1 = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        meta2 = {**SAMPLE_JD_METADATA, "job_description_id": "2", "role_title": "Data Scientist"}
        chunks2 = chunk_text(
            "Data Scientist\nJob Title: Data Scientist\nAnalyze datasets and build ML models.\n",
            **meta2,
        )
        all_chunks = chunks1 + chunks2
        add_documents(all_chunks, [FAKE_EMBEDDING] * len(all_chunks))

        results = retrieve_relevant_job_descriptions("Sample resume text", top_k=8)

        assert isinstance(results, list)
        assert len(results) >= 1
        for item in results:
            assert "job_description_id" in item
            assert "role_title" in item
            assert "chunks" in item
            assert isinstance(item["chunks"], list)
            assert len(item["chunks"]) >= 1

    def test_chunks_are_grouped_by_jd_id(self, chroma_tmp, monkeypatch):
        self._mock_embedding(monkeypatch)

        chunks1 = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        add_documents(chunks1, [FAKE_EMBEDDING] * len(chunks1))

        results = retrieve_relevant_job_descriptions("resume", top_k=8)
        assert len(results) == 1
        assert results[0]["job_description_id"] == "1"
        assert len(results[0]["chunks"]) == len(chunks1)

    def test_empty_resume_returns_empty_list(self, chroma_tmp, monkeypatch):
        self._mock_embedding(monkeypatch)
        assert retrieve_relevant_job_descriptions("") == []
        assert retrieve_relevant_job_descriptions("   ") == []

    def test_empty_collection_returns_empty_list(self, chroma_tmp, monkeypatch):
        self._mock_embedding(monkeypatch)
        result = retrieve_relevant_job_descriptions("Some resume text")
        assert result == []

    def test_embedding_failure_raises_embedding_error(self, chroma_tmp, monkeypatch):
        monkeypatch.setattr(
            "app.rag.retriever.generate_embedding",
            MagicMock(side_effect=RuntimeError("Gemini down")),
        )
        with pytest.raises(EmbeddingError, match="Gemini down"):
            retrieve_relevant_job_descriptions("resume text")

    def test_role_title_preserved_in_results(self, chroma_tmp, monkeypatch):
        self._mock_embedding(monkeypatch)
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        add_documents(chunks, [FAKE_EMBEDDING] * len(chunks))

        results = retrieve_relevant_job_descriptions("resume")
        assert results[0]["role_title"] == "Software Engineer"

    def test_retrieval_uses_mocked_embedding_only(self, chroma_tmp, monkeypatch):
        """Retrieval uses embedding search and does not call generation APIs."""
        embedding_mock = MagicMock(return_value=FAKE_EMBEDDING)
        monkeypatch.setattr("app.rag.retriever.generate_embedding", embedding_mock)
        chunks = chunk_text(SAMPLE_JD_TEXT, **SAMPLE_JD_METADATA)
        add_documents(chunks, [FAKE_EMBEDDING] * len(chunks))

        retrieve_relevant_job_descriptions("resume text", top_k=4)

        embedding_mock.assert_called_once_with("resume text")
