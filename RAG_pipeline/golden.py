
# (question, expected_paper_id, expected_answer)
# expected_paper_id of None means the corpus cannot answer it and the
# system should refuse.

GOLDEN = [
    # --- conceptual, phrased unlike the paper
    ("what abilities does a language model need for retrieval to work",
     "2309.01431v2",
     "Noise robustness, negative rejection, information integration, counterfactual robustness."),

    ("which of those abilities do models handle worst",
     "2309.01431v2",
     "Negative rejection, information integration, and dealing with false information."),

    ("does splitting documents by meaning beat splitting them by size",
     "2607.01852v1",
     "No. Cluster-based semantic chunking did not outperform fixed-size or recursive chunking."),

    ("why can't you train the retriever and the generator together",
     "2406.03790v2",
     "Instance retrieval is non-differentiable, so gradients cannot flow through it."),

    ("what goes wrong when a model is trained on cleaner context than it sees in production",
     "2403.14197v1",
     "Fusion-in-Decoder overfits to the training context quality and performs worse on different quality."),

    ("is retrieving the most similar passage always the right thing to do",
     "2405.19893v1",
     "No. MetRag argues similarity alone can degrade performance, and adds utility and compactness."),

    ("what breaks when retrieved evidence doesn't match what the model is asked to produce",
     "2603.04647v1",
     "Semantic misalignment between retrieved results and generation objectives, plus poor evidence use."),

    ("what limits plain vector retrieval on questions that need several sources",
     "2502.01113v3",
     "It struggles to capture relationships between pieces of knowledge, limiting multi-hop reasoning."),

    # --- specific identifiers
    ("TACRED", "2406.03790v2",
     "The relation extraction benchmark ETRAG was evaluated on."),

    ("GROBID", "2412.15404v1",
     "The tool used to extract bibliographic information in the literature navigation system."),

    ("RAGAS", "2412.15404v1",
     "The Retrieval-Augmented Generation Assessment framework used for evaluation."),

    ("WebQA and MultimodalQA", "2512.17194v1",
     "The two multi-modal RAG benchmarks MMRAG-RFT reaches state of the art on."),

    ("frame semantics", "2406.16167v1",
     "The cognitive linguistic theory FS-RAG uses for indexing and retrieving facts."),

    # --- factual lookups
    ("how many parameters does the graph foundation model have",
     "2502.01113v3",
     "8 million."),

    ("how much data was the graph foundation model trained on",
     "2502.01113v3",
     "60 knowledge graphs, over 14M triples, 700k documents."),

    ("how does cross-attention change as training context quality improves",
     "2403.14197v1",
     "The model attends more uniformly across each passage in the context."),

    # --- should be refused: plausible, not in this corpus
    ("what does OpenAI charge per token for embeddings", None, None),
    ("how well does retrieval augmented generation work for medical diagnosis", None, None),
    ("what chunk size does LangChain use by default", None, None),
    ("which vector database has the lowest latency at a billion vectors", None, None),
]