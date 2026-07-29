This file preserves the original assignment brief. Completion evidence is mapped in
`README.md` and `docs/FINAL_REPORT.md`.

# Project 1: Prompting & RAG Foundations

**Stack:** watsonx.ai
**Duration:** 6 days
**Difficulty:** Tier 1 — Foundation

---

## Overview

Build an assistant that answers questions grounded in a set of documents — and can re-express any answer it gives in three different tones: a formal report summary, a casual message, and a concise executive briefing. The retrieval half teaches you how to ground a model in real data instead of letting it invent answers. The tone half teaches you how far prompt structure alone — system prompts, few-shot examples, structured output — can shape what a model produces from the same underlying content.

Together, these are the two most fundamental skills in AI application development: getting a model to answer only from facts you gave it, and getting a model to reliably follow instructions about *how* to say something. Every later project in this program builds on both.

---

## What to Build

A working pipeline with:

1. **Document ingestion** — load and chunk documents into a vector store
2. **Retrieval** — given a user question, find the most relevant chunks
3. **Grounded generation** — pass retrieved chunks to a watsonx.ai model with a well-crafted prompt to produce a grounded answer, with a source citation
4. **Tone transformation** — take any grounded answer and re-express it in three tones (formal report, casual message, executive briefing), each with its own prompt template and at least one few-shot example, returned as structured JSON
5. **A simple interface** — a minimal UI or CLI where a user asks a question, sees the grounded answer, and can request any of the three tone variations

The domain of the documents is up to you — a good default is a set of company policy documents, a product manual, or a few publicly available reports.

---

## Milestones

Work through these in order. There is no fixed day-by-day schedule — move at the pace that gets each milestone genuinely done, not just checked off.

### Milestone 1 — Understand the problem
- Read about RAG architecture: what a vector store is, what embeddings are, why chunking matters
- Read about the difference between system prompts and user prompts in foundation model APIs
- Set up the watsonx.ai environment and confirm API access
- Choose a document set (3–5 documents is enough to start)
- Define the three tones the tool will support and write down in plain English what makes each one distinct
- Deliverable: a short written plan covering your document set, chosen tones, and how you'll test both

### Milestone 2 — Build the ingestion and retrieval pipeline
- Load documents and split them into chunks
- Generate embeddings using watsonx.ai embedding models
- Store embeddings in a vector store (Chroma, FAISS, or watsonx's built-in options)
- Given a user query, retrieve the top-k relevant chunks
- Deliverable: a script that ingests documents and retrieves relevant chunks for a test question

### Milestone 3 — Build grounded generation and the first tone
- Construct a RAG prompt that includes the retrieved context and the question, instructing the model to answer only from that context
- Call a watsonx.ai foundation model and return a grounded answer with a source citation
- Pick one tone (start with the formal report summary) and write a system prompt that reliably re-expresses a grounded answer in that tone
- Test the tone prompt against at least 5 different grounded answers — does it hold the tone consistently?
- Deliverable: an end-to-end pipeline that answers a question from documents, plus one working, tested tone prompt

### Milestone 4 — Build the remaining tones and structure the output
- Repeat the tone-prompt process for the casual message and executive summary tones
- Add at least one few-shot example to each tone template and observe whether consistency improves
- Return all three tone variations in a consistent JSON structure (e.g. `{ "tone": "formal", "output": "..." }`)
- Handle failures gracefully — what happens if a tone call fails or returns malformed JSON?
- Deliverable: three working tone templates, wired together so a single grounded answer can be requested in any tone

### Milestone 5 — Improve and iterate
- Experiment with chunk size and overlap — how does it affect answer quality?
- Try different RAG prompt structures — when does the model perform better?
- Add a "source" citation to every grounded answer (which document and section it came from)
- Deliberately test edge cases in the tone prompts: an input already in the target tone, a very short input, a non-English input
- Deliverable: at least 3 documented chunking/prompt experiments with written observations, and notes on at least one tone edge case

### Milestone 6 — Evaluate, compare models, and reflect
- Build a test set of at least 20 questions with expected answers for the retrieval/grounding side
- Score the system: how many does it get right, partially right, or wrong? Find at least 3 questions it answers incorrectly and diagnose why
- Separately, evaluate tone consistency across the same 20 inputs — are the three outputs genuinely distinct for each?
- Swap the generation model for a smaller/cheaper one — does grounding accuracy or tone quality drop noticeably? For which task?
- Deliverable: an evaluation report covering retrieval accuracy, failure analysis, tone consistency, and a model comparison

---

## Key Concepts to Understand

These are the things you should be able to explain by the end.

### Chunking
Documents are too long to send to a model in one go. Chunking splits them into smaller pieces. The size of each chunk and how much they overlap with each other affects what the model can see when answering a question.

- **Too small:** chunks lose context (a sentence without the paragraph around it is often meaningless)
- **Too large:** you retrieve less specific content and may exceed the model's context window
- **Overlap:** helps prevent a relevant sentence being split across two chunks where neither chunk alone is useful

### Embeddings and Similarity Search
An embedding is a numerical representation of text that captures its meaning. Two chunks that mean similar things will have embeddings that are close together in vector space. This is what allows retrieval: convert the user's question into an embedding, find the chunks whose embeddings are closest, and those are the most relevant chunks.

### Prompt Construction and Grounding
The instruction "only use the context" is what prevents hallucination. Without it, the model will fill gaps with its training knowledge, which may be wrong or outdated. Grounding means anchoring the model's output to real source material — citations are a grounding technique, because if the model must say where it got the answer, it's harder for it to invent one.

### Hallucination
A model hallucinating means it generates plausible-sounding but incorrect information. In a RAG system, hallucination usually happens when the retrieved chunks don't actually contain the answer, the prompt doesn't clearly instruct the model to stay within the context, or the model is asked about something not covered by any document.

### System Prompts vs. User Prompts
- **System prompt:** sets the model's persistent behaviour, role, and constraints for the entire interaction. This is where you define the tone, the output format, and any rules the model must follow.
- **User prompt:** the actual input for this specific request — the topic or raw text to transform.

Keeping these separate matters because it lets you reuse the same system prompt (tone definition) across many different inputs without rewriting it each time.

### Few-Shot Prompting
A zero-shot prompt gives the model instructions only. A few-shot prompt also includes examples of what good output looks like. Few-shot examples are one of the most reliable ways to steer a model toward a specific style — the key is that the examples must be genuinely representative; bad examples teach bad behaviour.

### Output Formatting and Structured Generation
Asking a model to return JSON is useful but fragile if not done carefully. The prompt must state the exact structure expected, provide a schema or example, and instruct the model not to add explanation outside the JSON. Even with careful prompting, models occasionally produce malformed JSON — the pipeline must handle this, either by validating and retrying, or by falling back to plain text.

### Model Selection Tradeoffs
Not all tasks need the most capable model. Grounded question-answering over documents often benefits from a larger, more capable model (it has to reason over retrieved context and avoid hallucinating). Tone transformation of already-correct content is often fine with a smaller, faster model — it's mostly style, not reasoning. You should be able to argue your model choice for each task, not just accept the default.

### Prompt Brittleness
A prompt that works well on 5 test cases can fail on the 6th. Common reasons: the input is longer or shorter than what the prompt was designed around, the input contains formatting the prompt doesn't account for, or the input is in a different domain than what was tested. Robustness means testing against diverse inputs, not just the easy ones.

---

## Acceptance Criteria

### The system must:
- [ ] Answer questions correctly, grounded in the documents, for at least 70% of the retrieval test set
- [ ] Include a source citation (document name and section) with every grounded answer
- [ ] Return a clear "I don't know" when the answer isn't in the documents, rather than guessing
- [ ] Produce distinct, recognisably different outputs for each of the three tones given the same grounded answer
- [ ] Return tone output in a consistent, structured format (JSON or clearly delimited sections), with at least one few-shot example per tone template
- [ ] Handle malformed or unexpected model output without crashing
- [ ] Include at least 3 documented chunking/prompt experiments with written observations
- [ ] Include an evaluation report covering: retrieval test set results and failure analysis, tone consistency across 20 inputs, and a model comparison

---

## Common Pitfalls to Watch For

- **Retrieving too few chunks:** top-1 retrieval often misses relevant context. Start with top-3 or top-5.
- **Not cleaning documents:** raw PDFs often have headers, footers, and page numbers mixed into the text. This noise ends up in chunks and confuses retrieval.
- **Testing only easy questions:** require questions where the answer spans multiple sections or where the answer is simply not in the documents.
- **Ignoring latency:** each question triggers at least two API calls (embedding + generation), plus one more per tone requested. You should be aware of this and not be surprised when it feels slow.
- **Prompt drift across tones:** it's common to write the first tone prompt carefully and rush the other two. All three need the same level of rigour.
- **Over-constraining length:** telling the model "write exactly 280 characters" is much harder to enforce than "keep it under 3 sentences." Soft constraints are more reliable than hard ones.
- **Assuming JSON is always valid:** models will occasionally return text before or after the JSON block, add trailing commas, or use single quotes. The pipeline needs a parsing step that handles this.
- **Treating all failures as prompt failures:** sometimes the model produces poor output because the input itself is ambiguous or very short. Distinguish between prompt problems and input problems.

---

## Stretch Goals (for more experienced trainees)

- Add a **re-ranking step** after retrieval: retrieve top-10 chunks, then use a model to score which are actually relevant before passing to generation
- Implement **hybrid search**: combine semantic (embedding) search with keyword (BM25) search for better coverage
- Add a **fourth tone** of your own design — define it, write the prompt, and justify why it's a useful addition
- Implement **self-evaluation**: after generating each tone variation, make a second model call that scores the output on tone adherence (1–5) and flags any that fall below a threshold for regeneration
- Expose the system via a simple **REST API** so it could be called by another application

---

## Resources

- watsonx.ai documentation: embedding models, foundation model inference, prompt engineering guide, and model parameters reference
- IBM prompt lab: useful for manual experimentation before writing code
- LangChain or LlamaIndex docs for RAG pipeline patterns (framework-agnostic concepts apply)
- "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020) — the original RAG paper, worth skimming for context
- "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (Wei et al., 2022) — useful background on how prompt structure shapes model behaviour

## Practitioner Resources

- [IBM watsonx.ai Prompt Lab docs](https://www.ibm.com/docs/en/watsonx/saas?topic=prompts-prompt-lab) — official guide to structuring prompts with system/user roles, variables, and decoding params in watsonx.ai.
- [RAG on watsonx.ai](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-rag.html?context=wx) — official docs on embeddings, vector index retrievers, and grounding responses in watsonx.
- [Optimizing your RAG knowledge base](https://www.ibm.com/docs/en/watsonx/saas?topic=generation-optimizing-your-rag-knowledge-base) — IBM's guidance on preparing and splitting source documents for retrieval quality.
- [Choosing a foundation model](https://www.ibm.com/docs/en/watsonx/saas?topic=models-choosing-model) — IBM's framework for model selection tradeoffs (task fit, size, tuning options).
- [IBM: What is few-shot prompting?](https://www.ibm.com/think/topics/few-shot-prompting) — concise explainer with examples of few-shot prompting patterns.
- [Pinecone: Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/) — deep dive on fixed-size, content-aware, and semantic chunking approaches for RAG.
- [Pinecone: Vector Similarity Explained](https://www.pinecone.io/learn/vector-similarity/) — clear breakdown of cosine, dot-product, and Euclidean similarity metrics.
- [LangChain: Text Splitters](https://docs.langchain.com/oss/python/integrations/splitters) — practical implementation reference for chunking documents before embedding.
- [Anthropic: Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — foundational guide covering system vs user prompts and few-shot techniques.
- [Anthropic: Reducing Hallucinations / Guardrails](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/keep-claude-in-character) — techniques for grounding, consistency, and robustness under adversarial input.
- [OpenAI: Structured Outputs Guide](https://developers.openai.com/api/docs/guides/structured-outputs) — how to enforce JSON-schema-conformant output from LLMs.
- [Prompting Guide: Few-Shot Prompting](https://www.promptingguide.ai/techniques/fewshot) — community reference with worked examples and pitfalls of few-shot prompting.
