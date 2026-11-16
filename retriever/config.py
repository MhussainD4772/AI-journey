CONN = "postgresql://postgres:localdev@localhost:5433/postgres"

MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

# Files that are real markdown but not documentation: the 7,918-line
# changelog, contributor lists, site banners.
SKIP_FILES = {
    "release-notes.md",
    "fastapi-people.md",
    "newsletter.md",
    "external-links.md",
    "translations.md",
    "translation-banner.md",
    "agent-banner.md",
    "_llm-test.md",
}