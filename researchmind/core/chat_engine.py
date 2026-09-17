from typing import List, Dict, Any, Optional, Generator
from pydantic import BaseModel, Field

from researchmind.config import get_genai_client, Config
from researchmind.paper_loader import PaperMetadata
from researchmind.core.prompts import CHAT_SYSTEM_PROMPT
from researchmind.core.agent import FALLBACK_MODELS, _extract_response_text


class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    content: str


class PaperChatEngine:
    def __init__(
        self,
        paper: PaperMetadata,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.paper = paper
        self.model_name = model_name or Config.get_default_model()
        self.api_key = api_key
        self._client = None
        self.history: List[ChatMessage] = []

    @property
    def client(self):
        if self._client is None:
            self._client = get_genai_client(self.api_key)
        return self._client

    def _build_context_prompt(self) -> str:
        authors_str = ", ".join(self.paper.authors) if self.paper.authors else "Unknown"
        return (
            f"=== RESEARCH PAPER SOURCE DOCUMENT ===\n"
            f"TITLE: {self.paper.title}\n"
            f"AUTHORS: {authors_str}\n"
            f"PAGES: {self.paper.num_pages}\n\n"
            f"--- FULL TEXT (WITH PAGE MARKERS) ---\n"
            f"{self.paper.full_text}\n"
            f"======================================\n"
        )

    def generate_starter_questions(self) -> List[str]:
        """
        Generates 4 intelligent, paper-specific questions for the user to explore.
        """
        prompt = (
            f"{self._build_context_prompt()}\n\n"
            f"Based on this research paper, generate 4 concise, high-value, probing questions that a researcher "
            f"or reviewer would want to ask about this work (e.g., about methodology nuances, benchmark baselines, "
            f"limitations, or implementation). Output each question on a separate line starting with '- '."
        )
        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        try:
            resp = None
            for model in models_to_try:
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    break
                except Exception:
                    continue

            if not resp:
                raise RuntimeError("Failed to generate questions")

            raw_text = _extract_response_text(resp)
            questions = []
            for line in raw_text.split("\n"):
                line = line.strip()
                if line.startswith(("-", "*", "1.", "2.", "3.", "4.")):
                    q = line.lstrip("-*0123456789. ")
                    if len(q) > 10:
                        questions.append(q)
            return questions[:4] or [
                "What is the primary architectural contribution?",
                "How does performance compare to existing state-of-the-art?",
                "What are the main limitations identified by the authors?",
                "How can this method be reproduced in code?",
            ]
        except Exception:
            return [
                "What is the primary architectural contribution?",
                "How does performance compare to existing state-of-the-art?",
                "What are the main limitations identified by the authors?",
                "How can this method be reproduced in code?",
            ]

    def ask(self, user_question: str) -> str:
        """
        Asks a question and returns the answer synchronously.
        """
        self.history.append(ChatMessage(role="user", content=user_question))

        # Format conversation with grounding context
        convo_text = []
        for msg in self.history:
            prefix = "User" if msg.role == "user" else "Assistant"
            convo_text.append(f"{prefix}: {msg.content}")

        full_prompt = (
            f"{CHAT_SYSTEM_PROMPT}\n\n"
            f"{self._build_context_prompt()}\n\n"
            f"Conversation History:\n" + "\n".join(convo_text) + "\n\n"
            f"Assistant (respond citing page numbers [Page X]):"
        )

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        resp = None
        for model in models_to_try:
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                )
                break
            except Exception:
                continue

        answer = _extract_response_text(resp) if resp else "I could not find an answer in the paper."
        self.history.append(ChatMessage(role="model", content=answer))
        return answer

    def ask_stream(self, user_question: str) -> Generator[str, None, None]:
        """
        Asks a question and yields chunks in real-time streaming.
        """
        self.history.append(ChatMessage(role="user", content=user_question))

        convo_text = []
        for msg in self.history:
            prefix = "User" if msg.role == "user" else "Assistant"
            convo_text.append(f"{prefix}: {msg.content}")

        full_prompt = (
            f"{CHAT_SYSTEM_PROMPT}\n\n"
            f"{self._build_context_prompt()}\n\n"
            f"Conversation History:\n" + "\n".join(convo_text) + "\n\n"
            f"Assistant (respond citing page numbers [Page X]):"
        )

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        full_answer = []
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
                        full_answer.append(txt)
                        yield txt
                        yielded = True
                if yielded:
                    self.history.append(ChatMessage(role="model", content="".join(full_answer)))
                    return
            except Exception:
                continue

        fallback_msg = "I could not connect to generate a response at this time. Please try again."
        yield fallback_msg
        self.history.append(ChatMessage(role="model", content=fallback_msg))

