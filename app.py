import json
import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class MissingAPIKeyError(RuntimeError):
    """Raised when no Gemini API key is available."""


class GeminiLearningEngine:
    def __init__(self, api_key=None, model_name="gemini-2.5-flash"):
        api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise MissingAPIKeyError(
                "No API key found. Set GEMINI_API_KEY in a .env file or enter it in the sidebar."
            )
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    # ---------- core helper ----------
    def _generate(self, contents, system_instruction=None, json_output=False):
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json" if json_output else None,
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=contents, config=config
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}") from e
        if not response.text:
            raise RuntimeError("The model returned an empty response. Please try again.")
        return response.text

    # ---------- features ----------
    def chat_assistant(self, history, user_message, level="Beginner"):
        """history: list of {"role": "user"|"assistant", "content": str}"""
        system_instruction = (
            f"You are an encouraging, expert AI tutor. Explain concepts clearly for a {level} level student. "
            "Use simple analogies, break down complex ideas, and offer follow-up questions to test understanding."
        )
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"  # Gemini only accepts user/model
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))
        return self._generate(contents, system_instruction=system_instruction)

    def summarize_notes(self, study_text):
        prompt = (
            "Summarize the following study material into clear, concise notes. "
            "Highlight key formulas, definitions, and crucial takeaways using bullet points:\n\n"
            f"{study_text}"
        )
        return self._generate(prompt)

    def generate_questions(self, topic, mark_type):
        prompt = (
            f"Create 3 distinct {mark_type} exam-style review questions for the topic: {topic}. "
            "Provide a marking scheme describing what an ideal answer should include."
        )
        return self._generate(prompt)

    def generate_quiz(self, topic, level="Beginner", n=3):
        """Returns a list of dicts: {question, options[4], answer_index, explanation}"""
        prompt = (
            f"Generate a {n}-question multiple choice quiz on '{topic}' for a {level} student. "
            "Return ONLY a JSON array. Each item must have: "
            '"question" (string), "options" (array of exactly 4 strings, without A/B/C/D prefixes), '
            '"answer_index" (integer 0-3), "explanation" (short string).'
        )
        raw = self._generate(prompt, json_output=True)
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError("Could not parse the quiz. Please try again.") from e

        quiz = []
        for item in data if isinstance(data, list) else []:
            opts = item.get("options", [])
            idx = item.get("answer_index")
            if len(opts) == 4 and isinstance(idx, int) and 0 <= idx < 4 and item.get("question"):
                quiz.append(
                    {
                        "question": item["question"],
                        "options": [str(o) for o in opts],
                        "answer_index": idx,
                        "explanation": item.get("explanation", ""),
                    }
                )
        if not quiz:
            raise RuntimeError("The quiz came back in an unexpected format. Please try again.")
        return quiz

    def generate_study_plan(self, subjects, hours, days):
        prompt = (
            f"Create a structured {days}-day study schedule for these subjects: {subjects}, "
            f"with {hours} study hours available per day. Break tasks into realistic modules."
        )
        return self._generate(prompt)

    def solve_doubt(self, concept, level):
        prompt = (
            f"Explain the difficult academic concept '{concept}' to a {level} student. "
            "Use a real-world example or analogy to make it intuitive."
        )
        return self._generate(prompt)
