from .models import WorksheetRequest
from .workflow import WorkflowResult


def render_markdown(result: WorkflowResult) -> str:
    request, worksheet = result.request, result.worksheet
    lines = [
        f"# {request.subject}: {request.topic}",
        "",
        f"**Grade:** {request.grade}",
        "",
        f"**Learning objective:** {request.learning_objective}",
        "",
        "## Explanation",
        "",
        worksheet.explanation.strip(),
        "",
        "## Worked examples",
        "",
    ]
    for number, example in enumerate(worksheet.worked_examples, 1):
        lines.extend([f"### Example {number}: {example.title}", "", example.problem, ""])
        lines.extend(f"{step}. {text}" for step, text in enumerate(example.steps, 1))
        lines.extend(["", f"**Answer:** {example.answer}", ""])

    lines.extend(["## Summary", ""])
    lines.extend(f"- {item}" for item in worksheet.summary)
    lines.extend(["", "## Exercises", ""])
    lines.extend(f"{number}. {exercise.question}" for number, exercise in enumerate(worksheet.exercises, 1))
    lines.extend(["", "## Solutions", ""])
    lines.extend(f"{number}. {exercise.solution}" for number, exercise in enumerate(worksheet.exercises, 1))
    return "\n".join(lines).rstrip() + "\n"


def review_report(result: WorkflowResult, model_name: str) -> dict:
    return {
        "status": "approved" if result.review.approved else "needs_review",
        "model": model_name,
        "revisions": result.revisions,
        "request": result.request.model_dump(),
        "review": result.review.model_dump(),
    }
