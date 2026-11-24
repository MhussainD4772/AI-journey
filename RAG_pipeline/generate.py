import os
import sys
from dataclasses import dataclass

from google import genai
from google.genai import types

import config
from search import Result, hybrid_search

PROMPT = """You answer questions about research papers using only the numbered sources below.

Rules:
- Use only what the sources say. Do not add anything from your own knowledge.
- Put a citation after every claim, matching the source number: [1], or [1][3] if several support it.
- Be brief. A few sentences.

Sources:
{sources}

Question: {question}

Answer:"""


@dataclass
class Answer:
    text: str
    chunks: list[Result]   # position in this list + 1 == the [n] in the text


def build_sources(chunks: list[Result]) -> str:
    blocks = []
    for n, c in enumerate(chunks, start=1):
        blocks.append(f"[{n}] {c.title} (page {c.page})\n{c.content}")
    return "\n\n".join(blocks)


def answer(question: str, limit: int = 5) -> Answer:
    chunks = hybrid_search(question, limit=limit)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=config.GEN_MODEL,
        contents=PROMPT.format(sources=build_sources(chunks), question=question),
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=1500,
        ),
    )

    return Answer(text=(response.text or "").strip(), chunks=chunks)


def main() -> None:
    question = " ".join(sys.argv[1:])
    if not question:
        sys.exit("usage: python generate.py <question>")

    result = answer(question)

    print(f"\n{result.text}\n")
    print("sources")
    for n, c in enumerate(result.chunks, start=1):
        print(f"  [{n}] {c.chunk_key}  p{c.page}  {c.title[:60]}")


if __name__ == "__main__":
    main()