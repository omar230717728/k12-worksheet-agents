import unittest

from worksheet_agents.models import (
    Exercise,
    LessonPlan,
    Review,
    ReviewIssue,
    Worksheet,
    WorksheetRequest,
    WorkedExample,
)
from worksheet_agents.render import render_markdown, review_report
from worksheet_agents.workflow import run_workflow


REQUEST = WorksheetRequest(
    subject="Mathematics",
    topic="Addition",
    grade="2",
    learning_objective="Add two numbers up to 20.",
)
PLAN = LessonPlan(
    concepts=["addition"],
    teaching_sequence=["model addition"],
    exercise_targets=["add two numbers"],
    grade_guidance="Use small whole numbers.",
)


def worksheet(answer: str) -> Worksheet:
    return Worksheet(
        explanation="Addition combines amounts.",
        worked_examples=[
            WorkedExample(title="Two groups", problem="2 + 3", steps=["Count 2, then 3 more"], answer="5")
        ],
        summary=["Combine the amounts."],
        exercises=[
            Exercise(question="1 + 1 = ?", solution=answer),
            Exercise(question="2 + 2 = ?", solution="4"),
            Exercise(question="3 + 3 = ?", solution="6"),
        ],
    )


REJECTED = Review(
    approved=False,
    issues=[ReviewIssue(section="Solutions", problem="Exercise 1 answer is wrong", requested_fix="Use 2")],
)
APPROVED = Review(approved=True, issues=[])


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def generate(self, prompt, schema):
        self.calls.append(schema)
        result = next(self.responses)
        assert isinstance(result, schema)
        return result


class WorkflowTests(unittest.TestCase):
    def test_gemini_output_schemas_avoid_unsupported_keywords(self):
        def keywords(value):
            if isinstance(value, dict):
                for key, nested in value.items():
                    yield key
                    yield from keywords(nested)
            elif isinstance(value, list):
                for nested in value:
                    yield from keywords(nested)

        for model in (LessonPlan, Worksheet, Review):
            schema_keywords = set(keywords(model.model_json_schema()))
            self.assertNotIn("additionalProperties", schema_keywords)
            self.assertNotIn("minLength", schema_keywords)

    def test_reviewer_feedback_causes_one_revision(self):
        model = FakeModel([PLAN, worksheet("3"), REJECTED, worksheet("2"), APPROVED])
        result = run_workflow(REQUEST, model)
        self.assertTrue(result.review.approved)
        self.assertEqual(result.revisions, 1)
        self.assertEqual(model.calls, [LessonPlan, Worksheet, Review, Worksheet, Review])
        rendered = render_markdown(result)
        self.assertIn("## Exercises", rendered)
        self.assertIn("## Solutions", rendered)
        self.assertIn("1. 2", rendered)

    def test_second_rejection_stops_and_reports_issues(self):
        model = FakeModel([PLAN, worksheet("3"), REJECTED, worksheet("3"), REJECTED])
        result = run_workflow(REQUEST, model)
        self.assertFalse(result.review.approved)
        self.assertEqual(result.revisions, 1)
        self.assertEqual(review_report(result, "fake")["status"], "needs_review")

    def test_blank_request_and_inconsistent_review_are_rejected(self):
        with self.assertRaises(ValueError):
            WorksheetRequest(subject=" ", topic="Addition", grade="2", learning_objective="Add")
        with self.assertRaises(ValueError):
            Review(approved=True, issues=REJECTED.issues)


if __name__ == "__main__":
    unittest.main()
