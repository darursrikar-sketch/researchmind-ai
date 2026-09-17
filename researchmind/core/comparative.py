import time
from typing import List, Dict, Any, Optional, Generator
from pydantic import BaseModel, Field

from researchmind.config import get_genai_client, Config
from researchmind.paper_loader import PaperMetadata
from researchmind.core.prompts import COMPARATIVE_SYSTEM_PROMPT
from researchmind.core.agent import FALLBACK_MODELS, _extract_response_text


class ComparisonResult(BaseModel):
    paper_ids: List[str]
    paper_titles: List[str]
    model_used: str
    timestamp: float = Field(default_factory=time.time)
    markdown_report: str


class PaperComparisonAgent:
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name or Config.get_default_model()
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_genai_client(self.api_key)
        return self._client

    def _build_multi_paper_context(self, papers: List[PaperMetadata]) -> str:
        parts = []
        for idx, paper in enumerate(papers, 1):
            authors_str = ", ".join(paper.authors) if paper.authors else "Unknown"
            # Include abstract + first 5 pages and conclusion/results
            text_sample = paper.full_text[:35000]  # rich excerpt to fit easily into reasoning
            parts.append(
                f"### PAPER {idx}: {paper.title}\n"
                f"Authors: {authors_str} | Date: {paper.published or 'N/A'} | Pages: {paper.num_pages}\n"
                f"Abstract: {paper.abstract}\n\n"
                f"Text Excerpt:\n{text_sample}\n"
                f"{'=' * 40}\n"
            )
        return "\n".join(parts)

    def compare(self, papers: List[PaperMetadata]) -> ComparisonResult:
        """
        Runs comparative analysis across 2+ papers synchronously.
        """
        if len(papers) < 2:
            raise ValueError("Comparative analysis requires at least 2 papers.")

        context = self._build_multi_paper_context(papers)
        prompt = (
            f"{COMPARATIVE_SYSTEM_PROMPT}\n\n"
            f"Here are the papers to compare:\n\n"
            f"{context}\n\n"
            f"Provide a comprehensive, objective comparative analysis and structured Markdown comparison matrix."
        )

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        resp = None
        used_model = self.model_name
        for model in models_to_try:
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                used_model = model
                break
            except Exception:
                continue

        return ComparisonResult(
            paper_ids=[p.id for p in papers],
            paper_titles=[p.title for p in papers],
            model_used=used_model,
            markdown_report=_extract_response_text(resp) if resp else "No comparison generated.",
        )

    def compare_stream(self, papers: List[PaperMetadata]) -> Generator[str, None, None]:
        """
        Streams the comparative analysis in real-time.
        """
        if len(papers) < 2:
            raise ValueError("Comparative analysis requires at least 2 papers.")

        context = self._build_multi_paper_context(papers)
        prompt = (
            f"{COMPARATIVE_SYSTEM_PROMPT}\n\n"
            f"Here are the papers to compare:\n\n"
            f"{context}\n\n"
            f"Provide a comprehensive, objective comparative analysis and structured Markdown comparison matrix."
        )

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        for model in models_to_try:
            try:
                stream = self.client.models.generate_content_stream(
                    model=model,
                    contents=prompt,
                )
                yielded = False
                for chunk in stream:
                    txt = _extract_response_text(chunk)
                    if txt and txt != "No content generated.":
                        yield txt
                        yielded = True
                if yielded:
                    return
            except Exception:
                continue

        yield "Failed to generate comparison across selected models. Please check your model selection or API key."

