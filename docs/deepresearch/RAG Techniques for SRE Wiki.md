

# **Enterprise SRE RAG Architecture: Deep Dive, Content Strategy, and Implementation Specifications**

## **Executive Summary**

The architectural requirements for a Site Reliability Engineering (SRE) Wiki differ fundamentally from general-purpose corporate knowledge bases. SRE environments utilize a heterogeneous mix of structured declarative configurations (Terraform, YAML), semi-structured temporal data (system logs, stack traces), and unstructured narrative prose (post-mortem reports, runbooks). Standard "naive" Retrieval-Augmented Generation (RAG) pipelines—typically characterized by fixed-size token chunking and simple cosine similarity retrieval—fail to address the precision, context, and safety requirements of production engineering. A hallucinated command or a misidentified configuration parameter in an SRE context can precipitate catastrophic service outages.

Consequently, this research report outlines an "Enterprise-Grade" architectural standard designed to mitigate these risks. The proposed architecture utilizes a "3-Stage Rocket" retrieval pattern, incorporating Hybrid Search, Cross-Encoder Reranking, and Layout-Aware Hierarchical Context Assembly. Furthermore, it introduces a rigorous Content Type Decision Matrix to govern ingestion strategies for diverse data classes and provides detailed Implementation Specifications for database schemas, specifically tailored for high-performance vector stores like Qdrant, Weaviate, and PostgreSQL with pgvector. This document serves as the authoritative reference for building a technical SRE Wiki that is exhaustive, context-aware, and production-safe.

---

# **Part 1: Technique Deep Dive (technique\_deep\_dive.md)**

## **1.0 The "3-Stage Rocket" Retrieval Architecture**

The prevailing best practice for high-stakes technical retrieval is the "3-Stage Rocket" architecture. This pattern is designed to progressively refine the search space from a broad initial recall to a precise, context-rich injection payload. Unlike simple retrieve-and-generate loops, this multi-stage approach decouples the mechanisms of retrieval (finding the needle) from the mechanisms of generation (threading the needle), ensuring that the Large Language Model (LLM) is grounded in the most accurate available context.

### **1.1 Stage 1: Hybrid Retrieval (The Booster)**

The first stage of the pipeline is responsible for the initial retrieval of a broad candidate set of document chunks. In the domain of software engineering and infrastructure management, relying solely on dense vector search (semantic similarity) is insufficient and often dangerous. Dense embeddings, while excellent at capturing conceptual relationships (e.g., understanding that "pod failure" and "container crash" are related), frequently struggle with the precise lexicographical matching required for technical identifiers.1

For instance, an SRE querying for a specific error code such as 0x80040154 or a specific Kubernetes annotation like nginx.ingress.kubernetes.io/force-ssl-redirect requires exact string matching. A purely semantic search might conflate 0x80040154 with 0x80040155 if their embedding proximity is close due to shared contexts of "memory errors," yet these codes may require vastly different resolution steps.

To address this, the architecture mandates a **Hybrid Search** strategy that combines two distinct indexing mechanisms:

1. **Dense Vector Search:** This component utilizes Hierarchical Navigable Small World (HNSW) indexes to identify conceptually related documents. It excels at handling natural language queries such as "How do I restore the primary database after a region failover?" by mapping the semantic intent of the query to the vector space of the runbooks.2  
2. **Sparse Keyword Search (BM25/SPLADE):** This component functions on an inverted index principle, ensuring that unique tokens—such as variable names, error constants, and specific configuration keys—are weighted heavily. BM25 (Best Matching 25\) calculates scores based on term frequency-inverse document frequency (TF-IDF), ensuring that rare, specific terms in the query drive the retrieval.1

The outputs of these two parallel retrieval streams are normalized and combined, typically using Reciprocal Rank Fusion (RRF) or a weighted sum equation (e.g., $\\alpha \\cdot \\text{DenseScore} \+ (1-\\alpha) \\cdot \\text{SparseScore}$). This fusion produces a raw candidate list of top-$k$ results (typically $k=100$), ensuring that the initial pool contains both conceptually relevant and keyword-exact matches.5

### **1.2 Stage 2: Cross-Encoder Reranking (The Sustainer)**

The candidate list generated in Stage 1 inevitably contains "distractors"—chunks that share high semantic similarity or keyword overlap with the query but lack the specific causal reasoning required to answer the prompt. For example, a query about "database connection timeouts" might return chunks describing "database connection success logs" or "timeout configuration parameters" alongside the actual troubleshooting guide.

Stage 2 employs a **Cross-Encoder** model to filter this noise. Unlike Bi-Encoders used in Stage 1 (which encode the query and document independently to allow for fast vector comparisons), Cross-Encoders process the query and the document simultaneously as a single input pair. This allows the model's self-attention mechanism to deeply analyze the interaction between the query terms and the document content.1

**Table 1: Bi-Encoder vs. Cross-Encoder Performance in Technical Retrieval**

| Feature | Bi-Encoder (Stage 1\) | Cross-Encoder (Stage 2\) | Implications for SRE RAG |
| :---- | :---- | :---- | :---- |
| **Architecture** | Siamese Networks (Independent processing) | Full Self-Attention (Joint processing) | Cross-encoders detect subtle contradictions typical in troubleshooting guides. |
| **Latency** | Low (\< 10ms for similarity search) | High (\~100ms \- 500ms depending on model) | Reranking is computationally expensive; limited to top 50-100 candidates. |
| **Accuracy (NDCG)** | \~0.89 (Dense) / \~0.88 (Sparse) | \~0.93 (Full Pipeline) | The precision gain is critical for avoiding "hallucinated" solutions. |
| **Use Case** | Retrieval from millions of docs | Re-ordering top 50 docs | Essential for distinguishing "Root Cause" from "Symptoms". |
| **Reference** | 1 | 1 |  |

While the Cross-Encoder adds latency (approximately 100ms), empirical benchmarks demonstrate a significant improvement in retrieval quality, boosting Normalized Discounted Cumulative Gain (NDCG@10) scores from 0.91 (HyDE) to 0.93. In an SRE context, this precision is the difference between retrieving a deprecated workaround and the current gold-standard fix.1

### **1.3 Stage 3: Layout-Aware Hierarchical Context Assembly (The Payload)**

The final stage addresses the "fragmentation problem" inherent in standard chunking. Naive splitting approaches (e.g., fixed 512-token windows) often sever the semantic link between a solution and its necessary context. A chunk might contain the instruction "Run drop database," but the prerequisite warning "Only perform this in the staging environment" might be located in the previous chunk, which was not retrieved.

To solve this, the architecture implements the **"Small-to-Big" (Parent Document Retrieval)** pattern.

* **Mechanism:** The system indexes small, granular "child" chunks (e.g., 128–256 tokens) to maximize vector precision. Small chunks represent specific concepts (e.g., a single step in a runbook) and have a tighter vector distribution, making them easier to match against specific user queries.6  
* **Retrieval Strategy:** When a child chunk is identified as a hit, the system does *not* return the child chunk to the LLM. Instead, it utilizes a parent\_id reference stored in the child's metadata to retrieve a larger "parent" window or the full document section. This ensures that the LLM receives the complete context—headings, warnings, and adjacent steps—necessary to generate a safe response.9

## **2.0 Advanced Chunking Topologies**

### **2.1 Layout-Aware Hierarchical Chunking**

Technical documentation is structured hierarchically, not linearly. A document is a tree of sections (H1, H2, H3), not a stream of tokens. **Layout-Aware Chunking** respects this Document Object Model (DOM).

* **Parsing Logic:** Algorithms parse the document structure (Markdown headers, HTML tags) to identify logical boundaries. Instead of splitting purely by character count, the splitter preserves the integrity of sections. For example, an H2 section titled "Disaster Recovery" containing 1500 tokens might be split into smaller child chunks, but each child retains metadata linking it back to the H2 parent.13  
* **Contextual Enrichment:** Advanced implementations, such as Anthropic's "Contextual Retrieval," prepend the hierarchy to the chunk text before embedding. A chunk containing "Restart the service" is transformed to "Disaster Recovery \> Web Tier \> Restart the service" before vectorization. This resolves the ambiguity of generic instructions that could apply to multiple services.15

### **2.2 Semantic Chunking**

For narrative-heavy content like Post-Mortem reports, structural boundaries (headers) may be sparse. **Semantic Chunking** offers a dynamic alternative.

* **Mechanism:** This technique involves calculating the cosine similarity between the embeddings of sequential sentences. When the similarity score drops below a defined threshold, it indicates a shift in topic, triggering a chunk boundary.  
* **Implications:** This ensures that a detailed analysis of a "Database Deadlock" is kept in one chunk, while the subsequent "Network Latency" analysis is separated, even if they are in the same paragraph block. While computationally more expensive during ingestion (requiring an embedding inference for every sentence), it aligns chunk boundaries with semantic transitions rather than arbitrary token limits.13

### **2.3 Agentic Chunking**

Emerging methodologies include **Agentic Chunking**, where an LLM is employed to analyze the text and determine optimal split points based on logical flow and content density.

* **Process:** The LLM acts as a pre-processor, identifying distinct propositions or "atomic facts" within the text. It then groups these propositions into coherent chunks.  
* **Trade-offs:** While potentially the most accurate method for complex legal or technical reasoning, the cost and latency of using an LLM for ingestion at scale (e.g., millions of log lines) make it prohibitive for high-volume data. It is best reserved for high-value, low-volume documents like "Root Cause Analysis" summaries or policy documents.13

## **3.0 Dual-Storage Architecture: Knowledge Graphs and Vectors**

To achieve true "reasoning" capabilities over SRE data, the architecture advocates for a **Dual-Storage** approach that integrates Vector Databases with Knowledge Graphs (GraphRAG).

* **Episodic vs. Semantic Memory:** Drawing parallels to human cognition, the vector store handles "Episodic Memory" (retrieving specific past incidents via similarity), while the Knowledge Graph handles "Semantic Memory" (understanding the fixed relationships between entities, such as Service A \--depends\_on--\> Service B).19  
* **Graph Traversal:** In a complex outage scenario, a vector search might fail to connect a "Database CPU Spike" in Service X with a "Deployment" in Service Y. However, if the Knowledge Graph encodes the dependency that Service Y writes to Service X's database, a graph traversal (Breadth-First Search) can retrieve the deployment event as a potential root cause, even if the textual descriptions are dissimilar. This enhances retrieval diversity and accuracy.21

---

# **Part 2: Wiki Content Strategy (wiki\_content\_strategy.md)**

## **1.0 Introduction**

A robust SRE Wiki comprises disparate data types, each obeying different structural rules. Applying a uniform chunking strategy—such as the industry-standard RecursiveCharacterTextSplitter with 512 tokens—across all data types yields suboptimal results. It fragments code blocks, severs log traces, and dilutes the specificity of error codes. This section defines a rigorous **Content Type Decision Matrix** to govern the ingestion lifecycle of SRE data.

## **2.0 Content Type Decision Matrix**

The following decision matrix creates a taxonomy of SRE data and maps each class to its optimal ingestion configuration.

**Table 2: SRE Wiki Content Ingestion Strategy**

| Data Class | Primary Characteristic | Recommended Chunking Strategy | Optimal Chunk Size (Tokens) | Retrieval Pattern | Rationale & Insight |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Runbooks / SOPs** | Structured, Hierarchical, Procedural | **Layout-Aware / Hierarchical** | Child: 256-512 Parent: 1024-2048 | **Small-to-Big (Parent Document)** | Procedures are unsafe out of context. Matching a child chunk ("Run command X") must retrieve the parent ("Pre-checks for command X") to prevent operational hazards.6 |
| **Terraform / IaC** | Syntactical, Nested, Dependency-heavy | **CodeSplitter / AST-Based** | Variable (Function/Resource block) | **Contextual Window** | Token splitting breaks syntax (e.g., closing braces }). AST splitters (Tree-sitter) respect logical blocks (Resources, Modules), ensuring retrieved code is syntactically valid.23 |
| **System Logs** | Time-series, Unstructured, Repetitive | **Sliding Window** | 512 tokens w/ 20% overlap | **Dense \+ Sparse (Hybrid)** | Logs flow linearly. Overlap prevents severing a stack trace header from its body. Sparse search (BM25) is critical for exact matching of high-entropy error IDs.25 |
| **Post-Mortems** | Narrative, Analysis-heavy, Long-form | **Semantic Chunking** | Dynamic (Sentence/Paragraph) | **Hybrid \+ Rerank** | Root cause narratives benefit from semantic boundaries. Grouping sentences by embedding similarity ensures that a full explanation of a failure mode is captured in one chunk.13 |
| **Stack Traces** | High-entropy, Non-linguistic | **Pattern/Exception Splitter** | Per Stack Frame | **Sparse (BM25) Only** | Dense vectors degrade on hex addresses and variable paths. Keyword matching on Exception Classes (e.g., NullPointerException) and line numbers is far more effective.27 |

## **3.0 Deep Dive: Infrastructure as Code (IaC) Strategy**

Infrastructure as Code (IaC) files, such as Terraform (HCL) or Kubernetes manifests (YAML), present unique challenges. Standard text splitters often sever a resource block from its provider configuration or split a multi-line string in the middle, rendering the snippet useless for generation.

### **3.1 The CodeSplitter & Tree-Sitter Solution**

The strategy mandates the use of **AST-Based Splitting** (Abstract Syntax Tree). Tools like CodeSplitter or custom parsers utilizing tree-sitter-hcl parse the code into its logical components.

* **Logic:** The parser identifies the start and end of a logical block (e.g., a resource "aws\_s3\_bucket" "example" {... }). The entire block is treated as an atomic unit. If the block exceeds the token limit, it is split at the attribute level, never mid-line.  
* **Metadata Enrichment:** A critical insight is that IaC code is often identical across environments (Dev, Staging, Prod), differentiated only by directory path or variable files. The ingestion pipeline must extract this context. A chunk defining an S3 bucket must be enriched with metadata: { "environment": "prod-us-east-1", "module": "networking" }. This allows the LLM to distinguish between a production configuration and a staging sandbox, preventing "environment hallucination".29  
* **Implementation Detail:** Since Terraform AST parsing APIs are not always publicly exposed or stable, robust implementations may require custom tree-sitter bindings or fallback to RecursiveCharacterTextSplitter with HCL-specific separators (e.g., closing braces }).32

## **4.0 Deep Dive: The "Stack Trace" Paradox**

Stack traces represent a high-entropy data class that defies standard vectorization. They are often voluminous, repetitive, and dense with non-natural language tokens (hex codes, memory addresses).

### **4.1 The Summary-Index Pattern**

Embedding a raw 50-line stack trace often dilutes the vector space, making it difficult to match against a natural language query like "Why is the payment service failing?".

* **Solution:** Implement a **"Summary-Index"** pattern.  
  1. **Extraction:** During ingestion, a regex parser extracts the **Exception Type** (e.g., java.net.ConnectException) and the **Top 3 Stack Frames**.  
  2. **Embedding:** Only this summary is embedded into the vector store.  
  3. **Storage:** The full, raw stack trace is stored as a "Parent" document.  
  4. **Retrieval:** The user's query matches the summary (e.g., "connection error"), but the RAG system retrieves the full parent stack trace for the LLM to analyze. This optimizes retrieval precision without sacrificing the detailed data needed for diagnosis.27

## **5.0 Content Lifecycle Management**

SRE documentation suffers from rapid "bit rot." A runbook valid yesterday may be dangerous today if a patch was applied. The content strategy must include active lifecycle management mechanisms.

* **Time-Weighted Reranking:** In Stage 2 (Reranking), the scoring function should include a decay parameter based on the last\_updated metadata timestamp. Documents that are older should receive a penalty in the final ranking, pushing newer solutions to the top.  
* **Rolling Index for Logs:** For high-volume log data, a "Rolling Index" strategy is required. Data older than a defined retention period (e.g., 30 days) should be automatically purged or moved to a "Cold Tier" collection to maintain index performance and relevance. This mirrors standard log aggregation retention policies (e.g., Splunk/ELK) but applied to the vector domain.15

---

# **Part 3: RAG Implementation Specifications (rag\_implementation\_specs.md)**

## **1.0 Introduction**

This section translates the architectural theories into concrete implementation specifications. It details database schema definitions, ingestion pipeline configurations, and the critical post-processing logic required to execute the "Small-to-Big" retrieval pattern. The specifications are designed to be platform-agnostic but provide specific implementation examples for **Qdrant**, **Weaviate**, and **PostgreSQL (pgvector)**.

## **2.0 Database Schema Specifications**

To support the Parent Document Retrieval pattern, the database schema must explicitly model the relationship between the **Search Index (Child)** and the **Content Store (Parent)**.

### **2.1 Logical Data Model**

* **Collection A (Child Nodes):** Contains small, granular chunks (128-512 tokens), high-dimensional dense vectors, sparse vectors (SPLADE/BM25), and Foreign Key references to the Parent.  
* **Collection B (Parent Nodes):** Contains large text blobs (1024-4096 tokens or full files), structural metadata, and original file references.

### **2.2 Vector Store Implementation Examples**

#### **2.2.1 Qdrant / Weaviate JSON Payload Schema (Child Node)**

This schema is optimized for Hybrid Retrieval and Layout-Aware filtering.

JSON

{  
  "id": "uuid-child-chunk-v4",  
  "vector": {  
    "dense": \[0.012, \-0.34,...\],     // 1024-dim dense vector (e.g., text-embedding-3-small)  
    "sparse": {                       // SPLADE or BM25 sparse vector  
      "indices": \[34, 560,...\],  
      "values": \[0.5, 0.8,...\]  
    }  
  },  
  "payload": {  
    "content\_snippet": "restart the kubelet service using systemctl...",  
    "parent\_id": "uuid-parent-doc-v4",  
    "chunk\_index": 42,  
    "source\_file": "runbooks/k8s-recovery.md",  
    "doc\_type": "runbook",  
    "heading\_hierarchy":, // Critical for filtering  
    "tags": \["kubernetes", "critical", "linux"\],  
    "last\_updated": "2024-05-20T14:30:00Z"  
  }  
}

**Insight:** The heading\_hierarchy field enables powerful filtered queries. An SRE can scope a search specifically to "Disaster Recovery" sections, ignoring "Installation" sections, by applying a payload filter on this array.13

#### **2.2.2 PostgreSQL (pgvector) Schema**

For teams leveraging existing relational infrastructure, PostgreSQL with pgvector offers a robust solution.

SQL

\-- Parent Documents Table: Stores the "Big" context  
CREATE TABLE parent\_documents (  
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, \-- BIGINT is preferred over UUID for indexing speed  
    full\_text TEXT NOT NULL,                            \-- The large context window  
    file\_path VARCHAR(255),  
    metadata JSONB,                                     \-- Stores hierarchy, authors, commit\_hash  
    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP  
);

\-- Child Chunks Table: Stores the "Small" search targets  
CREATE TABLE child\_chunks (  
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  
    parent\_id BIGINT REFERENCES parent\_documents(id),  
    embedding VECTOR(1024),                             \-- Dense vector column  
    sparse\_vec VECTOR(20000),                           \-- Sparse vector column (if supported by extension)  
    chunk\_text TEXT,                                    \-- The granular snippet  
    chunk\_index INT                                     \-- Critical for ordering and merging  
);

\-- Indexing for Speed  
CREATE INDEX ON child\_chunks USING hnsw (embedding vector\_cosine\_ops);

**Technical Note:** While UUIDs are standard for distributed systems, using BIGINT for primary keys in Postgres pgvector implementations can offer slight performance advantages in index size and lookup speed for massive datasets. Furthermore, users must be wary of the TOAST (The Oversized-Attribute Storage Technique) mechanism in Postgres; indexing very large text fields directly can lead to performance degradation, reinforcing the need to separate the searchable vector index (Child) from the bulk storage (Parent).38

## **3.0 Ingestion Pipeline Specifications**

### **3.1 Chunking Configuration**

The ingestion pipeline should utilize a hierarchical splitting strategy.

* **Primary Splitter:** MarkdownHeaderTextSplitter (or equivalent Layout-Aware parser) to first break the document into logical sections based on headers.  
* **Secondary Splitter:** RecursiveCharacterTextSplitter to process the content within each header if it exceeds the child chunk size.  
* **Parameter Specification:**  
  * **Child Chunk Size:** **256-512 tokens**. Research benchmarks indicate this is the "sweet spot" for embedding models like e5-small or text-embedding-3-small. It balances semantic completeness with vector precision.40  
  * **Parent Chunk Size:** **1024-2048 tokens** (or the full logical section).  
  * **Overlap:** **10-15% (approx. 50-75 tokens)**. This is mandatory for "Sliding Window" retrieval, ensuring that boundary concepts (e.g., a sentence starting in one chunk and ending in another) are not lost.43

### **3.2 Contextual Retrieval Enhancement (The Anthropic Method)**

To further combat the loss of context in small chunks, the ingestion pipeline should implement **Contextual Retrieval**.

* **Mechanism:** Before embedding a child chunk, prepend the parent's title and hierarchy to the text.  
  * *Original Chunk:* "Run systemctl restart."  
  * *Enriched Chunk for Embedding:* "Context: Runbook for Nginx Load Balancer \> Emergency Restart Procedures. Content: Run systemctl restart."  
* **Result:** The vector representation now encodes "Nginx" and "Emergency," preventing this generic command from matching irrelevant queries about other services.15

## **4.0 Post-Processing Logic: Merging & Windowing**

The raw output from the vector database is a list of disjointed Child chunks. Feeding these directly to an LLM can lead to fragmented and incoherent reasoning. The following post-processing algorithms are strictly required.

### **4.1 Algorithm: Adjacent Chunk Merging**

This algorithm reconstructs a continuous narrative from fragmented hits, mimicking a human reading adjacent paragraphs.

**Pseudocode:**

1. **Input:** ranked\_chunks (List of Top-K Child Chunks from the Reranker).  
2. **Group:** Sort ranked\_chunks by parent\_id, then by chunk\_index.  
3. **Iterate & Merge:**  
   * Initialize merged\_contexts list.  
   * For each chunk in the sorted group:  
     * Check if chunk.parent\_id equals previous\_chunk.parent\_id **AND** chunk.chunk\_index equals previous\_chunk.chunk\_index \+ 1\.  
     * **If True:** This indicates the chunks are immediate neighbors. Concatenate chunk.text to previous\_chunk.text. Update the metadata to reflect the expanded range (e.g., "Lines 10-20" becomes "Lines 10-30").  
     * **If False:** Append the chunk to merged\_contexts as a new, separate entry.  
4. **Threshold Check:** If a merged entry consists of more than $N$ consecutive child chunks (e.g., $N \> 3$), trigger a fetch for the full parent\_document text instead, as the user likely needs the entire section.45

### **4.2 Algorithm: Contextual Window Expansion (Sliding Window)**

For data types like Logs and IaC, retrieving a single chunk is rarely sufficient. The system must expand the window to include neighbors, even if they didn't vector-match the query.

**Logic:**

1. **Input:** A high-scoring hit chunk (e.g., chunk\_index: 42, parent\_id: XYZ).  
2. **Expansion:** Automatically calculate the indices of the preceding and succeeding chunks: \[42-1, 42, 42+1\].  
3. **Query:** Execute a secondary key-value lookup to fetch chunks 41 and 43 from the child\_chunks collection.  
4. **Concatenation:** Return the concatenated string Text(41) \+ Text(42) \+ Text(43).  
5. **Benefit:** This ensures that if the vector match hit the middle of a stack trace, the LLM also sees the "caused by" header (Chunk 41\) and the subsequent error details (Chunk 43), providing a complete diagnostic view.6

## **5.0 Deduplication Strategy**

Duplicate content poisons retrieval results, wasting context tokens on repetitive information (e.g., identical license headers in every Terraform file).

* **Ingestion-Time Deduplication:** Implement hashing (e.g., MD5 or SimHash) on the *content* of each chunk before indexing. If the hash exists, map the new document metadata to the existing chunk ID rather than creating a new vector.  
* **Retrieval-Time Deduplication:** If multiple child chunks point to the same parent\_id, the system should collapse them. Instead of retrieving Parent Doc A three times (triggered by Child 1, Child 2, and Child 5), retrieve it once. This effectively "packs" the context window with diverse sources rather than repetitive redundancy.22

## **6.0 Evaluation and Benchmarking**

To validate the efficacy of this architecture, continuous evaluation using frameworks like **Ragas** or **ARES** is recommended.

* **Metrics:** Focus on **Faithfulness** (Did the answer come from the context?) and **Answer Relevance** (Did it answer the SRE's question?).  
* **Benchmarks:** Recent studies indicate that while page-level chunking (splitting by physical page) performs well for general data, the hierarchical/section-based chunking described here outperforms it for structured technical queries. Furthermore, embedding model benchmarks suggest that text-embedding-3-small at 512 dimensions is a highly efficient "sweet spot" for production RAG, balancing cost and accuracy.18

By adhering to these specifications, the SRE Wiki will evolve from a passive document store into an active, context-aware engine capable of supporting complex engineering operations with high reliability.

#### **Works cited**

1. ⚡ Dense vs Sparse vs Hybrid RRF: Which RAG Technique Actually Works? | by Robert Dennyson | Nov, 2025 | Medium, accessed November 18, 2025, [https://medium.com/@robertdennyson/dense-vs-sparse-vs-hybrid-rrf-which-rag-technique-actually-works-1228c0ae3f69](https://medium.com/@robertdennyson/dense-vs-sparse-vs-hybrid-rrf-which-rag-technique-actually-works-1228c0ae3f69)  
2. Beyond Retrieval: Ensembling Cross-Encoders and GPT Rerankers with LLMs for Biomedical QA \- arXiv, accessed November 18, 2025, [https://arxiv.org/html/2507.05577v1](https://arxiv.org/html/2507.05577v1)  
3. What Is Weaviate? A Semantic Search Database \- Oracle, accessed November 18, 2025, [https://www.oracle.com/database/vector-database/weaviate/](https://www.oracle.com/database/vector-database/weaviate/)  
4. Cheatsheet for Production-Ready Advanced RAG — The Cloud Girl, accessed November 18, 2025, [https://www.thecloudgirl.dev/blog/this-is-your-playbook-for-production-readynbsp-advanced-rag](https://www.thecloudgirl.dev/blog/this-is-your-playbook-for-production-readynbsp-advanced-rag)  
5. Best Chunking Strategy for the Medical RAG System (Guidelines Docs) in PDFs \- Reddit, accessed November 18, 2025, [https://www.reddit.com/r/Rag/comments/1ljhksy/best\_chunking\_strategy\_for\_the\_medical\_rag\_system/](https://www.reddit.com/r/Rag/comments/1ljhksy/best_chunking_strategy_for_the_medical_rag_system/)  
6. Advanced Retrieval Techniques In RAG | by Prince Krampah, accessed November 18, 2025, [https://ai.gopubby.com/advance-retrieval-techniques-in-rag-5fdda9cc304b](https://ai.gopubby.com/advance-retrieval-techniques-in-rag-5fdda9cc304b)  
7. Rerankers and Two-Stage Retrieval \- Pinecone, accessed November 18, 2025, [https://www.pinecone.io/learn/series/rag/rerankers/](https://www.pinecone.io/learn/series/rag/rerankers/)  
8. Elastic Rerank | Elastic Docs, accessed November 18, 2025, [https://www.elastic.co/docs/explore-analyze/machine-learning/nlp/ml-nlp-rerank](https://www.elastic.co/docs/explore-analyze/machine-learning/nlp/ml-nlp-rerank)  
9. Data Engineering for Advanced RAG: Small-to-Big with Pinecone, LangChain, and Datavolo, accessed November 18, 2025, [https://datavolo.io/2024/03/data-engineering-for-advanced-rag-small-to-big-with-pinecone-langchain-and-datavolo/](https://datavolo.io/2024/03/data-engineering-for-advanced-rag-small-to-big-with-pinecone-langchain-and-datavolo/)  
10. 3\. Improving Retrieval Processes, accessed November 18, 2025, [https://abc-notes.data.tech.gov.sg/notes/topic-5-advanced-rag/3.-improving-retrieval-processes.html](https://abc-notes.data.tech.gov.sg/notes/topic-5-advanced-rag/3.-improving-retrieval-processes.html)  
11. Vector Search retrieval quality guide \- Azure Databricks \- Microsoft Learn, accessed November 18, 2025, [https://learn.microsoft.com/en-us/azure/databricks/vector-search/vector-search-retrieval-quality](https://learn.microsoft.com/en-us/azure/databricks/vector-search/vector-search-retrieval-quality)  
12. \[FEAT\]: Add Optional Small-to-Big Retrieval · Issue \#1387 · Mintplex-Labs/anything-llm, accessed November 18, 2025, [https://github.com/Mintplex-Labs/anything-llm/issues/1387](https://github.com/Mintplex-Labs/anything-llm/issues/1387)  
13. Implement RAG chunking strategies with LangChain and watsonx.ai \- IBM, accessed November 18, 2025, [https://www.ibm.com/think/tutorials/chunking-strategies-for-rag-with-langchain-watsonx-ai](https://www.ibm.com/think/tutorials/chunking-strategies-for-rag-with-langchain-watsonx-ai)  
14. Advanced RAG: Layout Aware and multi-document RAG. Part 1 : Layout aware parsing and chunking of documents | by Viraj Kadam, accessed November 18, 2025, [https://viraajkadam.medium.com/advanced-rag-layout-aware-and-multi-document-rag-f45cb0d5838d](https://viraajkadam.medium.com/advanced-rag-layout-aware-and-multi-document-rag-f45cb0d5838d)  
15. Contextual Retrieval in AI Systems \- Anthropic, accessed November 18, 2025, [https://www.anthropic.com/news/contextual-retrieval](https://www.anthropic.com/news/contextual-retrieval)  
16. RAG Chunking Strategies: Complete Guide to Document Splitting for Better Retrieval, accessed November 18, 2025, [https://latenode.com/blog/ai-frameworks-technical-infrastructure/rag-retrieval-augmented-generation/rag-chunking-strategies-complete-guide-to-document-splitting-for-better-retrieval](https://latenode.com/blog/ai-frameworks-technical-infrastructure/rag-retrieval-augmented-generation/rag-chunking-strategies-complete-guide-to-document-splitting-for-better-retrieval)  
17. Chunking Strategies to Improve Your RAG Performance \- Weaviate, accessed November 18, 2025, [https://weaviate.io/blog/chunking-strategies-for-rag](https://weaviate.io/blog/chunking-strategies-for-rag)  
18. Best Chunking Strategies for RAG in 2025 \- Firecrawl, accessed November 18, 2025, [https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)  
19. Zep: A Temporal Knowledge Graph Architecture for Agent Memory \- arXiv, accessed November 18, 2025, [https://arxiv.org/html/2501.13956v1](https://arxiv.org/html/2501.13956v1)  
20. ZEP:ATEMPORAL KNOWLEDGE GRAPH ARCHITECTURE FOR AGENT MEMORY, accessed November 18, 2025, [https://blog.getzep.com/content/files/2025/01/ZEP\_\_USING\_KNOWLEDGE\_GRAPHS\_TO\_POWER\_LLM\_AGENT\_MEMORY\_2025011700.pdf](https://blog.getzep.com/content/files/2025/01/ZEP__USING_KNOWLEDGE_GRAPHS_TO_POWER_LLM_AGENT_MEMORY_2025011700.pdf)  
21. AcademicRAG: Knowledge Graph Enhanced Retrieval-Augmented Generation for Academic Resource Discovery \- kth .diva, accessed November 18, 2025, [https://kth.diva-portal.org/smash/get/diva2:1971383/FULLTEXT01.pdf](https://kth.diva-portal.org/smash/get/diva2:1971383/FULLTEXT01.pdf)  
22. GraphRAG Field Guide: Navigating the World of Advanced RAG Patterns \- Neo4j, accessed November 18, 2025, [https://neo4j.com/blog/developer/graphrag-field-guide-rag-patterns/](https://neo4j.com/blog/developer/graphrag-field-guide-rag-patterns/)  
23. Node Parser Modules | LlamaIndex Python Documentation, accessed November 18, 2025, [https://developers.llamaindex.ai/python/framework/module\_guides/loading/node\_parsers/modules/](https://developers.llamaindex.ai/python/framework/module_guides/loading/node_parsers/modules/)  
24. tianyang/repobench\_python\_v1.1 · Datasets at Hugging Face, accessed November 18, 2025, [https://huggingface.co/datasets/tianyang/repobench\_python\_v1.1/viewer/default/cross\_file\_first?p=2](https://huggingface.co/datasets/tianyang/repobench_python_v1.1/viewer/default/cross_file_first?p=2)  
25. Chunking Strategies for AI and RAG Applications \- DataCamp, accessed November 18, 2025, [https://www.datacamp.com/blog/chunking-strategies](https://www.datacamp.com/blog/chunking-strategies)  
26. Sliding Window in RAG: Step-by-Step Guide | newline \- Fullstack.io, accessed November 18, 2025, [https://www.newline.co/@zaoyang/sliding-window-in-rag-step-by-step-guide--c4c786c6](https://www.newline.co/@zaoyang/sliding-window-in-rag-step-by-step-guide--c4c786c6)  
27. Resolve Agent: A Technical Approach to Revolutionizing Troubleshooting With AI \- Boomi, accessed November 18, 2025, [https://boomi.com/blog/boomi-resolve-agent-ai/](https://boomi.com/blog/boomi-resolve-agent-ai/)  
28. Retrieval-Augmented Test Generation: How Far Are We? \- arXiv, accessed November 18, 2025, [https://arxiv.org/html/2409.12682v1](https://arxiv.org/html/2409.12682v1)  
29. Develop a RAG Solution \- Chunking Phase \- Azure Architecture Center | Microsoft Learn, accessed November 18, 2025, [https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-chunking-phase](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-chunking-phase)  
30. Optimizing RAG Context: Chunking and Summarization for Technical Docs, accessed November 18, 2025, [https://dev.to/oleh-halytskyi/optimizing-rag-context-chunking-and-summarization-for-technical-docs-3pel](https://dev.to/oleh-halytskyi/optimizing-rag-context-chunking-and-summarization-for-technical-docs-3pel)  
31. \[Bug\]: CodeSplitter takes exactly 1 argument (2 given) · Issue \#13521 · run-llama/llama\_index \- GitHub, accessed November 18, 2025, [https://github.com/run-llama/llama\_index/issues/13521](https://github.com/run-llama/llama_index/issues/13521)  
32. How to Extract AST \- Terraform \- HashiCorp Discuss, accessed November 18, 2025, [https://discuss.hashicorp.com/t/how-to-extract-ast/50719](https://discuss.hashicorp.com/t/how-to-extract-ast/50719)  
33. tree-sitter-terraform \- LuaRocks, accessed November 18, 2025, [https://luarocks.org/modules/neorocks/tree-sitter-terraform](https://luarocks.org/modules/neorocks/tree-sitter-terraform)  
34. Smarter Regression Testing with LLMs and RAG (No “Agent Army” Required). \- Medium, accessed November 18, 2025, [https://medium.com/@yurii.pushkarenko/smarter-regression-testing-with-llms-and-rag-no-agent-army-required-72dc40219cdc](https://medium.com/@yurii.pushkarenko/smarter-regression-testing-with-llms-and-rag-no-agent-army-required-72dc40219cdc)  
35. 5 Chunking Strategies for RAG: Optimize Your Retrieval-Augmented Generation Pipeline, accessed November 18, 2025, [https://www.reddit.com/r/NextGenAITool/comments/1o3p5xv/5\_chunking\_strategies\_for\_rag\_optimize\_your/](https://www.reddit.com/r/NextGenAITool/comments/1o3p5xv/5_chunking_strategies_for_rag_optimize_your/)  
36. n8n Docs | PDF | Software Engineering \- Scribd, accessed November 18, 2025, [https://www.scribd.com/document/899126385/n8n-docs](https://www.scribd.com/document/899126385/n8n-docs)  
37. lvwerra/codeparrot-valid · Datasets at Hugging Face, accessed November 18, 2025, [https://huggingface.co/datasets/lvwerra/codeparrot-valid/viewer/default/train](https://huggingface.co/datasets/lvwerra/codeparrot-valid/viewer/default/train)  
38. The Beauty of Parent-Child Chunking. Graph RAG Was Too Slow for Production, So This Parent-Child RAG System was useful \- Reddit, accessed November 18, 2025, [https://www.reddit.com/r/Rag/comments/1mtcvs7/the\_beauty\_of\_parentchild\_chunking\_graph\_rag\_was/](https://www.reddit.com/r/Rag/comments/1mtcvs7/the_beauty_of_parentchild_chunking_graph_rag_was/)  
39. Storing and querying vector data in Postgres with pgvector \- pganalyze, accessed November 18, 2025, [https://pganalyze.com/blog/5mins-postgres-vectors-pgvector](https://pganalyze.com/blog/5mins-postgres-vectors-pgvector)  
40. Benchmark of 11 Best Open Source Embedding Models for RAG \- Research AIMultiple, accessed November 18, 2025, [https://research.aimultiple.com/open-source-embedding-models/](https://research.aimultiple.com/open-source-embedding-models/)  
41. Mastering RAG: Advanced Chunking Strategies for Vector Databases \- Medium, accessed November 18, 2025, [https://medium.com/@subhashbs36/mastering-rag-advanced-chunking-strategies-for-vector-databases-b6e2cbb042d3](https://medium.com/@subhashbs36/mastering-rag-advanced-chunking-strategies-for-vector-databases-b6e2cbb042d3)  
42. Finding the Best Chunking Strategy for Accurate AI Responses | NVIDIA Technical Blog, accessed November 18, 2025, [https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/](https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/)  
43. accessed November 18, 2025, [https://contenteratechspace.com/chunking-techniques-in-retrieval-augmented-generation-rag-systems/\#:\~:text=Include%20a%20small%20overlap%20(e.g.,prompt%20to%20avoid%20repeating%20information.](https://contenteratechspace.com/chunking-techniques-in-retrieval-augmented-generation-rag-systems/#:~:text=Include%20a%20small%20overlap%20\(e.g.,prompt%20to%20avoid%20repeating%20information.)  
44. RAG: Part 2: Chunking. The information is endless, and we have… | by Mehul Jain | Medium, accessed November 18, 2025, [https://medium.com/@j13mehul/rag-part-2-chunking-8b68006eefc1](https://medium.com/@j13mehul/rag-part-2-chunking-8b68006eefc1)  
45. Context-Aware Hierarchical Merging for Long Document Summarization \- arXiv, accessed November 18, 2025, [https://arxiv.org/html/2502.00977v1](https://arxiv.org/html/2502.00977v1)  
46. Activity Detection in Untrimmed Videos Using Chunk-based Classifiers \- CVF Open Access, accessed November 18, 2025, [https://openaccess.thecvf.com/content\_WACVW\_2020/papers/w5/Gleason\_Activity\_Detection\_in\_Untrimmed\_Videos\_Using\_Chunk-based\_Classifiers\_WACVW\_2020\_paper.pdf](https://openaccess.thecvf.com/content_WACVW_2020/papers/w5/Gleason_Activity_Detection_in_Untrimmed_Videos_Using_Chunk-based_Classifiers_WACVW_2020_paper.pdf)  
47. Chunking Strategies for LLM Applications \- Pinecone, accessed November 18, 2025, [https://www.pinecone.io/learn/chunking-strategies/](https://www.pinecone.io/learn/chunking-strategies/)  
48. The Ultimate Guide on Retrieval Strategies — RAG (part-4) | by Prashant Sai \- Medium, accessed November 18, 2025, [https://prasanth-product.medium.com/the-ultimate-guide-on-retrieval-strategies-rag-part-4-6cedce09a4c4](https://prasanth-product.medium.com/the-ultimate-guide-on-retrieval-strategies-rag-part-4-6cedce09a4c4)  
49. Data × LLM: From Principles to Practices \- arXiv, accessed November 18, 2025, [https://arxiv.org/html/2505.18458v2](https://arxiv.org/html/2505.18458v2)  
50. text-embedding-3-small: High-Quality Embeddings at Scale \- PromptLayer Blog, accessed November 18, 2025, [https://blog.promptlayer.com/text-embedding-3-small-high-quality-embeddings-at-scale/](https://blog.promptlayer.com/text-embedding-3-small-high-quality-embeddings-at-scale/)