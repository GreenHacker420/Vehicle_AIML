from __future__ import annotations

import json
import os
import re
from typing import Any


class LLMInsightService:
    """
    Optional GenAI/LangChain insight enhancer.

    If not configured, the backend stays fully functional and uses rule-based
    insights only.
    """

    def __init__(self) -> None:
        """Initialise the service.

        Reads ``ENABLE_LLM_INSIGHTS``, ``GOOGLE_API_KEY`` / ``GENAI_API_KEY``,
        and ``GENAI_MODEL`` from the environment.  The LangChain client is only
        imported and instantiated when the feature flag is enabled *and* an API
        key is present, so the package is not required for normal operation.
        """
        self.enabled = os.getenv("ENABLE_LLM_INSIGHTS", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.model_name = os.getenv("GENAI_MODEL", "gemini-1.5-flash")
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY")
        self._llm: Any | None = None

        if not self.enabled or not self.api_key:
            return

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            self._llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.2,
            )
        except Exception:
            self._llm = None

    @property
    def available(self) -> bool:
        """Return True if the LLM client was initialised successfully."""
        return self._llm is not None

    def generate(
        self,
        *,
        risk_level: str,
        risk_probability: float,
        rule_summary: str,
        row: dict[str, Any],
        drivers: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Generate an LLM-enhanced insight payload for a single prediction.

        Sends the rule-based summary and structured drivers to Gemini and
        returns a dict with ``summary`` (str) and ``recommendations`` (list).
        Returns ``None`` if the LLM is unavailable or the call fails.
        """
        if not self.available:
            return None

        context = {
            "risk_level": risk_level,
            "risk_probability": round(risk_probability, 4),
            "rule_summary": rule_summary,
            "normalized_row": row,
            "drivers": drivers,
        }
        system_prompt = (
            "You are a senior fleet maintenance analyst. "
            "Write concise, practical insights for operations teams.\n"
            "Return strict JSON with keys: summary, recommendations.\n"
            "summary: 1-2 sentences, plain language, include what the number means.\n"
            "recommendations: array of up to 3 objects with keys action and rationale.\n"
            "Do not use markdown."
        )
        human_prompt = f"Prediction context:\\n{json.dumps(context, ensure_ascii=True)}"

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            response = self._llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=human_prompt),
                ]
            )
        except Exception:
            return None

        raw = self._coerce_content(response.content if hasattr(response, "content") else response)
        parsed = self._parse_json_block(raw)
        if parsed is None:
            return None

        summary = parsed.get("summary")
        recommendations = parsed.get("recommendations")
        if not isinstance(summary, str):
            return None
        if not isinstance(recommendations, list):
            recommendations = []

        normalized_recommendations: list[dict[str, str]] = []
        for item in recommendations[:3]:
            if not isinstance(item, dict):
                continue
            action = item.get("action")
            rationale = item.get("rationale")
            if isinstance(action, str) and isinstance(rationale, str):
                normalized_recommendations.append(
                    {
                        "action": action.strip(),
                        "rationale": rationale.strip(),
                    }
                )

        return {
            "summary": summary.strip(),
            "recommendations": normalized_recommendations,
        }

    @staticmethod
    def _coerce_content(content: Any) -> str:
        """Normalise an LLM response content value to a plain string."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    maybe_text = item.get("text")
                    if isinstance(maybe_text, str):
                        parts.append(maybe_text)
                else:
                    parts.append(str(item))
            return " ".join(parts)
        return str(content)

    @staticmethod
    def _parse_json_block(text: str) -> dict[str, Any] | None:
        """Extract and parse the first JSON object from *text*.

        Handles responses wrapped in markdown code fences (```json ... ```).
        Returns ``None`` if no valid JSON object is found.
        """
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        candidates = [cleaned]
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            candidates.append(match.group(0))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue
        return None

