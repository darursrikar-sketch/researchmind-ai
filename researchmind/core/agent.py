import time
from typing import Dict, Any, List, Optional, Callable, Generator
from pydantic import BaseModel, Field

from researchmind.config import get_genai_client, Config
from researchmind.paper_loader import PaperMetadata
from researchmind.core.prompts import (
    SYSTEM_ANALYST_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    METHODOLOGY_PROMPT,
    PEER_REVIEW_PROMPT,
    FINDINGS_AND_BENCHMARKS_PROMPT,
    LIMITATIONS_AND_FUTURE_WORK_PROMPT,
    REPLICATION_AND_CODE_PROMPT,
)


MODULE_PROMPTS = {
    "summary": ("Executive Summary & TL;DR", EXECUTIVE_SUMMARY_PROMPT),
    "methodology": ("Methodology & Architecture", METHODOLOGY_PROMPT),
    "review": ("Critical Peer Review & Validity", PEER_REVIEW_PROMPT),
    "benchmarks": ("Findings & Benchmark Analysis", FINDINGS_AND_BENCHMARKS_PROMPT),
    "limitations": ("Limitations & Future Directions", LIMITATIONS_AND_FUTURE_WORK_PROMPT),
    "implementation": ("Replication & Implementation Guide", REPLICATION_AND_CODE_PROMPT),
}


FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
]


def _extract_response_text(response) -> str:
    """Safely extracts text from Gemini response, handling multi-part or thinking structures."""
    if getattr(response, "text", None):
        return response.text
    if getattr(response, "candidates", None) and response.candidates:
        cand = response.candidates[0]
        if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
            texts = [p.text for p in cand.content.parts if getattr(p, "text", None)]
            if texts:
                return "\n".join(texts)
    return "No content generated."


class AnalysisSection(BaseModel):
    key: str
    title: str
    content: str
    generation_time_s: float = 0.0


class PaperAnalysisResult(BaseModel):
    paper_id: str
    paper_title: str
    model_used: str
    timestamp: float = Field(default_factory=time.time)
    sections: Dict[str, AnalysisSection] = {}
    metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "paper_title": self.paper_title,
            "model_used": self.model_used,
            "timestamp": self.timestamp,
            "sections": {k: v.model_dump() for k, v in self.sections.items()},
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaperAnalysisResult":
        sections_dict = {}
        for k, v in data.get("sections", {}).items():
            sections_dict[k] = AnalysisSection(**v)
        return cls(
            paper_id=data.get("paper_id", ""),
            paper_title=data.get("paper_title", ""),
            model_used=data.get("model_used", ""),
            timestamp=data.get("timestamp", time.time()),
            sections=sections_dict,
            metadata=data.get("metadata", {}),
        )


class PaperAnalysisAgent:
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name or Config.get_default_model()
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_genai_client(self.api_key)
        return self._client

    def _prepare_paper_context(self, paper: PaperMetadata) -> str:
        """Formats paper metadata and content for prompt injection."""
        meta_lines = [
            f"PAPER TITLE: {paper.title}",
        ]
        if paper.authors:
            meta_lines.append(f"AUTHORS: {', '.join(paper.authors)}")
        if paper.published:
            meta_lines.append(f"DATE: {paper.published}")
        if paper.arxiv_id:
            meta_lines.append(f"ARXIV ID: {paper.arxiv_id}")
        if paper.abstract:
            meta_lines.append(f"\nABSTRACT:\n{paper.abstract}\n")

        header = "\n".join(meta_lines)
        body = f"\nFULL PAPER TEXT:\n{paper.full_text}"
        return f"{header}\n{body}"

    def _generate_with_fallback(self, prompt: str):
        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        last_err = None
        for model in models_to_try:
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                return resp, model
            except Exception as e:
                last_err = e
                continue
        if last_err:
            raise last_err

    def analyze_section(
        self, paper: PaperMetadata, section_key: str
    ) -> AnalysisSection:
        """
        Runs a single analysis module synchronously with fallback resilience.
        """
        if section_key not in MODULE_PROMPTS:
            raise ValueError(f"Unknown section key: {section_key}. Valid: {list(MODULE_PROMPTS.keys())}")

        title, prompt_template = MODULE_PROMPTS[section_key]
        paper_context = self._prepare_paper_context(paper)

        full_prompt = (
            f"{SYSTEM_ANALYST_PROMPT}\n\n"
            f"--- RESEARCH PAPER CONTENT ---\n"
            f"{paper_context}\n\n"
            f"--- TASK INSTRUCTION ---\n"
            f"{prompt_template}\n\n"
            f"Remember: Base all analysis strictly on the provided paper. "
            f"Cite specific page numbers [Page X] wherever applicable."
        )

        start = time.time()
        response, used_model = self._generate_with_fallback(full_prompt)
        duration = round(time.time() - start, 2)
        content = _extract_response_text(response)

        return AnalysisSection(
            key=section_key,
            title=title,
            content=content,
            generation_time_s=duration,
        )

    def analyze_section_stream(
        self, paper: PaperMetadata, section_key: str
    ) -> Generator[str, None, None]:
        """
        Streams generated tokens for a section in real time with fallback resilience.
        """
        if section_key not in MODULE_PROMPTS:
            raise ValueError(f"Unknown section key: {section_key}")

        title, prompt_template = MODULE_PROMPTS[section_key]
        paper_context = self._prepare_paper_context(paper)

        full_prompt = (
            f"{SYSTEM_ANALYST_PROMPT}\n\n"
            f"--- RESEARCH PAPER CONTENT ---\n"
            f"{paper_context}\n\n"
            f"--- TASK INSTRUCTION ---\n"
            f"{prompt_template}\n\n"
            f"Remember: Base all analysis strictly on the provided paper. "
            f"Cite specific page numbers [Page X] wherever applicable."
        )

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        for model in models_to_try:
            try:
                stream = self.client.models.generate_content_stream(
                    model=model,
                    contents=full_prompt,
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

    def analyze_all(
        self,
        paper: PaperMetadata,
        selected_sections: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> PaperAnalysisResult:
        """
        Orchestrates full analysis of paper across selected or all modules.
        """
        target_keys = selected_sections or list(MODULE_PROMPTS.keys())
        total = len(target_keys)

        result = PaperAnalysisResult(
            paper_id=paper.id,
            paper_title=paper.title,
            model_used=self.model_name,
            metadata=paper.to_dict(),
        )

        for idx, key in enumerate(target_keys, 1):
            if progress_callback:
                title = MODULE_PROMPTS[key][0]
                progress_callback(f"Analyzing {title}...", idx, total)

            sec_result = self.analyze_section(paper, key)
            result.sections[key] = sec_result

        return result

