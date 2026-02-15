"""
LLM Response Evaluator

Provides multiple evaluation strategies for assessing LLM responses:

1. ClassificationEvaluator  - Determines if a response is an answer or a rejection.
2. KeywordEvaluator         - Checks keyword overlap with expected answer (no API calls).
3. EmbeddingSimilarity      - Cosine similarity via OpenAI embeddings (cheap, accurate).
4. LLMJudgeEvaluator        - Uses an LLM to grade response quality (most accurate, costs more).
5. CompositeEvaluator       - Combines multiple evaluators into a single score.

Usage:
    from tests.llm.evaluator import CompositeEvaluator, EvalResult

    evaluator = CompositeEvaluator()
    result = evaluator.evaluate(
        question="What is the CSRD?",
        response="The CSRD is the Corporate Sustainability Reporting Directive...",
        expected_answer="The Corporate Sustainability Reporting Directive (CSRD) is an EU regulation...",
    )
    assert result.is_answer          # Not a rejection
    assert result.similarity >= 0.7  # Semantically close to expected
"""

from __future__ import annotations

import os
import re
import math
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EvalResult:
    """Result of an LLM response evaluation."""

    # Classification
    is_answer: bool = True
    """True if the response is an actual answer (not a refusal / rejection)."""

    rejection_reason: Optional[str] = None
    """If is_answer is False, a short description of why it was classified as a rejection."""

    # Similarity / quality scores  (0.0 – 1.0)
    keyword_score: float = 0.0
    """Fraction of expected-answer keywords found in the response."""

    embedding_similarity: float = 0.0
    """Cosine similarity between response and expected answer embeddings."""

    llm_judge_score: float = 0.0
    """Score assigned by an LLM acting as a judge (0.0 – 1.0)."""

    llm_judge_reasoning: str = ""
    """Free-text reasoning from the LLM judge."""

    # Composite
    composite_score: float = 0.0
    """Weighted combination of individual scores."""

    # Metadata
    evaluators_used: list = field(default_factory=list)
    """Names of evaluators that contributed to this result."""

    raw_details: Dict[str, Any] = field(default_factory=dict)
    """Any additional details from individual evaluators."""

    def passed(self, *, min_score: float = 0.7, must_be_answer: bool = True) -> bool:
        """Convenience: does this result meet the given thresholds?"""
        if must_be_answer and not self.is_answer:
            return False
        return self.composite_score >= min_score


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseEvaluator(ABC):
    """Base class for all evaluators."""

    name: str = "base"

    @abstractmethod
    def evaluate(
        self,
        question: str,
        response: str,
        expected_answer: str,
        **kwargs,
    ) -> EvalResult:
        ...


# ---------------------------------------------------------------------------
# 1. Classification – answer vs rejection
# ---------------------------------------------------------------------------

class ClassificationEvaluator(BaseEvaluator):
    """
    Determines whether a response is a genuine answer or a rejection/refusal.

    Uses pattern matching against common refusal phrases.  Works offline –
    no API calls required.
    """

    name = "classification"

    # Patterns that indicate a refusal / inability to answer.
    REJECTION_PATTERNS: list[str] = [
        r"i (?:can(?:'?t| ?not)|cannot|am unable to|don'?t have (?:the |enough )?(?:information|data|knowledge|context))",
        r"(?:sorry|apolog(?:ies|ize)),?\s*(?:but\s+)?i (?:can(?:'?t| ?not)|cannot)",
        r"i(?:'?m| am) (?:not able|unable) to (?:answer|respond|help|assist|provide)",
        r"(?:unfortunately|regrettably),?\s*i (?:can(?:'?t| ?not)|cannot|don'?t)",
        r"i don'?t (?:know|have|understand)\b.*(?:answer|information|data)",
        r"(?:no|not enough) (?:information|data|context) (?:available|provided|found)",
        r"(?:this|that|the) (?:question|query|topic) is (?:outside|beyond|not (?:within|in))",
        r"i (?:am |'m )?not (?:sure|certain|qualified)",
        r"there (?:is|are) no (?:relevant |matching )?(?:documents?|information|data|results?)",
        r"could not find (?:any |relevant )?(?:information|documents?|data|answer)",
    ]

    def __init__(self, extra_patterns: Optional[list[str]] = None):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.REJECTION_PATTERNS]
        if extra_patterns:
            self._patterns.extend(re.compile(p, re.IGNORECASE) for p in extra_patterns)

    def evaluate(self, question: str, response: str, expected_answer: str = "", **kwargs) -> EvalResult:
        result = EvalResult(evaluators_used=[self.name])
        for pattern in self._patterns:
            match = pattern.search(response)
            if match:
                result.is_answer = False
                result.rejection_reason = f"Matched rejection pattern: '{match.group()}'"
                result.composite_score = 0.0
                return result
        result.is_answer = True
        result.composite_score = 1.0  # Passed classification
        return result


# ---------------------------------------------------------------------------
# 2. Keyword overlap
# ---------------------------------------------------------------------------

class KeywordEvaluator(BaseEvaluator):
    """
    Computes keyword overlap between response and expected answer.

    Cheap, fast, no API calls.  Useful as a baseline signal.
    """

    name = "keyword"

    # Words too common to be informative
    STOP_WORDS = frozenset(
        "a an the is are was were be been being have has had do does did will "
        "would shall should may might can could of in to for on with at by "
        "from as into through during before after above below between under "
        "and but or nor not so yet both either neither each every all any few "
        "more most other some such no only own same than too very it its this "
        "that these those i me my we our you your he him his she her they them "
        "their what which who whom how when where why if then else also just "
        "about up out there here over again further once".split()
    )

    def __init__(self, min_keyword_length: int = 3):
        self.min_keyword_length = min_keyword_length

    def _extract_keywords(self, text: str) -> set[str]:
        words = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
        return {
            w for w in words
            if w not in self.STOP_WORDS and len(w) >= self.min_keyword_length
        }

    def evaluate(self, question: str, response: str, expected_answer: str = "", **kwargs) -> EvalResult:
        result = EvalResult(evaluators_used=[self.name])

        if not expected_answer:
            result.keyword_score = 0.0
            result.composite_score = 0.0
            return result

        expected_kw = self._extract_keywords(expected_answer)
        response_kw = self._extract_keywords(response)

        if not expected_kw:
            result.keyword_score = 0.0
            result.composite_score = 0.0
            return result

        overlap = expected_kw & response_kw
        result.keyword_score = len(overlap) / len(expected_kw)
        result.composite_score = result.keyword_score
        result.raw_details["matched_keywords"] = sorted(overlap)
        result.raw_details["expected_keywords"] = sorted(expected_kw)
        result.raw_details["missing_keywords"] = sorted(expected_kw - response_kw)
        return result


# ---------------------------------------------------------------------------
# 3. Embedding similarity  (requires OpenAI API key)
# ---------------------------------------------------------------------------

class EmbeddingSimilarityEvaluator(BaseEvaluator):
    """
    Computes cosine similarity between the response and the expected answer
    using OpenAI embeddings.

    Cost: ~$0.0001 per comparison (text-embedding-ada-002).
    """

    name = "embedding_similarity"

    def __init__(self, model: str = "text-embedding-ada-002", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _get_embedding(self, text: str) -> list[float]:
        client = self._get_client()
        response = client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def evaluate(self, question: str, response: str, expected_answer: str = "", **kwargs) -> EvalResult:
        result = EvalResult(evaluators_used=[self.name])

        if not expected_answer:
            result.embedding_similarity = 0.0
            result.composite_score = 0.0
            return result

        try:
            resp_emb = self._get_embedding(response)
            exp_emb = self._get_embedding(expected_answer)
            similarity = self._cosine_similarity(resp_emb, exp_emb)
            result.embedding_similarity = round(similarity, 4)
            result.composite_score = result.embedding_similarity
        except Exception as e:
            logger.warning(f"Embedding similarity evaluation failed: {e}")
            result.embedding_similarity = 0.0
            result.composite_score = 0.0
            result.raw_details["embedding_error"] = str(e)

        return result


# ---------------------------------------------------------------------------
# 4. LLM-as-Judge  (requires OpenAI API key)
# ---------------------------------------------------------------------------

class LLMJudgeEvaluator(BaseEvaluator):
    """
    Uses an LLM to grade a response by comparing it to the expected answer.

    The LLM returns a score (0.0–1.0) and a short explanation.
    Most accurate but slowest and most expensive evaluator.
    """

    name = "llm_judge"

    SYSTEM_PROMPT = """You are an expert evaluator assessing the quality of AI-generated answers.

Given a QUESTION, an AI RESPONSE, and an EXPECTED ANSWER, evaluate how well the
AI response answers the question compared to the expected answer.

Scoring guidelines:
- 1.0: The response fully covers the expected answer's key points, possibly with useful additions.
- 0.8-0.9: The response covers most key points with minor omissions.
- 0.6-0.7: The response partially covers the expected answer. Some important points are missing.
- 0.4-0.5: The response is somewhat relevant but misses most key points.
- 0.2-0.3: The response is barely related to the expected answer.
- 0.0-0.1: The response is completely wrong, irrelevant, or a refusal to answer.

You MUST respond with EXACTLY this format (two lines only):
SCORE: <number between 0.0 and 1.0>
REASONING: <one sentence explaining the score>"""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def evaluate(self, question: str, response: str, expected_answer: str = "", **kwargs) -> EvalResult:
        result = EvalResult(evaluators_used=[self.name])

        if not expected_answer:
            result.llm_judge_score = 0.0
            result.composite_score = 0.0
            return result

        user_prompt = (
            f"QUESTION:\n{question}\n\n"
            f"AI RESPONSE:\n{response}\n\n"
            f"EXPECTED ANSWER:\n{expected_answer}"
        )

        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=200,
            )
            reply = completion.choices[0].message.content.strip()

            # Parse score and reasoning
            score = 0.0
            reasoning = ""
            for line in reply.splitlines():
                line = line.strip()
                if line.upper().startswith("SCORE:"):
                    try:
                        score = float(line.split(":", 1)[1].strip())
                        score = max(0.0, min(1.0, score))
                    except (ValueError, IndexError):
                        score = 0.0
                elif line.upper().startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()

            result.llm_judge_score = round(score, 2)
            result.llm_judge_reasoning = reasoning
            result.composite_score = result.llm_judge_score
            result.raw_details["llm_judge_raw_reply"] = reply

        except Exception as e:
            logger.warning(f"LLM judge evaluation failed: {e}")
            result.llm_judge_score = 0.0
            result.composite_score = 0.0
            result.raw_details["llm_judge_error"] = str(e)

        return result


# ---------------------------------------------------------------------------
# 5. Composite evaluator – combines all of the above
# ---------------------------------------------------------------------------

class CompositeEvaluator(BaseEvaluator):
    """
    Runs multiple evaluators and produces a weighted composite score.

    Default weights:
        classification:         gate (must pass before scoring)
        keyword:                0.2
        embedding_similarity:   0.5
        llm_judge:              0.3

    Configure which evaluators to include via the *evaluators* parameter.
    If the OpenAI API key is not available, the embedding and LLM judge
    evaluators are automatically skipped.
    """

    name = "composite"

    # Evaluator name → default weight for the composite score.
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "keyword": 0.20,
        "embedding_similarity": 0.50,
        "llm_judge": 0.30,
    }

    def __init__(
        self,
        evaluators: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
        api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-ada-002",
        judge_model: str = "gpt-4o-mini",
    ):
        """
        Args:
            evaluators: List of evaluator names to use.
                        Defaults to ["classification", "keyword", "embedding_similarity"].
                        Add "llm_judge" for maximum accuracy.
            weights:    Override default weights for composite scoring.
            api_key:    OpenAI API key  (defaults to OPENAI_API_KEY env var).
            embedding_model: Model name for embedding similarity.
            judge_model:     Model name for LLM judge.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.weights = {**self.DEFAULT_WEIGHTS, **(weights or {})}

        # Default evaluator set — LLM judge excluded by default (opt-in)
        if evaluators is None:
            evaluators = ["classification", "keyword"]
            if self.api_key:
                evaluators.append("embedding_similarity")

        # Build evaluator instances
        self._evaluators: Dict[str, BaseEvaluator] = {}
        for name in evaluators:
            if name == "classification":
                self._evaluators[name] = ClassificationEvaluator()
            elif name == "keyword":
                self._evaluators[name] = KeywordEvaluator()
            elif name == "embedding_similarity":
                if self.api_key:
                    self._evaluators[name] = EmbeddingSimilarityEvaluator(
                        model=embedding_model, api_key=self.api_key
                    )
                else:
                    logger.warning("Skipping embedding_similarity — no OpenAI API key")
            elif name == "llm_judge":
                if self.api_key:
                    self._evaluators[name] = LLMJudgeEvaluator(
                        model=judge_model, api_key=self.api_key
                    )
                else:
                    logger.warning("Skipping llm_judge — no OpenAI API key")
            else:
                raise ValueError(f"Unknown evaluator: {name}")

    def evaluate(self, question: str, response: str, expected_answer: str = "", **kwargs) -> EvalResult:
        # --- Step 1: Classification gate ---
        classifier = self._evaluators.get("classification")
        if classifier:
            cls_result = classifier.evaluate(question, response, expected_answer)
            if not cls_result.is_answer:
                # Response is a rejection — skip quality scoring
                cls_result.evaluators_used = list(self._evaluators.keys())
                return cls_result

        # --- Step 2: Run scoring evaluators ---
        merged = EvalResult(
            is_answer=True,
            evaluators_used=list(self._evaluators.keys()),
        )

        active_weights: Dict[str, float] = {}
        for name, evaluator in self._evaluators.items():
            if name == "classification":
                continue  # Already handled above

            sub_result = evaluator.evaluate(question, response, expected_answer, **kwargs)

            # Copy individual scores
            if name == "keyword":
                merged.keyword_score = sub_result.keyword_score
            elif name == "embedding_similarity":
                merged.embedding_similarity = sub_result.embedding_similarity
            elif name == "llm_judge":
                merged.llm_judge_score = sub_result.llm_judge_score
                merged.llm_judge_reasoning = sub_result.llm_judge_reasoning

            # Collect raw details
            merged.raw_details.update(sub_result.raw_details)

            # Track which evaluators actually contributed a score
            if sub_result.composite_score > 0 or name in ("keyword",):
                active_weights[name] = self.weights.get(name, 0.0)

        # --- Step 3: Compute weighted composite ---
        total_weight = sum(active_weights.values())
        if total_weight > 0:
            weighted_sum = 0.0
            for name, weight in active_weights.items():
                if name == "keyword":
                    weighted_sum += merged.keyword_score * weight
                elif name == "embedding_similarity":
                    weighted_sum += merged.embedding_similarity * weight
                elif name == "llm_judge":
                    weighted_sum += merged.llm_judge_score * weight
            merged.composite_score = round(weighted_sum / total_weight, 4)
        else:
            merged.composite_score = 0.0

        return merged
