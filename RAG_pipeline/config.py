CONN = "postgresql://postgres:localdev@localhost:5433/rag"

MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

# Describes the strategy, not a number. When you compare chunking
# approaches later, this is what tells the two runs apart in the table.
VERSION = "v1-fixed1000-overlap2"

GEN_MODEL = "gemini-flash-lite-latest"
