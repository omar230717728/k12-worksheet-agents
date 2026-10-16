from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorksheetRequest(StrictModel):
    subject: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    learning_objective: str = Field(min_length=1)

    @field_validator("subject", "topic", "grade", "learning_objective")
    @classmethod
    def strip_and_require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class LessonPlan(StrictModel):
    concepts: list[str] = Field(min_length=1)
    teaching_sequence: list[str] = Field(min_length=1)
    exercise_targets: list[str] = Field(min_length=1)
    grade_guidance: str = Field(min_length=1)


class WorkedExample(StrictModel):
    title: str
    problem: str
    steps: list[str] = Field(min_length=1)
    answer: str


class Exercise(StrictModel):
    question: str
    solution: str


class Worksheet(StrictModel):
    explanation: str = Field(min_length=1)
    worked_examples: list[WorkedExample] = Field(min_length=1)
    summary: list[str] = Field(min_length=1)
    exercises: list[Exercise] = Field(min_length=3)


class ReviewIssue(StrictModel):
    section: str
    problem: str
    requested_fix: str


class Review(StrictModel):
    approved: bool
    issues: list[ReviewIssue]

    @model_validator(mode="after")
    def decision_matches_issues(self) -> "Review":
        if self.approved and self.issues:
            raise ValueError("an approved review must have no issues")
        if not self.approved and not self.issues:
            raise ValueError("a rejected review must explain at least one issue")
        return self
