# retriever/queries.py

# (query, the file that should answer it)
#
# Deliberately mixed:
#   - conceptual, phrased unlike the docs  -> vector should win
#   - bare identifiers                     -> keyword should win
#   - in between                           -> hybrid should earn its keep

QUERIES = [
    # conceptual — almost no vocabulary overlap with the docs
    ("how do I return a different status code depending on whether the item existed",
     "advanced/response-change-status-code.md"),

    ("what is the difference between async def and def for a path operation",
     "async.md"),

    ("how do I send JSON data to my API from a client",
     "tutorial/body.md"),

    ("how do I clean up a database session after the request finishes",
     "tutorial/dependencies/dependencies-with-yield.md"),

    ("reading configuration from the shell",
     "environment-variables.md"),

    ("how do I run the development server",
     "fastapi-cli.md"),

    # bare identifiers — no meaning to embed, exact token match wanted
    ("HTTPException", "tutorial/handling-errors.md"),

    ("RedirectResponse", "advanced/custom-response.md"),

    ("venv", "virtual-environments.md"),

    # in between — a real term plus natural phrasing
    ("declaring the type of a function argument in python",
     "python-types.md"),
]