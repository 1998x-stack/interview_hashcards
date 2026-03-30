"""
Card Generator — AI-assisted card creation via DashScope (qwen-max)
Uses the OpenAI-compatible endpoint.
"""
import openai

SYSTEM_PROMPT = """You are a flashcard generator for the hashcards system.

Output ONLY valid hashcards-format Markdown. No prose, no headings, no code fences.

Rules:
- Q&A format:  Q: <question>\nA: <answer>
- Cloze format: C: Sentence with [key term] filled in.
- One blank line between cards.
- Use Q&A for conceptual questions, cloze for factual recall.
- One card per distinct concept. Be concise.
- Do not number cards. Do not add any other text.
"""

class CardGenerator:
    """Generate hashcards-format cards from free text using qwen-max."""

    def __init__(self, api_key: str):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def generate(self, source_text: str, existing_decks: list) -> str:
        deck_hint = ""
        if existing_decks:
            deck_hint = f"\nExisting decks for context: {', '.join(existing_decks[:10])}."
        user_content = f"Generate flashcards from the following text.{deck_hint}\n\n---\n{source_text}"
        response = self.client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            extra_body={"enable_thinking": False},
        )
        return response.choices[0].message.content or ""
