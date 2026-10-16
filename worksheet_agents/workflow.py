from dataclasses import dataclass

from .gemini import StructuredModel
from .models import LessonPlan, Review, Worksheet, WorksheetRequest
from .prompts import planner_prompt, reviewer_prompt, writer_prompt


@dataclass(frozen=True)
class WorkflowResult:
    request: WorksheetRequest
    plan: LessonPlan
    worksheet: Worksheet
    review: Review
    revisions: int


def run_workflow(
    request: WorksheetRequest, model: StructuredModel, max_revisions: int = 1
) -> WorkflowResult:
    if max_revisions < 0:
        raise ValueError("max_revisions must be zero or greater")

    plan = model.generate(planner_prompt(request), LessonPlan)
    worksheet = model.generate(writer_prompt(request, plan), Worksheet)
    review = model.generate(reviewer_prompt(request, plan, worksheet), Review)
    revisions = 0

    while not review.approved and revisions < max_revisions:
        worksheet = model.generate(writer_prompt(request, plan, worksheet, review), Worksheet)
        revisions += 1
        review = model.generate(reviewer_prompt(request, plan, worksheet), Review)

    return WorkflowResult(request, plan, worksheet, review, revisions)
