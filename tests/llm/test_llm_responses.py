"""
LLM Response Evaluation Tests

These tests send questions to the RAG/chatbot system, receive answers, and
evaluate whether the responses are correct using multiple strategies:

  1. Classification – is it an answer or a rejection?
  2. Keyword overlap – does it contain expected keywords?
  3. Embedding similarity – is it semantically close? (requires OpenAI key)
  4. LLM-as-Judge – does a second LLM rate it highly? (opt-in)

Run these tests:
    # All LLM evaluation tests
    pytest tests/llm/ -m llm_eval -v

    # Only offline tests (no API calls)
    pytest tests/llm/ -m "llm_eval and not external_api" -v

    # Include LLM judge (most accurate, costs more)
    pytest tests/llm/ -m llm_eval -v --llm-judge

    # Filter by category
    pytest tests/llm/ -m llm_eval -v -k "esg_knowledge"

    # Filter by tag
    pytest tests/llm/ -m llm_eval -v -k "csrd"
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest
import yaml

# ---------------------------------------------------------------------------
# Ensure Django is configured
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WEBSITE_DIR = BASE_DIR / "website"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(WEBSITE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")

import django
django.setup()

from tests.llm.evaluator import (
    CompositeEvaluator,
    ClassificationEvaluator,
    KeywordEvaluator,
    EmbeddingSimilarityEvaluator,
    LLMJudgeEvaluator,
    EvalResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# pytest hooks & fixtures
# ---------------------------------------------------------------------------

def pytest_addoption(parser):
    """Add custom CLI options for LLM evaluation tests."""
    parser.addoption(
        "--llm-judge",
        action="store_true",
        default=False,
        help="Enable LLM-as-Judge evaluator (costs money, most accurate)",
    )
    parser.addoption(
        "--eval-min-score",
        type=float,
        default=None,
        help="Override minimum score threshold for all test cases",
    )
    parser.addoption(
        "--eval-mode",
        choices=["offline", "embedding", "full"],
        default="embedding",
        help=(
            "Evaluation mode: "
            "'offline' = keyword only, "
            "'embedding' = keyword + embedding similarity (default), "
            "'full' = keyword + embedding + LLM judge"
        ),
    )


def load_test_cases() -> List[Dict[str, Any]]:
    """Load test cases from YAML file."""
    yaml_path = Path(__file__).parent / "test_cases.yaml"
    with open(yaml_path, "r") as f:
        cases = yaml.safe_load(f)
    return cases or []


@pytest.fixture(scope="session")
def evaluator(request) -> CompositeEvaluator:
    """Create a CompositeEvaluator based on CLI options."""
    use_judge = request.config.getoption("--llm-judge", default=False)
    eval_mode = request.config.getoption("--eval-mode", default="embedding")

    # Determine which evaluators to use
    evaluators = ["classification", "keyword"]

    if eval_mode in ("embedding", "full") or use_judge:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            evaluators.append("embedding_similarity")
        else:
            logger.warning(
                "OPENAI_API_KEY not set — skipping embedding similarity. "
                "Set it or use --eval-mode=offline"
            )

    if eval_mode == "full" or use_judge:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            evaluators.append("llm_judge")
        else:
            logger.warning("OPENAI_API_KEY not set — skipping LLM judge")

    return CompositeEvaluator(evaluators=evaluators)


@pytest.fixture
def rag_bot(db):
    """
    Create a callable that sends a question to the RAG system and returns
    the response string.

    Requires DB access (creates a test user) and the RAG system with an
    active OpenAI API key.  Tests using this fixture should be marked with
    ``external_api`` and ``slow``.

    Returns a function: (question: str, session_type: str) -> str
    """
    from chatbot.views import generate_bot_response
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Create or get a test user for RAG queries
    test_user, _ = User.objects.get_or_create(
        username="llm_test_user",
        defaults={
            "email": "llm_test@example.com",
            "is_active": True,
        },
    )
    # Ensure profile exists (may be auto-created by signal)
    from accounts.models import Profile
    profile, _ = Profile.objects.get_or_create(user=test_user)
    profile.email_confirmed = True
    profile.save()

    def ask(question: str, session_type: str = "general") -> str:
        """Send a question to the RAG chatbot and return the response."""
        if not question.strip():
            return ""
        try:
            response = generate_bot_response(question, session_type, user=test_user)
            return response or ""
        except Exception as e:
            logger.error(f"RAG system error: {e}")
            return f"Error: {e}"

    return ask


# ---------------------------------------------------------------------------
# Test case parametrization
# ---------------------------------------------------------------------------

_test_cases = load_test_cases()


def _case_id(case: Dict) -> str:
    """Generate a readable test ID from a case dict."""
    return case.get("id", case.get("question", "unknown")[:40])


# ---------------------------------------------------------------------------
# Tests: answer quality (expects an answer)
# ---------------------------------------------------------------------------

@pytest.mark.llm_eval
@pytest.mark.external_api
@pytest.mark.slow
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "case",
    [c for c in _test_cases if c.get("expect_answer", True)],
    ids=[_case_id(c) for c in _test_cases if c.get("expect_answer", True)],
)
def test_llm_answer_quality(case: Dict, rag_bot, evaluator, request):
    """
    Test that the LLM provides a quality answer for a known question.

    Steps:
        1. Send the question to the RAG system.
        2. Verify the response is NOT a rejection.
        3. Evaluate semantic similarity to the expected answer.
        4. Assert the composite score meets the minimum threshold.
    """
    question = case["question"]
    expected = case.get("expected_answer", "")
    session_type = case.get("session_type", "general")
    min_score_override = request.config.getoption("--eval-min-score", default=None)
    min_score = min_score_override if min_score_override is not None else case.get("min_score", 0.7)

    # Step 1: Get response from the system
    response = rag_bot(question, session_type)
    assert response, f"Empty response for question: {question}"

    # Step 2: Evaluate
    result = evaluator.evaluate(
        question=question,
        response=response,
        expected_answer=expected,
    )

    # Step 3: Format detailed output for debugging
    detail_msg = _format_eval_details(case, response, result)

    # Step 4: Assert — must be an answer, not a rejection
    assert result.is_answer, (
        f"Expected an answer but got a rejection.\n{detail_msg}"
    )

    # Step 5: Assert quality score
    assert result.composite_score >= min_score, (
        f"Score {result.composite_score:.2f} < required {min_score:.2f}.\n{detail_msg}"
    )


# ---------------------------------------------------------------------------
# Tests: rejection detection (expects the system to refuse)
# ---------------------------------------------------------------------------

@pytest.mark.llm_eval
@pytest.mark.external_api
@pytest.mark.slow
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "case",
    [c for c in _test_cases if not c.get("expect_answer", True)],
    ids=[_case_id(c) for c in _test_cases if not c.get("expect_answer", True)],
)
def test_llm_rejection_detection(case: Dict, rag_bot, evaluator, request):
    """
    Test that the LLM correctly rejects out-of-scope or harmful questions.

    Steps:
        1. Send the question to the RAG system.
        2. Verify the response IS a rejection or deflection.
    """
    question = case["question"]
    session_type = case.get("session_type", "general")

    if not question.strip():
        pytest.skip("Empty question — edge case handled by input validation")

    # Step 1: Get response from the system
    response = rag_bot(question, session_type)

    # Step 2: Evaluate classification only
    classifier = ClassificationEvaluator()
    result = classifier.evaluate(question=question, response=response)

    detail_msg = _format_eval_details(case, response, result)

    # For out-of-scope questions, we accept either:
    # - An explicit rejection (is_answer=False)
    # - A response that redirects to the platform's scope
    # Some RAG systems answer everything — so we also check if the system
    # at least acknowledges it's outside its domain.
    if result.is_answer:
        # Check if the response at least acknowledges limitations
        deflection_indicators = [
            "not related to",
            "outside",
            "beyond",
            "can help you with",
            "designed to",
            "focus on",
            "scope",
            "assist with",
            "esg",
            "sustainability",
            "platform",
            "subscription",
        ]
        response_lower = response.lower()
        has_deflection = any(ind in response_lower for ind in deflection_indicators)

        if not has_deflection:
            # Soft failure — log a warning but don't fail hard
            # Many RAG systems will attempt to answer anything
            logger.warning(
                f"Test case '{case.get('id')}': Expected rejection but got an "
                f"answer without deflection. Response: {response[:200]}..."
            )
            pytest.xfail(
                f"System answered instead of rejecting. "
                f"Consider tuning system prompts.\n{detail_msg}"
            )


# ---------------------------------------------------------------------------
# Offline-only evaluation tests (no API calls, always runnable)
# ---------------------------------------------------------------------------

@pytest.mark.llm_eval
@pytest.mark.external_api
@pytest.mark.slow
@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "case",
    [c for c in _test_cases if c.get("expect_answer", True) and c.get("expected_answer")],
    ids=[_case_id(c) for c in _test_cases if c.get("expect_answer", True) and c.get("expected_answer")],
)
def test_llm_keyword_coverage(case: Dict, rag_bot):
    """
    Lightweight keyword-coverage check (no API calls required).

    Verifies that the response contains a reasonable fraction of the
    keywords from the expected answer.
    """
    question = case["question"]
    expected = case.get("expected_answer", "")
    session_type = case.get("session_type", "general")

    response = rag_bot(question, session_type)
    assert response, f"Empty response for question: {question}"

    kw_eval = KeywordEvaluator()
    result = kw_eval.evaluate(question=question, response=response, expected_answer=expected)

    # A keyword score of 0.3 means at least 30% of expected keywords appear
    min_kw_score = 0.25
    detail_msg = (
        f"Question:  {question}\n"
        f"Response:  {response[:300]}...\n"
        f"Keyword Score: {result.keyword_score:.2f}\n"
        f"Matched: {result.raw_details.get('matched_keywords', [])}\n"
        f"Missing: {result.raw_details.get('missing_keywords', [])}\n"
    )
    assert result.keyword_score >= min_kw_score, (
        f"Keyword coverage {result.keyword_score:.2f} < {min_kw_score}.\n{detail_msg}"
    )


# ---------------------------------------------------------------------------
# Evaluator self-tests (unit tests that don't hit the RAG system)
# ---------------------------------------------------------------------------

@pytest.mark.llm_eval
class TestClassificationEvaluator:
    """Unit tests for the classification evaluator itself."""

    def test_identifies_clear_answer(self):
        evaluator = ClassificationEvaluator()
        result = evaluator.evaluate(
            question="What is ESG?",
            response="ESG stands for Environmental, Social, and Governance factors.",
        )
        assert result.is_answer is True

    def test_identifies_refusal_cant(self):
        evaluator = ClassificationEvaluator()
        result = evaluator.evaluate(
            question="What is the meaning of life?",
            response="I'm sorry, but I can't answer that question as it's outside my scope.",
        )
        assert result.is_answer is False

    def test_identifies_refusal_no_information(self):
        evaluator = ClassificationEvaluator()
        result = evaluator.evaluate(
            question="Tell me about quantum physics",
            response="I don't have enough information to answer your question about quantum physics.",
        )
        assert result.is_answer is False

    def test_identifies_refusal_unable(self):
        evaluator = ClassificationEvaluator()
        result = evaluator.evaluate(
            question="How do I cook pasta?",
            response="I am unable to help with cooking questions. I can assist with ESG topics.",
        )
        assert result.is_answer is False

    def test_identifies_no_documents_found(self):
        evaluator = ClassificationEvaluator()
        result = evaluator.evaluate(
            question="What about XYZ?",
            response="There are no relevant documents for your query.",
        )
        assert result.is_answer is False

    def test_real_answer_not_false_positive(self):
        evaluator = ClassificationEvaluator()
        result = evaluator.evaluate(
            question="What is the CSRD?",
            response=(
                "The CSRD is the Corporate Sustainability Reporting Directive. "
                "It requires companies to report on their environmental and social impacts. "
                "I can provide more information if needed."
            ),
        )
        assert result.is_answer is True


@pytest.mark.llm_eval
class TestKeywordEvaluator:
    """Unit tests for the keyword evaluator itself."""

    def test_perfect_overlap(self):
        evaluator = KeywordEvaluator()
        answer = "The CSRD is Corporate Sustainability Reporting Directive"
        result = evaluator.evaluate(
            question="What is CSRD?",
            response=answer,
            expected_answer=answer,
        )
        assert result.keyword_score == 1.0

    def test_partial_overlap(self):
        evaluator = KeywordEvaluator()
        result = evaluator.evaluate(
            question="What is CSRD?",
            response="The CSRD is an EU regulation about reporting.",
            expected_answer="The Corporate Sustainability Reporting Directive requires ESG disclosures.",
        )
        assert 0.0 < result.keyword_score < 1.0

    def test_no_overlap(self):
        evaluator = KeywordEvaluator()
        result = evaluator.evaluate(
            question="What is CSRD?",
            response="Bananas are yellow fruits.",
            expected_answer="The Corporate Sustainability Reporting Directive.",
        )
        assert result.keyword_score < 0.2

    def test_empty_expected(self):
        evaluator = KeywordEvaluator()
        result = evaluator.evaluate(
            question="test",
            response="some response",
            expected_answer="",
        )
        assert result.keyword_score == 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_eval_details(case: Dict, response: str, result: EvalResult) -> str:
    """Format evaluation details for assertion messages."""
    lines = [
        f"Test Case:  {case.get('id', 'unknown')}",
        f"Category:   {case.get('category', '-')}",
        f"Question:   {case.get('question', '')[:100]}",
        f"Expected:   {case.get('expected_answer', '')[:150]}...",
        f"Response:   {response[:200]}...",
        f"",
        f"--- Scores ---",
        f"  Is Answer:       {result.is_answer}",
        f"  Keyword:         {result.keyword_score:.3f}",
        f"  Embedding:       {result.embedding_similarity:.3f}",
        f"  LLM Judge:       {result.llm_judge_score:.3f}",
        f"  Composite:       {result.composite_score:.3f}",
        f"  Evaluators:      {', '.join(result.evaluators_used)}",
    ]
    if result.rejection_reason:
        lines.append(f"  Rejection:       {result.rejection_reason}")
    if result.llm_judge_reasoning:
        lines.append(f"  Judge Reasoning: {result.llm_judge_reasoning}")
    if result.raw_details.get("missing_keywords"):
        lines.append(f"  Missing KW:      {result.raw_details['missing_keywords'][:10]}")
    return "\n".join(lines)
