import json
from pathlib import Path
from typing import List

from .embedding_service import EmbeddingAdapter, SentenceTransformerAdapter
from .history_cache import HistoryCache
from .llm_interface import QwenAdapter, build_prompt

class RAGService:
    """Retrieval‑Augmented Generation service.

    - Retrieves relevant documents (placeholder implementation).
    - Caches recent conversation history.
    - Calls the LLM adapter with built prompt.
    """

    def __init__(self, embedding_adapter: EmbeddingAdapter = None, cache: HistoryCache = None):
        self.embedding_adapter = embedding_adapter or SentenceTransformerAdapter()
        self.cache = cache or HistoryCache()
        self.llm = QwenAdapter()
        # In a real implementation, documents would be loaded from SQLite and indexed.
        self.documents_path = Path(__file__).parent / ".." / ".." / "data" / "documents"
        self.documents_path.mkdir(parents=True, exist_ok=True)

    def generate(self, session_id: str, scenario: str, user_query: str) -> str:
        """Generate a response for a given session and scenario.

        - Adds user message to cache.
        - Retrieves relevant docs.
        - Builds prompt and calls LLM.
        - Stores LLM response in cache.
        """
        # Cache the user message
        self.cache.add_message(session_id, "user", user_query)

        # Build prompt (build_prompt fetches docs internally if needed)
        prompt = build_prompt(scenario, user_query)
        response = self.llm.generate(prompt)

        # Cache the assistant response
        self.cache.add_message(session_id, "assistant", response)
        return response

    async def evaluate_job(
        self,
        job_data: dict,
        session_id: str,
        db,
    ) -> dict:
        """Delegate job evaluation to :class:`~AI.llm.job_match_service.JobMatchService`.

        This thin wrapper keeps *RAGService* as the single entry-point for all
        RAG scenarios while the heavy lifting lives in *JobMatchService*.

        Parameters
        ----------
        job_data:
            Dict with keys ``title``, ``company``, ``description``.
        session_id:
            Active session identifier passed to the service for cache lookups.
        db:
            SQLAlchemy :class:`AsyncSession` injected by the FastAPI router.

        Returns
        -------
        dict
            Serialised :class:`~schemas.job_schemas.JobEvaluationOut`.
        """
        # Import here to avoid circular imports at module level
        from .job_match_service import JobMatchService  # noqa: PLC0415

        service = JobMatchService(
            db=db,
            embedding_adapter=self.embedding_adapter,
            cache=self.cache,
        )
        result = await service.evaluate_job(
            title=job_data["title"],
            company=job_data["company"],
            description=job_data["description"],
            session_id=session_id,
        )
        return result.model_dump()
