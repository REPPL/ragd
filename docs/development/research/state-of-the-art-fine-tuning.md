# State-of-the-Art Fine-Tuning for Local RAG Systems

> **Note:** This document surveys state-of-the-art techniques for fine-tuning models
> in local RAG systems. ragd implements **local-only** processing with equal support
> for Apple Silicon (MLX) and CUDA (Unsloth/Axolotl) platforms.

## Executive Summary

**Key Recommendations for ragd:**

1. **Start with Embedding Fine-Tuning:** Lower barrier, 5-25% retrieval improvement, works with existing Ollama LLM
2. **Use Synthetic Data:** LLM-generated query-document pairs scale better than manual labelling
3. **Platform-Adaptive:** MLX for Apple Silicon, Unsloth for CUDA - both achieve similar results
4. **Progressive Complexity:** Embeddings first, then rerankers, then LLM fine-tuning (RAFT)
5. **Minimum Dataset:** 5,000-10,000 query-document pairs for meaningful improvement

### When to Fine-Tune vs Use Off-the-Shelf Models

```
START
  |
  +-- Is domain vocabulary highly specialised? (legal, medical, technical)
  |     +-- YES --> Fine-tune embeddings (5-25% improvement expected)
  |     +-- NO  --> Continue
  |
  +-- Are retrieval results unsatisfactory with general models?
  |     +-- YES --> Fine-tune embeddings + evaluate
  |     +-- NO  --> Use off-the-shelf (nomic-embed, BGE-M3)
  |
  +-- Do you have domain-specific query-answer pairs?
  |     +-- YES --> Consider RAFT for LLM fine-tuning (35-76% improvement)
  |     +-- NO  --> Use synthetic data generation first
  |
  +-- Is reranking precision critical?
        +-- YES --> Fine-tune cross-encoder or ColBERT
        +-- NO  --> Use pre-trained BGE-reranker
```

---

## Fine-Tuning Components in RAG Systems

A complete RAG system has three components that can benefit from fine-tuning:

| Component | Purpose | Fine-Tuning Impact | Difficulty |
|-----------|---------|-------------------|------------|
| **Embedding Model** | Document/query representation | 5-25% retrieval improvement | Low |
| **Reranker** | Precision re-scoring | 10-20% precision improvement | Medium |
| **LLM** | Answer generation | 35-76% domain accuracy | High |

### Recommended Fine-Tuning Order

1. **Embedding models** - Fastest ROI, affects entire pipeline
2. **Rerankers** - Improves precision without changing storage
3. **LLM (RAFT)** - Highest potential but most complex

---

## 1. Embedding Model Fine-Tuning

### Why Fine-Tune Embeddings?

Embedding models are trained on general knowledge corpora, which limits their effectiveness for domain-specific retrieval. Fine-tuning aligns the model's similarity metrics with domain-specific context and terminology.

**Expected Improvements:**

| Scenario | Typical Improvement |
|----------|---------------------|
| General domain adaptation | 5-10% |
| Specialised document formats | 10-15% |
| Legal/medical with training data | 15-25% |
| Code retrieval | 10-20% |

**Key Finding:** A smaller, carefully fine-tuned model can outperform larger, general-purpose embedding models in specific domains.

### Contrastive Learning Approach

The standard approach uses **contrastive learning** with `MultipleNegativesRankingLoss`:

```python
from sentence_transformers import SentenceTransformer, losses
from sentence_transformers.training_args import SentenceTransformerTrainingArguments
from sentence_transformers.trainer import SentenceTransformerTrainer

# Load base model
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# Define loss function
loss = losses.MultipleNegativesRankingLoss(model)

# Training arguments
args = SentenceTransformerTrainingArguments(
    output_dir="./finetuned-embeddings",
    num_train_epochs=3,
    per_device_train_batch_size=32,
    learning_rate=2e-5,
    warmup_ratio=0.1,
)

# Train
trainer = SentenceTransformerTrainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    loss=loss,
)
trainer.train()
```

### Hard Negative Mining

Hard negatives are samples difficult to distinguish from positives but don't contain the answer. They force models to learn more discriminative features.

**Mining Strategies:**

1. **BM25 Negatives:** Top BM25 results that aren't relevant
2. **Semantic Negatives:** Nearest neighbours in embedding space that aren't relevant
3. **LLM-Generated:** Ask LLM to create plausible but incorrect contexts

```python
def mine_hard_negatives(query: str, positive_doc: str, index, top_k: int = 10):
    """Mine hard negatives from existing index."""
    # Get similar documents
    candidates = index.search(query, top_k=top_k * 2)

    # Filter out the positive document
    negatives = [doc for doc in candidates if doc.id != positive_doc.id]

    # Return top-k hardest negatives
    return negatives[:top_k]
```

### Matryoshka Representation Learning (MRL)

MRL creates embeddings that can be truncated to various dimensions without significant quality loss. This enables flexible storage/performance trade-offs.

**How It Works:**

During training, the model optimises not just one loss function but several - for the full embedding dimension and progressively smaller truncations (e.g., 768, 512, 256, 128, 64).

```python
from sentence_transformers import losses

# Matryoshka loss wraps the base loss
matryoshka_loss = losses.MatryoshkaLoss(
    model,
    loss=losses.MultipleNegativesRankingLoss(model),
    matryoshka_dims=[768, 512, 256, 128, 64]
)
```

**Benefits:**
- Up to 14x smaller embedding size at same accuracy level
- Flexible dimension selection at inference time
- Adopted by OpenAI (text-embedding-3), Nomic, and Alibaba GTE

**Performance Retention:**

| Dimension | % of Full Performance |
|-----------|----------------------|
| 768 (full) | 100% |
| 512 | ~99% |
| 256 | ~98% |
| 128 | ~95% |
| 64 | ~90% |

### Dataset Requirements

**Minimum Viable Dataset:** 5,000-10,000 query-document pairs

**Dataset Formats:**

| Format | Description | Use Case |
|--------|-------------|----------|
| **Positive Pairs** | (query, relevant_document) | Basic fine-tuning |
| **Triplets** | (query, positive, negative) | With hard negatives |
| **Scored Pairs** | (text1, text2, similarity_score) | Regression tasks |

### Fine-Tuning Performance Benchmarks

**Results from Phil Schmid's experiments:**

- Base model: 78% hit-rate
- Fine-tuned (6.3k samples): 84% hit-rate (+7%)
- Training time: 3 minutes on consumer GPU
- OpenAI ada-002: 87% (fine-tuned only 3% behind)

---

## 2. LLM Fine-Tuning for RAG (RAFT)

### What is RAFT?

**RAFT (Retrieval Augmented Fine-Tuning)** is a training recipe that improves a model's ability to answer questions in "open-book" settings by teaching it to:

1. Identify relevant documents from retrieved context
2. Ignore distractor documents
3. Generate answers with verbatim citations

### How RAFT Works

```
Training Data Format:
  Question + [Oracle Document + Distractor Documents] → Chain-of-Thought Answer with Citations

Key Insight: Train with P=80% oracle document present, 20% without
```

**Training Process:**

1. Prepare question-answer pairs from your domain
2. For each question, include the oracle (correct) document
3. Add distractor documents (irrelevant but plausible)
4. Train model to cite the oracle document verbatim
5. Include some training examples WITHOUT the oracle document

```python
def create_raft_training_example(
    question: str,
    answer: str,
    oracle_doc: str,
    distractor_docs: list[str],
    include_oracle: bool = True  # 80% True, 20% False
):
    """Create RAFT-style training example."""
    context_docs = distractor_docs.copy()

    if include_oracle:
        # Insert oracle at random position
        insert_pos = random.randint(0, len(context_docs))
        context_docs.insert(insert_pos, oracle_doc)

    context = "\n\n".join([
        f"[Document {i+1}]: {doc}"
        for i, doc in enumerate(context_docs)
    ])

    prompt = f"""Context:
{context}

Question: {question}

Answer with citations:"""

    # Chain-of-thought answer with ##begin_quote## markers
    cot_answer = generate_cot_answer(answer, oracle_doc)

    return {"prompt": prompt, "completion": cot_answer}
```

### RAFT Performance Results

| Dataset | Improvement vs Llama-2 |
|---------|----------------------|
| PubMed | Significant |
| HotpotQA | +35.25% |
| Torch Hub | +76.35% |

### LoRA and QLoRA for Efficient Fine-Tuning

**LoRA (Low-Rank Adaptation):** Adds small trainable matrices to frozen base model weights.

**QLoRA (Quantised LoRA):** Combines LoRA with 4-bit quantisation for massive memory savings.

| Method | Memory Required | Training Speed | Quality |
|--------|-----------------|----------------|---------|
| Full Fine-tune | 48GB+ | Slow | Best |
| LoRA | 12-16GB | Fast | ~98% of full |
| QLoRA | 6-8GB | Medium | ~95-98% of full |

**QLoRA Innovations:**
- **4-bit NormalFloat (NF4):** Optimal for normally distributed weights
- **Double Quantisation:** Quantises the quantisation constants
- **Paged Optimisers:** Manages memory spikes during training

### Best Practices for LLM Fine-Tuning

1. **Learning Rate:** At least 10x lower than pre-training (e.g., 2e-5)
2. **Epochs:** Maximum 3 epochs to avoid overfitting
3. **Batch Size:** Large batches (32+) for stability
4. **Precision:** Use 16-bit (bf16/fp16) for efficiency
5. **Data Quality:** Quality matters more than quantity

**Common Pitfalls:**
- Misconfigured 4-bit/bitsandbytes settings leading to NaN losses
- Training for too many epochs (overfitting)
- Insufficient hard negatives in training data

---

## 3. Reranker Fine-Tuning

### Reranker Types

| Type | Approach | Speed | Accuracy |
|------|----------|-------|----------|
| **Cross-Encoder** | Concatenate query+doc, classify | Slow | Highest |
| **ColBERT** | Late interaction, token-level | Medium | High |
| **Bi-Encoder** | Separate embeddings, dot product | Fast | Good |

### Cross-Encoder Fine-Tuning

Cross-encoders process query and document together, enabling full attention between them:

```python
from sentence_transformers import CrossEncoder

# Load base cross-encoder
model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

# Fine-tune on domain data
model.fit(
    train_dataloader=train_dataloader,
    evaluator=evaluator,
    epochs=3,
    warmup_steps=100,
    output_path='./finetuned-reranker'
)
```

**Trade-off:** Each document requires a full forward pass. For 100 documents per query, this means 100x the compute of a bi-encoder.

### ColBERT and Late Interaction

ColBERT uses **late interaction** - computing embeddings separately but using token-level similarity:

```
Query:  "What is machine learning?"
         [Q1, Q2, Q3, Q4] → Token embeddings

Document: "Machine learning is a subset of AI..."
          [D1, D2, D3, D4, ...] → Token embeddings

Score = MaxSim(Q_tokens, D_tokens)
```

**Advantages:**
- Pre-compute document embeddings (storage efficient)
- Query-time computation only for query tokens
- Better than bi-encoders, faster than cross-encoders

**Jina ColBERT v2 (August 2024):**
- Multilingual support (89 languages)
- Flexible output dimensions
- Integrates with RAGatouille library

### RAG-Retrieval Unified Framework

The [RAG-Retrieval](https://github.com/NovaSearch-Team/RAG-Retrieval) project provides unified fine-tuning for:

- Embedding models (BERT-based, LLM-based)
- Late interaction models (ColBERT)
- Reranker models (Cross-encoder, LLM-based)

**Supported Models:**
- BGE family (bge-embedding, bge-m3, bge-reranker)
- BCE, GTE, and other open-source models
- Stella and Jasper (December 2024)

---

## 4. Synthetic Data Generation

### The LlamaIndex Approach

Generate hypothetical questions from document chunks:

```python
from llama_index.finetuning import generate_qa_embedding_pairs

# Generate training data from documents
qa_pairs = generate_qa_embedding_pairs(
    documents=documents,
    llm=ollama_llm,  # Use local LLM
    num_questions_per_chunk=2
)
```

**Process:**
1. Chunk documents into passages
2. For each chunk, generate 2-5 hypothetical questions
3. Pair questions with source chunks as positives
4. Mine hard negatives from other chunks

### Quality Filtering with LLM-as-Judge

Enterprise approaches (e.g., Databricks) filter synthetic queries:

```python
def filter_with_llm_judge(query: str, document: str, llm) -> bool:
    """Use LLM to filter low-quality synthetic pairs."""
    prompt = f"""Rate if this question can be answered by this document.

Question: {query}
Document: {document}

Answer YES if the document contains information to answer the question.
Answer NO otherwise.

Rating:"""

    response = llm.generate(prompt)
    return "YES" in response.upper()
```

### Hard Negative Generation

**NVIDIA's Approach:**

1. Use BM25 to find lexically similar but irrelevant documents
2. Use embedding similarity to find semantically close negatives
3. Filter to ensure negatives don't actually answer the query

```python
def generate_hard_negatives(
    query: str,
    positive_doc: str,
    corpus: list[str],
    embedding_model,
    bm25_index,
    num_negatives: int = 5
) -> list[str]:
    """Generate hard negatives using hybrid approach."""

    # BM25 candidates
    bm25_candidates = bm25_index.search(query, k=20)

    # Embedding candidates
    query_emb = embedding_model.encode(query)
    emb_candidates = semantic_search(query_emb, corpus, k=20)

    # Combine and filter
    all_candidates = set(bm25_candidates + emb_candidates)
    all_candidates.discard(positive_doc)

    # Rank by difficulty (closest to positive but still negative)
    positive_emb = embedding_model.encode(positive_doc)
    ranked = sorted(
        all_candidates,
        key=lambda x: cosine_similarity(
            embedding_model.encode(x),
            positive_emb
        ),
        reverse=True
    )

    return ranked[:num_negatives]
```

---

## 5. Local Fine-Tuning Frameworks

### CUDA/Linux/Windows

#### Unsloth

**Best for:** Single GPU, maximum efficiency

- 2-5x faster training than standard implementations
- 80% less memory usage vs FlashAttention 2
- Custom Triton kernels for optimised attention
- Supports: Llama 3/4, Gemma 3, Mistral, Phi, Qwen, DeepSeek

```python
from unsloth import FastLanguageModel

# Load model with 4-bit quantisation
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3.2-3b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0,
)
```

**Limitations:**
- Single GPU only (open-source version)
- Limited model architecture support

#### Axolotl

**Best for:** Multi-GPU, beginners, flexibility

- YAML-based configuration
- Multi-GPU support via DeepSpeed
- Wide model support (Llama, Mistral, Falcon, Gemma, Phi)
- Easy dataset preparation

```yaml
# axolotl config.yml
base_model: meta-llama/Llama-3.2-3B
model_type: LlamaForCausalLM

load_in_4bit: true
adapter: qlora
lora_r: 32
lora_alpha: 64

datasets:
  - path: ./raft_training_data.json
    type: alpaca

sequence_len: 2048
micro_batch_size: 4
gradient_accumulation_steps: 4
num_epochs: 3
learning_rate: 2e-5
```

#### Torchtune

**Best for:** PyTorch purists, research

- Pure PyTorch implementation
- Memory-efficient recipes
- Multi-node training (February 2025)
- Tested on 24GB consumer GPUs

### Apple Silicon (MLX)

#### MLX Framework

Apple's native framework for Apple Silicon, optimising for unified memory architecture.

**Key Advantages:**
- Unified memory: No CPU-GPU transfer overhead
- Native Metal acceleration
- 7B model fine-tuning on 16GB M-series Macs
- ~15-20 minutes for LoRA fine-tuning on M3

```python
import mlx.core as mx
from mlx_lm import load, generate
from mlx_lm.tuner import train

# Load model
model, tokenizer = load("mlx-community/Llama-3.2-3B-4bit")

# Fine-tune with LoRA
train(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_data,
    args={
        "adapter_file": "adapters.npz",
        "iters": 1000,
        "batch_size": 4,
        "learning_rate": 1e-5,
        "lora_rank": 8,
    }
)
```

#### mlx-lm for LLM Fine-Tuning

```bash
# Install
pip install mlx-lm

# Fine-tune with LoRA
python -m mlx_lm.lora \
    --model mlx-community/Llama-3.2-3B-4bit \
    --train \
    --data ./training_data \
    --iters 1000
```

#### Performance on Apple Silicon

| Mac | Memory | 7B Model LoRA | 3B Model LoRA |
|-----|--------|---------------|---------------|
| M1 16GB | 13-14GB peak | 15-20 min | 8-12 min |
| M2 16GB | 12-13GB peak | 12-18 min | 6-10 min |
| M3 Pro 18GB | 12GB peak | 8-12 min | 5-8 min |
| M3 Max 64GB | 15GB peak | 6-10 min | 4-6 min |

---

## 6. Hardware Requirements Summary

### Embedding Fine-Tuning

| Hardware | Memory Required | Training Time (6k samples) |
|----------|-----------------|---------------------------|
| CPU only | 8GB RAM | 30-60 min |
| Consumer GPU (RTX 3060) | 6GB VRAM | 3-5 min |
| Apple M1/M2 | 8GB unified | 5-10 min |
| Apple M3+ | 8GB unified | 3-5 min |

### LLM Fine-Tuning (7B Model)

**CUDA Systems:**

| Method | VRAM Required | Training Time |
|--------|---------------|---------------|
| Full Fine-tune | 48GB+ | Hours |
| LoRA | 12-16GB | 20-40 min |
| QLoRA | 6-8GB | 30-60 min |

**Apple Silicon:**

| Method | Unified Memory | Training Time |
|--------|----------------|---------------|
| LoRA (MLX) | 12-16GB | 15-25 min |
| QLoRA (MLX) | 8-12GB | 20-35 min |

### Reranker Fine-Tuning

| Model Type | Memory Required | Training Time |
|------------|-----------------|---------------|
| Cross-encoder (MiniLM) | 4-6GB | 10-20 min |
| Cross-encoder (BERT-large) | 8-12GB | 30-60 min |
| ColBERT | 8-12GB | 20-40 min |

---

## 7. Integration with ragd

### Embedder Protocol Compatibility

Fine-tuned models integrate via the existing `Embedder` protocol:

```python
# src/ragd/embedding/embedder.py
class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...
```

**Implementation for Fine-Tuned Models:**

```python
class FineTunedEmbedder:
    def __init__(self, model_path: str):
        self.model = SentenceTransformer(model_path)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts).tolist()

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return f"finetuned:{self.model_path}"
```

### Configuration Extension

```yaml
embedding:
  # Use fine-tuned model
  model: "custom"
  custom_model_path: "~/.ragd/models/finetuned-embeddings"

  # Or use base model with fine-tuned adapters
  model: "BAAI/bge-small-en-v1.5"
  adapter_path: "~/.ragd/adapters/domain-specific"
```

### Platform Detection

ragd already has hardware detection (`src/ragd/hardware.py`). Fine-tuning can leverage this:

```python
from ragd.hardware import detect_hardware, HardwareTier

def get_finetuning_backend():
    hw = detect_hardware()

    if hw.has_cuda:
        return "unsloth"  # or "axolotl" for multi-GPU
    elif hw.has_mps:  # Apple Silicon
        return "mlx"
    else:
        return "cpu"  # Defer to cloud/Colab
```

---

## 8. Evaluation and Benchmarking

### RAGAS Metrics for Fine-Tuned RAG

| Metric | Measures | Target |
|--------|----------|--------|
| **Context Precision** | Retrieved docs relevance | > 0.8 |
| **Context Recall** | Coverage of ground truth | > 0.7 |
| **Faithfulness** | Answer grounded in context | > 0.9 |
| **Answer Relevancy** | Answer addresses question | > 0.8 |

### A/B Testing Fine-Tuned Models

```python
def evaluate_model_ab(
    base_model: Embedder,
    finetuned_model: Embedder,
    test_queries: list[tuple[str, str]],  # (query, expected_doc_id)
    index
) -> dict:
    """Compare retrieval quality between models."""

    results = {"base": [], "finetuned": []}

    for query, expected_id in test_queries:
        # Base model retrieval
        base_emb = base_model.embed([query])[0]
        base_results = index.search(base_emb, k=10)
        base_hit = expected_id in [r.id for r in base_results]
        results["base"].append(base_hit)

        # Fine-tuned model retrieval
        ft_emb = finetuned_model.embed([query])[0]
        ft_results = index.search(ft_emb, k=10)
        ft_hit = expected_id in [r.id for r in ft_results]
        results["finetuned"].append(ft_hit)

    return {
        "base_hit_rate": sum(results["base"]) / len(results["base"]),
        "finetuned_hit_rate": sum(results["finetuned"]) / len(results["finetuned"]),
        "improvement": (sum(results["finetuned"]) - sum(results["base"])) / len(results["base"])
    }
```

---

## References

### Embedding Fine-Tuning
- [Phil Schmid: Fine-tune Embedding Model for RAG](https://www.philschmid.de/fine-tune-embedding-model-for-rag)
- [Databricks: Improving RAG with Embedding Finetuning](https://www.databricks.com/blog/improving-retrieval-and-rag-embedding-model-finetuning)
- [LlamaIndex: Fine-Tuning Embeddings for RAG](https://medium.com/llamaindex-blog/fine-tuning-embeddings-for-rag-with-synthetic-data-e534409a3971)
- [Hugging Face: Fine-tune ModernBERT for RAG](https://huggingface.co/blog/sdiazlor/fine-tune-modernbert-for-rag-with-synthetic-data)
- [Redis: Get Better RAG by Fine-tuning Embedding Models](https://redis.io/blog/get-better-rag-by-fine-tuning-embedding-models/)

### LLM Fine-Tuning
- [RAFT Paper (arXiv:2403.10131)](https://arxiv.org/abs/2403.10131)
- [Berkeley RAFT Blog](https://gorilla.cs.berkeley.edu/blogs/9_raft.html)
- [Microsoft: RAFT - A New Way to Teach LLMs](https://techcommunity.microsoft.com/blog/aiplatformblog/raft-a-new-way-to-teach-llms-to-be-better-at-rag/4084674)
- [Sebastian Raschka: Practical Tips for LoRA](https://magazine.sebastianraschka.com/p/practical-tips-for-finetuning-llms)
- [Phil Schmid: Fine-tune LLMs in 2025](https://www.philschmid.de/fine-tune-llms-in-2025)
- [Mercity: Guide to LoRA and QLoRA](https://www.mercity.ai/blog-post/guide-to-fine-tuning-llms-with-lora-and-qlora)

### Reranker Fine-Tuning
- [RAG-Retrieval GitHub](https://github.com/NovaSearch-Team/RAG-Retrieval)
- [Jina: What is ColBERT and Late Interaction](https://jina.ai/news/what-is-colbert-and-late-interaction-and-why-they-matter-in-search/)
- [Answer.AI: Small but Mighty ColBERT](https://www.answer.ai/posts/2024-08-13-small-but-mighty-colbert.html)
- [Galileo: How to Select a Reranking Model](https://galileo.ai/blog/mastering-rag-how-to-select-a-reranking-model)

### Frameworks
- [Unsloth GitHub](https://github.com/unslothai/unsloth)
- [Unsloth Documentation](https://docs.unsloth.ai/)
- [Axolotl Documentation](https://docs.axolotl.ai/)
- [MLX GitHub](https://github.com/ml-explore/mlx)
- [Apple MLX Research](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)
- [Torchtune Documentation](https://pytorch.org/torchtune/)

### Techniques
- [Matryoshka Representation Learning (arXiv:2205.13147)](https://arxiv.org/abs/2205.13147)
- [Hugging Face: Matryoshka Embeddings](https://huggingface.co/blog/matryoshka)
- [NVIDIA: Evaluating RAG with Synthetic Data](https://developer.nvidia.com/blog/evaluating-and-enhancing-rag-pipeline-performance-using-synthetic-data/)
- [SBERT: Unsupervised Learning](https://sbert.net/examples/sentence_transformer/unsupervised_learning/README.html)

### Comparison Articles
- [Spheron: Comparing Axolotl, Unsloth, Torchtune](https://blog.spheron.network/comparing-llm-fine-tuning-frameworks-axolotl-unsloth-and-torchtune-in-2025)
- [Modal: Best Frameworks for Fine-tuning LLMs in 2025](https://modal.com/blog/fine-tuning-llms)
- [Daily Dose of DS: Fine-Tuning or RAG?](https://www.dailydoseofds.com/augmenting-llms-fine-tuning-or-rag/)

---

## Related Documentation

- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Embedding model selection
- [State-of-the-Art Evaluation](./state-of-the-art-evaluation.md) - RAGAS and evaluation
- [State-of-the-Art Local RAG](./state-of-the-art-local-rag.md) - Performance optimisation
- [F-058: Fine-Tuning Pipeline](../features/planned/F-058-fine-tuning-pipeline.md) - Feature specification
- [ADR-0027: Fine-Tuning Strategy](../decisions/adrs/0027-fine-tuning-strategy.md) - Architecture decision

---

**Status:** Research complete
