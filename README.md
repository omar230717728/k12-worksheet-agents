# K–12 worksheet generator

A small Python multi-agent system that turns a subject, topic, grade, and learning objective into a Markdown worksheet. It uses three specialized Gemini roles: Planner, Writer, and Reviewer.

## Architecture and workflow

1. The CLI validates four named input fields.
2. The **Planner** identifies concepts, teaching order, exercise targets, and grade guidance. Its output is structured as a `LessonPlan`.
3. The **Writer** uses the request and plan to draft explanations, worked examples, a summary, exercises, and paired solutions. Its output is a structured `Worksheet`.
4. The **Reviewer** independently checks objective coverage, grade suitability, facts, examples, and solutions. It returns an approval decision with specific issues.
5. On rejection, the Writer gets the review issues and revises once by default. The Reviewer checks the revision. The program saves an approved worksheet or a clearly marked draft with its review report.

The roles use separate prompts and structured inputs and outputs. The workflow is coordinated by ordinary Python functions. This makes the handoff between agents visible without adding a graph framework for a fixed sequence.

## Project structure

| Path | Responsibility |
| --- | --- |
| `worksheet_agents/__main__.py` | CLI arguments, input loading, output paths, and exit codes |
| `worksheet_agents/models.py` | Pydantic shapes and basic validation for requests and agent responses |
| `worksheet_agents/prompts.py` | Separate instructions for Planner, Writer, and Reviewer |
| `worksheet_agents/gemini.py` | One interface for Gemini structured JSON calls and API errors |
| `worksheet_agents/workflow.py` | Agent order and the bounded review and revision loop |
| `worksheet_agents/render.py` | Markdown worksheet and JSON review report formatting |
| `examples/inputs/` | Named JSON requests containing the four required fields |
| `examples/worksheets/` | Approved Markdown worksheets, named after their inputs |
| `examples/reviews/` | Review decisions and model metadata, named after their inputs |
| `examples/drafts/` | Rejected drafts if the final review still finds issues |
| `tests/` | CLI, schema, error handling, and workflow checks |

The main functions follow the path of one request:

1. `parse_args()` and `load_request()` accept either a named JSON input or four CLI fields, then validate the request. This keeps input and path handling out of the agents.
2. `run_workflow()` calls Planner, Writer, and Reviewer in order. If the Reviewer rejects a draft, it sends the specific issues back to the Writer and reviews the revision. The revision limit prevents an open ended loop.
3. `GeminiModel.generate()` sends each prompt with its expected Pydantic response schema and validates the returned JSON. The workflow depends on the small `StructuredModel` interface, so tests can use a fake model without API calls.
4. `render_markdown()` builds the student worksheet, while `review_report()` records the decision and run metadata. `main()` saves an approved worksheet or a clearly marked rejected draft and returns a distinct exit code.

## Design decisions

- **Gemini model:** The default model is `gemini-3.8-flash` through Google's `google-genai` SDK. The exact model for a run is recorded in its review JSON. Use `--model` to select another available Gemini model. Output quality depends on the selected model.
- **Pydantic:** Validates the request and agent output shapes. It cannot validate factual correctness.
- **Bounded review:** One revision limits API calls and prevents an endless loop. `--max-revisions` can change the limit.
- **Safe failure:** If the final review rejects the material, the program returns exit code 2, saves `examples/drafts/<name>.md` and `examples/reviews/<name>.json`, and does not create an approved output at the requested path. API or input errors return exit code 1.
- **No retrieval:** The input does not specify a curriculum or reference collection, so the current workflow relies on the model and review. A curated curriculum source and retrieval could be added later.

## Install and run

Clone the private repository after accepting a collaborator invitation:

```powershell
git clone https://github.com/omar230717728/k12-worksheet-agents.git
cd k12-worksheet-agents
```

Use Python 3.10 or newer. Create and activate a virtual environment, then install dependencies:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey), then set it in the current shell. Do not put the key in source files or commit it:

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

Generate a worksheet by input name. The program reads `examples/inputs/linear_functions.json`, then writes `examples/worksheets/linear_functions.md` and `examples/reviews/linear_functions.json`:

```powershell
python -m worksheet_agents --input linear_functions
```

You can also pass a JSON file path with `--input`, and optionally choose a Markdown path with `--output`.

Or provide the four fields directly. The topic becomes the filename, so this writes `examples/worksheets/water_cycle.md` and `examples/reviews/water_cycle.json`:

```powershell
python -m worksheet_agents --subject Science --topic "Water Cycle" --grade 4 --objective "Explain evaporation, condensation, and precipitation in the water cycle"
```

The review JSON contains the model ID, input, approval status, revision count, and any unresolved issues. The three included examples cover different subjects and grades and were generated with `gemini-3.8-flash`.

If Gemini returns `503 UNAVAILABLE` after its built-in retries, try again later or choose the lower cost Flash-Lite model for the run:

```powershell
python -m worksheet_agents --input linear_functions --model gemini-3.5-flash-lite
```

The chosen model is recorded in the review JSON.

## Limitations and possible enhancements

The Reviewer is another model call and can miss an error, particularly in calculations. A teacher should inspect material before classroom use. Model responses can vary between runs. The tool does not currently verify alignment to a particular curriculum. Possible enhancements include subject-specific calculation checks, retrieval from an approved curriculum collection, and LangGraph if the workflow grows to need persistence or human approval steps.
