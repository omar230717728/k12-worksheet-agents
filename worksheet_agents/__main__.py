import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .gemini import GeminiModel
from .models import WorksheetRequest
from .render import render_markdown, review_report
from .workflow import run_workflow

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def resolve_input_path(value: Path) -> Path:
    if value.is_file():
        return value
    if len(value.parts) == 1:
        filename = value.name if value.suffix == ".json" else f"{value.name}.json"
        candidate = EXAMPLES_DIR / "inputs" / filename
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Input JSON not found: {value}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a K-12 worksheet with three Gemini agents.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Input name in examples/inputs, or a JSON file path")
    source.add_argument("--subject", help="School subject; requires --topic, --grade, and --objective")
    parser.add_argument("--topic")
    parser.add_argument("--grade")
    parser.add_argument("--objective")
    parser.add_argument("--output", type=Path, help="Optional Markdown path; defaults to examples/worksheets/<input name>.md")
    parser.add_argument("--model", default="gemini-3.8-flash", help="Gemini model ID")
    parser.add_argument("--max-revisions", type=int, default=1)
    args = parser.parse_args(argv)
    if args.input and any((args.topic, args.grade, args.objective)):
        parser.error("--topic, --grade, and --objective are used only with --subject")
    if args.subject and not all((args.topic, args.grade, args.objective)):
        parser.error("--subject requires --topic, --grade, and --objective")
    if args.max_revisions < 0:
        parser.error("--max-revisions must be zero or greater")
    if args.input:
        args.input = resolve_input_path(args.input)
        if args.output is None:
            args.output = EXAMPLES_DIR / "worksheets" / f"{args.input.stem}.md"
    elif args.output is None:
        parser.error("--output is required when using --subject")
    return args


def load_request(args: argparse.Namespace) -> WorksheetRequest:
    if args.input:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        data = {
            "subject": args.subject,
            "topic": args.topic,
            "grade": args.grade,
            "learning_objective": args.objective,
        }
    return WorksheetRequest.model_validate(data)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        request = load_request(args)
        model = GeminiModel(args.model)
        result = run_workflow(request, model, args.max_revisions)

        report_path = EXAMPLES_DIR / "reviews" / f"{args.output.stem}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(review_report(result, args.model), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if not result.review.approved:
            draft_path = EXAMPLES_DIR / "drafts" / f"{args.output.stem}.md"
            draft_path.parent.mkdir(parents=True, exist_ok=True)
            draft_path.write_text(
                "> **Draft: reviewer found unresolved issues. Do not distribute as a student worksheet.**\n\n"
                + render_markdown(result),
                encoding="utf-8",
            )
            print(f"Review failed. See {report_path} and {draft_path}.", file=sys.stderr)
            return 2

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_markdown(result), encoding="utf-8")
        print(f"Saved {args.output} and {report_path}")
        return 0
    except (OSError, ValueError, ValidationError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
