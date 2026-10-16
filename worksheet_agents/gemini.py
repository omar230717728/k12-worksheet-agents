import os
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredModel(Protocol):
    def generate(self, prompt: str, schema: type[T]) -> T: ...


class GeminiModel:
    def __init__(self, model_name: str) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("Set GEMINI_API_KEY before generating a worksheet.")
        from google import genai

        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model_name = model_name

    def generate(self, prompt: str, schema: type[T]) -> T:
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned no text; worksheet generation stopped.")
        return schema.model_validate_json(response.text)
