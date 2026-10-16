from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorksheetRequest(StrictInputModel):
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


class LessonPlan(BaseModel):
    concepts: list[str]
    teaching_sequence: list[str]
    exercise_targets: list[str]
    grade_guidance: str

    @model_validator(mode="after")
    def require_content(self) -> "LessonPlan":
        if not all((self.concepts, self.teaching_sequence, self.exercise_targets, self.grade_guidance.strip())):
            raise ValueError("lesson plan sections must not be empty")
        return self


class WorkedExample(BaseModel):
    title: str
    problem: str
    steps: list[str]
    answer: str


class Exercise(BaseModel):
    question: str
    solution: str


class Worksheet(BaseModel):
    explanation: str
    worked_examples: list[WorkedExample]
    summary: list[str]
    exercises: list[Exercise]

    @model_validator(mode="after")
    def require_sections(self) -> "Worksheet":
        if not self.explanation.strip() or not self.worked_examples or not self.summary:
            raise ValueError("worksheet explanation, examples, and summary are required")
        if len(self.exercises) < 3:
            raise ValueError("worksheet needs at least three exercises")
        return self


class ReviewIssue(BaseModel):
    section: str
    problem: str
    requested_fix: str


class Review(BaseModel):
    approved: bool
    issues: list[ReviewIssue]

    @model_validator(mode="after")
    def decision_matches_issues(self) -> "Review":
        if self.approved and self.issues:
            raise ValueError("an approved review must have no issues")
        if not self.approved and not self.issues:
            raise ValueError("a rejected review must explain at least one issue")
        return self
