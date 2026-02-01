# Worldview & Belief Extraction: Comprehensive Research Summary

**Research Date:** February 2026
**Focus:** Frameworks, theories, and computational practices for extracting worldviews, beliefs, and intellectual patterns

---

## 1. ACADEMIC & THEORETICAL FRAMEWORKS

### 1.1 Philosophical Foundations: Epistemology, Ontology, Axiology

**Core Tripartite Model:**
- **Ontology**: The study of being—what actually exists in the world
- **Epistemology**: The study of knowledge—how knowledge is produced, validated, and the limits of knowing
- **Axiology**: The study of values—what matters, what should be pursued, ethical foundations

**Why This Matters for Belief Extraction:**
A person's worldview is fundamentally a coherent framework built on these three pillars. Research shows that individuals operate from:
1. **Ontological commitments** (what exists: material, spiritual, relational, abstract)
2. **Epistemological assumptions** (how we know: empirical, rational, intuitive, contextual)
3. **Axiological stances** (what matters: freedom, security, truth, harmony, innovation)

**Research Paradigms (2024-2025):**
- **Pragmatist** approaches recognize that truth is evolving and context-dependent, emphasizing real-world problem-solving over abstract correctness
- **Relativist ontology + Constructivist epistemology** → Qualitative, interpretivist research; emphasis on participant meanings and rich context
- **Realist ontology + Empiricist epistemology** → Quantitative, positivist research; emphasis on objective measurement

**References:**
- [A guide to ontology, epistemology, and philosophical perspectives for interdisciplinary researchers](https://i2insights.org/2017/05/02/philosophy-for-interdisciplinarity/)
- [Navigating Ontology, Epistemology, and Axiology in Research](https://nsuworks.nova.edu/cgi/viewcontent.cgi?article=7632&context=tqr)
- [Components of a Worldview – Ontology, Epistemology & Linguistics](https://jessicaptomey.com/2012/08/10/conceptualizing-worldview-ontology-epistemology-linguistics/)

---

### 1.2 Psychological Models

#### Big Five Personality (OCEAN)
- **Scientific consensus** in personality psychology
- Measures traits on **continua** (not categorical)
- **Big Five factors:**
  1. Openness to Experience (intellectual curiosity, preference for novelty)
  2. Conscientiousness (organization, discipline, planning orientation)
  3. Extraversion (social engagement, energy, dominance)
  4. Agreeableness (cooperation, empathy, conflict avoidance)
  5. Neuroticism (emotional reactivity, anxiety, stress sensitivity)

**Limitation:** Big Five captures personality traits but not specific beliefs, worldview content, or ideological commitments.

#### MBTI & Type Theories (Limitations)
- **Type-based** (discrete categories) vs. Big Five's **trait-based** (continua) approach
- MBTI lacks strong empirical support compared to Big Five
- Useful for cognitive preference patterns but not directly for belief extraction

#### Personal Construct Theory (George Kelly)
- **Core idea:** People are scientists who construct theories about their world through personal constructs
- **Key mechanism:** Individuals organize experience through bipolar dimensions (constructs)
- **Application:** Can extract belief systems by identifying how someone categorizes experience
- **Methods:** Repertory Grid Technique (Rep Grid) to uncover personal constructs
- **Advantage:** Captures individual-specific meaning systems, not pre-defined categories

**References:**
- [Big Five Personality Traits: The 5-Factor Model](https://www.simplypsychology.org/big-five-personality.html)
- [Myers-Briggs vs. OCEAN: Industrial Psychologist Comparison](https://www.interviewaceapp.com/blog/myers-briggs-vs-ocean-an-industrial-psychologist-breaks-down-the-differences/)
- [5 Leading Alternatives to Big Five](https://www.teamdynamics.io/blog/5-leading-alternatives-to-big-five-top-workplace-personality-tests/)

---

### 1.3 Narrative Analysis & Discourse Analysis

#### Narrative Analysis
**Core Principle:** People construct meaning through narrative. A person's worldview is partly revealed through:
- What stories they tell about themselves
- How they construct causality (agency vs. external forces)
- Which actors are heroes/villains
- Implicit values embedded in plot structure

**Key Concepts:**
- **Narrative elements:** Agents (who acts), Goals (what they pursue), Plans (how they'll achieve it), Beliefs (what they assume)
- **Theory-of-mind interpretation:** Narrative discourse relations focus on agentive characters, goals, plans, beliefs, and temporal structure
- **Graph-based extraction:** Abstract Meaning Representation (AMR) can extract narrative structure as semantic graphs

**References:**
- [Modeling Narrative Discourse (David K. Elson, Columbia)](http://www.cs.columbia.edu/~delson/pubs/Modeling-Narrative-Discourse_Elson_R4.pdf)
- [Extracting narrative signals from public discourse: a network-based approach](https://www.nature.com/articles/s41599-025-06017-x)

#### Critical Discourse Analysis (CDA)
**Core Principle:** Language is never neutral—it reveals and reproduces power structures and ideologies.

**Approach:**
- Examine linguistic structures for signs of:
  - **Authority claims** (who is positioned as knowledgeable?)
  - **Agency patterns** (who acts, who is acted upon?)
  - **Modality** (certainty vs. hedging language)
  - **Nominalization** (who is responsible for actions?)
  - **Lexical choices** (positive/negative framing)

**Why Valuable:** CDA uncovers implicit ideological commitments that direct analysis doesn't reveal.

**References:**
- [Combining Critical Discourse Analysis and NLP tools](https://www.researchgate.net/publication/263167821_Combining_Critical_Discourse_Analysis_and_NLP_tools_in_investigations_of_religious_prose)
- [Discourse Analysis in NLP](https://aclanthology.org/P19-4003/)

#### Concept Mapping
**Method:** Represent beliefs as networks where:
- **Nodes** = concepts (ideas, entities, values)
- **Edges** = relationships (contradicts, supports, causes, exemplifies)
- **Density/structure** reveals coherence of belief system

**Application:** Can expose tensions, gaps, and central beliefs through graph analysis.

---

### 1.4 Abstract Meaning Representation (AMR)

**What It Is:**
- A graph formalism representing sentence meaning as rooted, directed acyclic graphs
- **Nodes** = concepts
- **Edges** = semantic relationships
- Abstracts away from surface syntax to capture deep meaning

**Why Valuable for Belief Extraction:**
- Can systematically extract who believes what (semantic roles: :ARG0, :ARG1)
- Identifies modality (possibility, necessity, negation)
- Captures complex nested beliefs ("I think that X believes Y because Z")

**Example Applications:**
- Extract belief propositions as AMR graphs
- Compare AMR structures to identify conceptual overlaps
- Detect negations and qualifications of claims

**References:**
- [Survey of Abstract Meaning Representation: Then, Now, Future](https://arxiv.org/html/2505.03229v1)
- [AMR Bibliography (comprehensive resource)](https://nert-nlp.github.io/AMR-Bibliography/)

---

## 2. COMPUTATIONAL APPROACHES FOR BELIEF EXTRACTION

### 2.1 Sentiment Analysis & Opinion Mining

**Core Tasks:**
1. **Sentiment classification** (positive/negative/neutral across targets)
2. **Aspect-based analysis** (what specific aspects does person have opinions about?)
3. **Opinion holder identification** (who holds which opinions?)
4. **Opinion target identification** (what are opinions about?)
5. **Opinion expression extraction** (which phrases convey opinions?)

**Key Linguistic Phenomena:**
- **Negation** ("I don't like X" reverses polarity)
- **Modality** (possibility, necessity, doubt)
- **Comparison** (implicit standards/values)
- **Intensifiers/Hedges** (really, sort of, arguably)

**Why Limited for Full Worldview Extraction:**
Sentiment analysis captures emotional orientation but not deeper philosophical commitments, causal theories, or value hierarchies.

**References:**
- [Sentiment Analysis: Mining Opinions, Sentiments, and Emotions](https://direct.mit.edu/coli/article/42/3/595/1534/Sentiment-Analysis-Mining-Opinions-Sentiments-and)
- [Sentiment Analysis and Opinion Mining (Bing Liu)](https://www.cs.uic.edu/~liub/FBS/SentimentAnalysis-and-OpinionMining.pdf)

---

### 2.2 Stance Detection & Contrarian Identification

**Stance Detection (2024 Advances):**
- **Definition:** Identify author's position (FOR, AGAINST, NEUTRAL) toward a target
- **Multi-modal approaches:** Combine text and image embeddings
- **Unsupervised methods:** Graph neural networks on embedding representations
- **Contextual enhancement:** User's ego-network improves accuracy; helps generalize across populations/time

**Contrarian & Outlier Detection:**
- **Distinctiveness scoring:** High distinctiveness (minority status) makes opinions more salient, influential
- **Optimal Distinctiveness Theory:** Groups are attractive when they maximize distinctiveness (optimal balance of similarity to group AND differentiation from outgroups)
- **Viewpoint diversity metrics:** Ranking fairness metrics evaluate whether search results represent diverse perspectives

**How to Detect Contrarian Beliefs:**
1. **Frequency-based**: Terms appearing in one person's text but rarely in peer group
2. **Embedding-based**: Semantic distance from group centroids
3. **Network-based**: Opinions that create disagreement/tension in interaction networks
4. **Distinctiveness-weighted**: Minority positions that stand out yet are coherent

**References:**
- [Survey of Stance Detection on Social Media: New Directions (2024)](https://arxiv.org/abs/2409.15690)
- [Unsupervised stance detection for social media](https://aclanthology.org/2024.eacl-long.107/)
- [Multi-modal Stance Detection (2024)](https://aclanthology.org/2024.findings-acl.736/)
- [Nonconformity Defines the Self: Minority Opinion Status](https://journals.sagepub.com/doi/10.1177/0146167209358075)
- [Optimal Distinctiveness Theory](https://www.sciencedirect.com/science/article/abs/pii/S0065260110430026)

---

### 2.3 Argument Mining

**What It Extracts:**
1. **Argument components**: Claims (main assertions), Premises (supporting reasons)
2. **Argument relationships**: Support (strengthens), Attack (weakens)
3. **Inference structure**: How beliefs logically connect

**Key Tasks:**
- Argument Component Identification (ACI): Find where arguments are in text
- Relationship Identification (RI): Determine support/attack relationships
- Argument mining for controversial topics: Extract alternative viewpoints on contested issues

**Connection to Worldview:**
Argument structures reveal:
- What someone considers evidence
- What premises they take as foundational (not needing proof)
- Which conclusions they prioritize
- Logical gaps or inconsistencies in belief systems

**References:**
- [Argument Mining: A Survey](https://direct.mit.edu/coli/article/45/4/765/93362/Argument-Mining-A-Survey)
- [Five Years of Argument Mining: Data-Driven Analysis](https://www.ijcai.org/proceedings/2018/0766.pdf)
- [Unveiling Global Discourse Structures: NLP Applications in Argument Mining](https://arxiv.org/html/2502.08371v1)

---

### 2.4 Named Entity Recognition (NER) & Knowledge Graphs

**NER for Belief Extraction:**
- Extract **people** mentioned (influences, allies, rivals)
- Extract **organizations** (institutions person trusts/critiques)
- Extract **locations** (geographic focus, belonging)
- Extract **concepts** (abstract entities: democracy, authenticity, wealth)

**Domain-Specific Entities:**
Recent approaches (GliNER, REBEL) allow extraction of **custom entity types** without retraining—critical for capturing domain-specific beliefs.

**Knowledge Graph Construction:**
1. Extract entities and relationships
2. Build graph: Nodes = entities/concepts, Edges = relationships
3. Analyze structure:
   - **Centrality**: Core concepts vs. periphery
   - **Density**: How interconnected are beliefs?
   - **Paths**: How do ideas lead to conclusions?

**References:**
- [Building Knowledge Graphs (End-to-End Guide, 2026)](https://medium.com/@brian-curry-research/building-a-knowledge-graph-a-comprehensive-end-to-end-guide-using-modern-tools-e06fe8f3b368)
- [Entity Linking and Relationship Extraction with Relik](https://neo4j.com/blog/developer/entity-linking-relationship-extraction-relik-llamaindex/)

---

### 2.5 Topic Modeling & Semantic Clustering

#### Latent Dirichlet Allocation (LDA)
**How It Works:**
- Treats each document as mixture of topics
- Each topic as mixture of words
- Bayesian inference finds underlying topics

**For Worldview Extraction:**
- Quickly identify major themes across large corpus
- Weak on capturing WHY someone believes something
- Strong on identifying WHAT topics matter most

#### Modern Semantic-Driven Approaches (2024+)
**Superior method combining:**
1. **Transformer embeddings** (Sentence-BERT captures semantic similarity)
2. **Dimensionality reduction** (UMAP preserves semantic structure)
3. **Clustering** (HDBSCAN finds natural groups)
4. **Topic refinement** (extract representative terms per cluster)

**Advantages:**
- Captures semantic meaning, not just word co-occurrence
- Handles rare topics better
- Produces coherent, interpretable clusters
- Can filter noise/outliers

**For Weave:**
This approach excels at discovering **conceptual themes** (groups of semantically related ideas), which is prerequisite for identifying worldview points.

**References:**
- [Latent Dirichlet Allocation: LDA Survey](https://www.ccs.neu.edu/home/vip/teach/DMcourse/5_topicmodel_summ/LDA_TM/LDA_survey_1711.04305.pdf)
- [Semantic-LDA](https://dl.acm.org/doi/10.1145/3639409)
- [Semantic-Driven Topic Modeling for Analyzing Creativity](https://arxiv.org/html/2509.16835)

---

### 2.6 Deception Detection via Linguistic Markers

**Linguistic Markers of Truthfulness:**
- **Certainty markers** ("always," "never") indicate truth
- **Higher word/character count** in truthful statements
- **Longer average word length** in falsehoods
- **Pronoun use**: Liars use fewer first-person pronouns (distance)
- **Sensory descriptions**: Excessive detail can signal fabrication
- **Verifiable assertions**: Truth-tellers mention details that can be checked

**Key Frameworks:**
- **Reality Monitoring**: Truthful memories have more perceptual details, contextual info
- **Linguistic Style Matching**: Degree to which speaker's language matches listener indicates truth
- **Cognitive Load**: Lying requires more cognitive effort, reflected in language simplification

**Computational Approach:**
- **LIWC (Linguistic Inquiry & Word Count)**: Gold standard tool with 100+ psycholinguistic dictionaries
- **Modern approach**: BERT embeddings + supervised learning outperforms naïve/expert judges significantly

**Key Insight for Worldview Extraction:**
Not every strongly-held position is "deceptive," but linguistic markers can flag **inconsistencies** between stated beliefs and demonstrated behavior.

**References:**
- [Acoustic-Prosodic and Lexical Cues to Deception](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00311/43547/Acoustic-Prosodic-and-Lexical-Cues-to-Deception)
- [Verbal Lie Detection Using LLMs](https://www.nature.com/articles/s41598-023-50214-0)
- [Detecting Deception Through Linguistic Cues (2025)](https://journals.sagepub.com/doi/10.1177/0261927X251316883)

---

### 2.7 Disagreement & Perspective Modeling

**Perspectivist Approaches (2025 Innovation):**

**Core Idea:** Annotator/speaker disagreement isn't noise—it's signal of genuine perspective differences.

**Modeling Approach:**
- Treat disagreement as **interaction between item and annotator embeddings**
- Each annotator has a perspective embedding that shapes their interpretation
- Disagreement becomes systematic, measurable feature

**Applications:**
1. Identify which topics generate disagreement (contentious vs. consensus)
2. Cluster perspectives: Which interpretations co-occur in same people?
3. Understand subgroup differences: How do groups systematically interpret differently?

**Why Valuable:**
Worldview differences often manifest as **interpretive disagreement**—same facts, different conclusions. This framework directly captures that.

**References:**
- [Beyond Consensus: Perspectivist Modeling of Annotator Disagreement](https://arxiv.org/html/2601.09065)
- [Agree to Disagree: Improving Disagreement Detection with Dual GRUs](https://www.researchgate.net/publication/319186878_Agree_to_Disagree_Improving_Disagreement_Detection_with_Dual_GRUs)

---

## 3. SPECIFIC ANALYSIS TYPES: DETAILED METHODS

### 3.1 "Demonstrated Interests" - Definition & Metrics

**What It Means:**
Interests explicitly shown through:
- Frequent discussion of specific topics
- Detailed knowledge demonstrated
- Return to same themes across time/contexts
- Critique or advocacy directed at specific areas

**Extraction Methods:**

1. **Frequency Analysis:**
   - TF-IDF: How distinctive is this term to this person vs. peer group?
   - Raw frequency: How often does topic appear?
   - Weighted frequency: Longer discussions weighted higher?

2. **Coherence Analysis:**
   - Does person develop ideas systematically (books, series)?
   - Do they cite themselves, build on previous work?
   - Is discussion amateur/casual or expert/detailed?

3. **Engagement Metrics:**
   - Time spent on topic in transcripts (paragraph count)
   - Emotional intensity (LIWC affect scores)
   - Elaboration depth (sentences per mention)

**Metrics to Track:**
- **Salience**: Rank topics by TF-IDF × elaboration depth
- **Persistence**: Does interest appear across multiple time periods?
- **Evolution**: Has treatment deepened, changed, or remained static?

---

### 3.2 "Lying Detection" - Beyond Tone

**Direct Approaches:**
1. **Linguistic Inconsistency Flagging:**
   - Compare stated beliefs across different time periods
   - Flag reversals, qualifications, or contradictions
   - Weigh by confidence language (certainty markers)

2. **Behavioral Inconsistency:**
   - Extract stated values vs. demonstrated priorities
   - Example: "I believe in transparency" but discusses avoiding disclosure
   - Use argument mining to find logical gaps

3. **Markers Beyond Tone:**
   - **Pronoun distance**: Liars use fewer first-person pronouns
   - **Hedging language**: "I think," "arguably," "sort of" (evasion markers)
   - **Cognitive load indicators**: Simpler sentence structure, reduced subordination
   - **Sensory density**: Excessive irrelevant detail can signal fabrication
   - **Verifiability gap**: Claims made without falsifiable specifics

**LIWC Features Specifically:**
- **Certainty words**: always, never, definitely → truth
- **Negations**: not, no, never (excess → deception?)
- **1st person singular**: I, me, my (less in liars)
- **Absolute language**: vs. qualifying language
- **Emotional content**: Excess emotionality can indicate defensive positioning

**Implementation:**
- Compute LIWC feature vectors
- Compare statements across time/contexts
- Score consistency via embedding similarity
- Flag high-variance positions (belief instability)

---

### 3.3 "Movement Patterns" - Group Influence Detection

**What It Means:**
How do individual's beliefs shift toward/away from their communities over time?

**Detection Methods:**

1. **Community Identification:**
   - NER + network analysis: Who is frequently mentioned together?
   - Collaborative structure: Co-authorship, interview frequency
   - Network clustering: Louvain modularity to find coherent groups

2. **Belief Trajectory Analysis:**
   - Chronologically order appearances/publications
   - Extract beliefs at each time point (using methods above)
   - Measure semantic distance between sequential beliefs
   - Calculate convergence toward group belief centroid

3. **Emergence Signals:**
   - **Newly adopted terminology**: When does person start using group's language?
   - **Argument adoption**: Do they start using group's signature arguments?
   - **Focus shift**: Do their topic priorities align with group over time?

4. **Statistical Tests:**
   - Is observed shift larger than random variation?
   - Is shift **toward** group centroid significant?
   - Are there inflection points (sudden adoption vs. gradual drift)?

**Emergent Behavior Analysis:**
- **PageRank on belief networks**: Which beliefs are most influential?
- **Information cascades**: Do contrarian beliefs spread?
- **Echo chamber dynamics**: How isolated is the group ideologically?

**References:**
- [Detecting Clusters/Communities in Social Networks](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6103523/)
- [Community Detection Algorithms (O'Reilly)](https://www.oreilly.com/library/view/graph-algorithms/9781492047674/ch06.html)

---

### 3.4 "Overlaps and Gaps" - Comparative Belief Analysis

**Graph-Based Methods:**

1. **Entity Co-occurrence Analysis:**
   - Build co-occurrence matrices: How often do concepts appear together?
   - Compute Jaccard similarity: Overlap(concepts_A, concepts_B) / Union(concepts_A, concepts_B)
   - Identify shared vs. unique concepts

2. **Belief Alignment Scoring:**
   - Convert beliefs to semantic embeddings
   - Compute cosine similarity between belief pairs
   - Identify clusters of aligned vs. contradictory beliefs

3. **Gap Detection:**
   - Identify logical prerequisites that aren't addressed
   - Find tension points (beliefs that should connect but don't)
   - Score coherence of belief network (network density, centrality distribution)

4. **Asymmetric Relationships:**
   - Does person A reference person B?
   - Does person B reciprocate?
   - Do referenced people actually hold stated beliefs?

**Visualization Approaches:**
- Force-directed graphs: Belief networks with similarity as edge weight
- Clustering visualization: Which beliefs naturally group?
- Temporal animation: How does network structure evolve?

---

## 4. TOOL ECOSYSTEM & IMPLEMENTATIONS

### 4.1 Runcible API

**Status:** Company focused on AI reasoning & trustworthiness (Runcible)

**Key Innovation:**
- Makes probabilistic AI outputs **decidable** (True/False/Undecidable)
- Aims to turn "sounds right" AI into "proves itself right" AI
- Transparency in epistemic limits

**Current Capabilities:**
- Founded on "decidability protocols"
- Emphasis on auditable, trustworthy intelligence
- **Not specifically marketed as belief/worldview extraction tool**

**Potential Integration:**
If Runcible provides APIs for structured reasoning over text, could use for:
- Validating extracted beliefs against consistency
- Flagging undecidable claims
- Providing confidence scores on extractions

**References:**
- [Runcible Website](https://runcible.com/)
- [Runcible Launches Next-Gen AI Reasoning Framework](https://runcible.com/2025/09/05/runcible-launches-new-website-and-next-generation-ai-reasoning-framework/)

---

### 4.2 Claude API & Related Frameworks

**Claude as Extraction Engine:**

1. **Document Analysis:**
   - Claude can read transcripts/articles and extract structured belief statements
   - Strength: Contextual understanding, nuance handling
   - Limitation: Token costs for large corpora

2. **Advanced Tool Use:**
   - Programmatic tool orchestration: Claude writes code to call multiple tools
   - Enables multi-step extraction: NER → relationship extraction → belief synthesis

3. **Claude Deep Research:**
   - Content extraction from web sources
   - Deeper context than API snippets alone

4. **Structured Extraction:**
   - Claude excels at constraint-based extraction (provide schema, extract to schema)
   - Can define belief statement JSON structure, extract to it at scale

**For Weave Integration:**
- Could use Claude for "deep synthesis" mode (expensive, high-quality)
- Combine with cheaper NLP methods for "quick/medium" modes
- Use for validating/refining auto-extracted beliefs

**References:**
- [Claude Web Search API](https://websearchapi.ai/blog/anthropic-claude-web-search-api)
- [Programmatic Tool Calling in Claude](https://www.anthropic.com/engineering/advanced-tool-use)
- [Claude Deep Research MCP Server](https://skywork.ai/skypage/en/claude-deep-research-ai-engineer-guide/1980147193323573248)

---

### 4.3 Entity Extraction & Knowledge Graphs

**Python Libraries (State of Art):**

1. **spaCy** (Industry standard)
   - Fast, pre-trained NER models
   - ~90% accuracy on standard entity types
   - Limited to standard types (PERSON, ORG, GPE, PRODUCT, DATE, etc.)

2. **GliNER** (Emerging leader)
   - Zero-shot entity extraction
   - Can define custom entity types without retraining
   - Ideal for domain-specific beliefs (e.g., "values," "principles")

3. **REBEL** (Relation Extraction)
   - Extracts both entities AND relationships end-to-end
   - Highly relevant: captures beliefs as subject-relation-object triples

4. **Relik** (Entity & Relation Linking)
   - Entity linking: Ground entities to knowledge bases
   - Relationship extraction with models that combine both tasks

**Rust Landscape (2024-2025):**

**Direct Rust NLP is limited.** Better approach: Call Python from Rust

1. **rust-bert**
   - Rust bindings to BERT-like models via tch-rs
   - Token classification possible but requires model conversion
   - Slower than Hugging Face Transformers
   - Steep learning curve for model management

2. **nlprule**
   - Rule-based NLP (rule databases from LanguageTool)
   - Good for tokenization, POS tagging, lemmatization
   - Not suitable for entity extraction at scale

3. **rsnltk**
   - Wraps Python NLTK for Rust
   - Workaround, not native solution

**Practical Recommendation for Weave:**
Keep Python for NLP heavy lifting:
- Extract entities + relationships at start
- Store as JSON
- Process JSON in Rust efficiently

**References:**
- [rust-bert on Lib.rs](https://lib.rs/crates/rust-bert)
- [Fast Tokenizers: How Rust is Turbocharging NLP](https://medium.com/@mshojaei77/fast-tokenizers-how-rust-is-turbocharging-nlp-dd12a1d13fa9)
- [End-to-end NLP Pipelines in Rust](https://aclanthology.org/2020.nlposs-1.4.pdf)

---

### 4.4 Neo4j for Belief Graphs

**Why Neo4j for Worldview Storage:**

1. **Native Graph Structure:**
   - Nodes = Beliefs, Concepts, People, Values
   - Edges = Supports, Contradicts, Causes, Exemplifies, Values
   - Natural fit for belief relationships

2. **Semantic Search:**
   - Vector search: Embed belief statements, find similar beliefs
   - Graph traversal: Follow chains of reasoning
   - Path queries: "What beliefs lead to this conclusion?"

3. **Analysis Queries:**
   - Centrality: Most important beliefs (PageRank)
   - Clustering: Coherent belief subsystems
   - Anomaly detection: Isolated beliefs, logical contradictions

**Practical Schema:**
```
// Nodes
(Belief {statement: "...", confidence: 0.85, source: "quote_location"})
(Concept {name: "wealth", category: "value"})
(Person {name: "Naval Ravikant"})

// Relationships
(Belief)-[:SUPPORTS]->(Belief)
(Belief)-[:CONTRADICTS]->(Belief)
(Belief)-[:CITES]->(Concept)
(Belief)-[:HELD_BY]->(Person)
(Person)-[:INFLUENCED_BY]->(Person)
```

**Queries Enabled:**
- Find all contradictions in belief system
- Trace dependencies: "What must be true for X to be true?"
- Compare belief graphs across people
- Identify consensus vs. distinctive beliefs

**References:**
- [The Future of Knowledge Graph: Structured & Semantic Search](https://neo4j.com/blog/developer/knowledge-graph-structured-semantic-search/)
- [Vector Search on Knowledge Graph in Neo4j](https://www.educative.io/blog/vector-search-on-knowledge-graph-in-neo4j)
- [neosemantics (n10s): Neo4j RDF & Semantics Toolkit](https://neo4j.com/labs/neosemantics/)

---

### 4.5 LIWC (Linguistic Inquiry & Word Count)

**What It Is:**
Gold standard psycholinguistic text analysis tool with 100+ built-in dictionaries

**Psycholinguistic Categories:**
- **Emotion**: Positive/negative affect, anxiety, anger, sadness
- **Cognitive processes**: Insight, causation, discrepancy, certainty
- **Social processes**: Family, friends, humans
- **Perception**: See, hear, feel
- **Biological processes**: Body, health, sex, ingest
- **Drives**: Affiliation, achievement, power
- **Relativity**: Motion, space, time
- **Personal concerns**: Work, achievement, leisure, money, death
- **Stylistic**: Pronouns, articles, prepositions, conjunctions

**For Worldview Extraction:**

1. **Psychological Profile:**
   - Certainty language → epistemological confidence
   - Power language → values around agency/control
   - Social orientation → communal vs. individualist values
   - Temporal focus → present vs. future oriented

2. **Consistency Checking:**
   - Compare LIWC profiles across time periods
   - Significant shifts in language use = potential belief changes
   - Mismatches (high drive language + low achievement language) = tensions

3. **Deception Flagging:**
   - Low first-person pronouns = distancing from claims
   - High negation words = defensive positioning
   - Excessive sensory language = fabrication signals

**Limitations:**
- Lexicon-based (misses context, sarcasm)
- Category overlap can confound interpretation
- Works best as **input to ML**, not standalone analysis

**References:**
- [LIWC: How It Works](https://www.liwc.app/help/howitworks)
- [LIWC-22 Official Site](https://www.liwc.app/)
- [LIWC and Computerized Text Analysis Methods](https://www.cs.cmu.edu/~ylataus/files/TausczikPennebaker2010.pdf)

---

## 5. INTEGRATED FRAMEWORK: WEAVE RECOMMENDATION

### 5.1 Optimal Architecture for Weave

**Multi-Layer Approach (Quick → Medium → Deep):**

**QUICK MODE (Pure Code):**
1. Extract keywords via YAKE/RAKE
2. Run spaCy NER for entity discovery
3. Compute TF-IDF for term importance
4. Return top terms grouped by frequency

**MEDIUM MODE (Local NLP):**
1. Embed keywords/entities with Sentence-BERT (all-MiniLM-L6-v2)
2. Cluster via HDBSCAN + silhouette optimization
3. Apply semantic-driven clustering refinement
4. Generate cluster labels from centroid terms
5. Run LIWC for psychological profile
6. Detect contradictions via embedding similarity
7. Rank worldview points by cluster coherence × LIWC signal strength

**DEEP MODE (LLM Synthesis):**
1. Provide Ollama with:
   - Cluster summaries (semantic themes)
   - Top quotes per cluster (grounding)
   - LIWC profiles (psychological markers)
   - Identified contradictions (tension points)
   - Argument structures (if argument mined)
2. Prompt for coherent narrative synthesis
3. Return elaborated worldview points with supporting quotes

### 5.2 Novel Capabilities for Future Versions

**Version 1.x:**
- Contrarian detection: Flag beliefs distinct from peer group
- Temporal analysis: Track worldview evolution
- Argument mining: Extract support/attack relationships
- Knowledge graph export: Neo4j-compatible format

**Version 2.x:**
- Comparative analysis: Compare worldviews of multiple people
- Perspective embedding: Identify distinct interpretive lenses
- Group movement detection: How beliefs shift toward/from communities
- Consistency scoring: Identify logical gaps and tensions

### 5.3 Data Models & Storage

**Extended Weave Data Models:**

```python
class ExtractedBelief(BaseModel):
    statement: str  # Propositional claim
    confidence: float  # 0-1 based on evidence density
    evidence: list[str]  # Supporting quotes/phrases
    sources: list[str]  # Which videos/timestamps

    # Contrarian scoring
    distinctiveness: float  # How unique to this person
    category: str  # e.g., "epistemology", "value", "prediction"

    # Psychological markers
    certainty_level: float  # From LIWC certainty words
    emotional_intensity: float  # From LIWC affect
    temporal_focus: str  # Past/present/future

class WorldviewPoint(BaseModel):
    # Original fields
    point: str
    elaboration: Optional[str]
    confidence: float
    evidence: list[str]
    sources: list[str]

    # Extended fields
    supporting_beliefs: list[str]  # Other beliefs that support this
    contradicting_beliefs: list[str]  # Beliefs in tension
    is_contrarian: bool  # Distinctive from peer group?
    is_primary: bool  # Central vs. peripheral to worldview?
    psychological_signature: dict  # LIWC markers

class WorldviewAnalysis(BaseModel):
    subject: str
    worldview_points: list[WorldviewPoint]

    # New analyses
    coherence_score: float  # How logically integrated?
    contrarian_profile: dict  # Distinctive beliefs with distinctiveness scores
    psychological_profile: dict  # Aggregate LIWC by category
    movement_history: Optional[list[dict]]  # Temporal worldview changes
    peer_alignment: Optional[dict]  # Similarity to reference groups
```

---

## 6. REFERENCES BY CATEGORY

### Worldview & Philosophical Foundations
- [A guide to ontology, epistemology, and philosophical perspectives](https://i2insights.org/2017/05/02/philosophy-for-interdisciplinarity/)
- [Navigating Ontology, Epistemology, and Axiology in Research](https://nsuworks.nova.edu/cgi/viewcontent.cgi?article=7632&context=tqr)
- [Components of a Worldview – Ontology, Epistemology & Linguistics](https://jessicaptomey.com/2012/08/10/conceptualizing-worldview-ontology-epistemology-linguistics/)

### Psychological Models
- [Big Five Personality Traits: The 5-Factor Model](https://www.simplypsychology.org/big-five-personality.html)
- [Myers-Briggs vs. OCEAN: Industrial Psychologist Comparison](https://www.interviewaceapp.com/blog/myers-briggs-vs-ocean-an-industrial-psychologist-breaks-down-the-differences/)
- [5 Leading Alternatives to Big Five](https://www.teamdynamics.io/blog/5-leading-alternatives-to-big-five-top-workplace-personality-tests/)

### Narrative & Discourse Analysis
- [Modeling Narrative Discourse (David K. Elson)](http://www.cs.columbia.edu/~delson/pubs/Modeling-Narrative-Discourse_Elson_R4.pdf)
- [Extracting narrative signals from public discourse](https://www.nature.com/articles/s41599-025-06017-x)
- [Combining Critical Discourse Analysis and NLP tools](https://www.researchgate.net/publication/263167821_Combining_Critical_Discourse_Analysis_and_NLP_tools_in_investigations_of_religious_prose)
- [Discourse Analysis in NLP](https://aclanthology.org/P19-4003/)

### Abstract Meaning Representation
- [Survey of Abstract Meaning Representation: Then, Now, Future](https://arxiv.org/html/2505.03229v1)
- [AMR Bibliography](https://nert-nlp.github.io/AMR-Bibliography/)

### Opinion Mining & Sentiment Analysis
- [Sentiment Analysis: Mining Opinions, Sentiments, and Emotions](https://direct.mit.edu/coli/article/42/3/595/1534/Sentiment-Analysis-Mining-Opinions-Sentiments-and)
- [Sentiment Analysis and Opinion Mining (Bing Liu)](https://www.cs.uic.edu/~liub/FBS/SentimentAnalysis-and-OpinionMining.pdf)

### Stance Detection & Contrarian Identification
- [Survey of Stance Detection on Social Media (2024)](https://arxiv.org/abs/2409.15690)
- [Unsupervised stance detection for social media](https://aclanthology.org/2024.eacl-long.107/)
- [Multi-modal Stance Detection (2024)](https://aclanthology.org/2024.findings-acl.736/)
- [Nonconformity Defines the Self: Minority Opinion Status](https://journals.sagepub.com/doi/10.1177/0146167209358075)
- [Optimal Distinctiveness Theory](https://www.sciencedirect.com/science/article/abs/pii/S0065260110430026)

### Argument Mining
- [Argument Mining: A Survey](https://direct.mit.edu/coli/article/45/4/765/93362/Argument-Mining-A-Survey)
- [Five Years of Argument Mining: Data-Driven Analysis](https://www.ijcai.org/proceedings/2018/0766.pdf)

### Knowledge Graphs & Entity Extraction
- [Building Knowledge Graphs (End-to-End Guide, 2026)](https://medium.com/@brian-curry-research/building-a-knowledge-graph-a-comprehensive-end-to-end-guide-using-modern-tools-e06fe8f3b368)
- [Entity Linking and Relationship Extraction with Relik](https://neo4j.com/blog/developer/entity-linking-relationship-extraction-relik-llamaindex/)
- [The Future of Knowledge Graph: Structured & Semantic Search](https://neo4j.com/blog/developer/knowledge-graph-structured-semantic-search/)

### Topic Modeling & Semantic Clustering
- [Latent Dirichlet Allocation: LDA Survey](https://www.ccs.neu.edu/home/vip/teach/DMcourse/5_topicmodel_summ/LDA_TM/LDA_survey_1711.04305.pdf)
- [Semantic-LDA](https://dl.acm.org/doi/10.1145/3639409)
- [Semantic-Driven Topic Modeling for Analyzing Creativity](https://arxiv.org/html/2509.16835)

### Deception Detection & Linguistic Markers
- [Acoustic-Prosodic and Lexical Cues to Deception](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00311/43547/Acoustic-Prosodic-and-Lexical-Cues-to-Deception)
- [Verbal Lie Detection Using LLMs](https://www.nature.com/articles/s41598-023-50214-0)
- [Detecting Deception Through Linguistic Cues (2025)](https://journals.sagepub.com/doi/10.1177/0261927X251316883)

### Disagreement & Perspective Modeling
- [Beyond Consensus: Perspectivist Modeling of Annotator Disagreement](https://arxiv.org/html/2601.09065)
- [Agree to Disagree: Improving Disagreement Detection](https://www.researchgate.net/publication/319186878_Agree_to_Disagree_Improving_Disagreement_Detection_with_Dual_GRUs)

### Social Network Analysis & Community Detection
- [Detecting Clusters/Communities in Social Networks](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6103523/)
- [Community Detection Algorithms (O'Reilly)](https://www.oreilly.com/library/view/graph-algorithms/9781492047674/ch06.html)

### Rust NLP Libraries
- [rust-bert on Lib.rs](https://lib.rs/crates/rust-bert)
- [Fast Tokenizers: How Rust is Turbocharging NLP](https://medium.com/@mshojaei77/fast-tokenizers-how-rust-is-turbocharging-nlp-dd12a1d13fa9)
- [End-to-end NLP Pipelines in Rust](https://aclanthology.org/2020.nlposs-1.4.pdf)

### LIWC & Psycholinguistics
- [LIWC: How It Works](https://www.liwc.app/help/howitworks)
- [LIWC-22 Official Site](https://www.liwc.app/)
- [LIWC and Computerized Text Analysis Methods](https://www.cs.cmu.edu/~ylataus/files/TausczikPennebaker2010.pdf)

---

## 7. KEY TAKEAWAYS FOR WEAVE

1. **Worldview is fundamentally tripartite**: Ontology (what exists) + Epistemology (how we know) + Axiology (what matters). Extract at all three levels.

2. **No single method is sufficient**. Combine:
   - Semantic clustering (discover themes)
   - Entity extraction (identify key concepts/people)
   - Argument mining (understand logical structure)
   - LIWC (psychological signatures)
   - Stance detection (find contrarian views)

3. **Contrarian beliefs are often the most revealing**. Distinctiveness scoring (how unique to this person) is signal of core worldview.

4. **Temporal dimension matters**. Beliefs aren't static. Track evolution, identify inflection points, detect group influence.

5. **Graph representation is natural**. Store as knowledge graph (Neo4j or similar) to enable:
   - Coherence analysis (logical consistency)
   - Path analysis (how beliefs lead to conclusions)
   - Comparative analysis (overlap with others)

6. **Rust integration**: Keep Python for heavy NLP, export to JSON, process/store in Rust efficiently.

7. **The "deep synthesis" level is where LLMs add value**. Provide them with:
   - Structured data (clusters, quotes, arguments)
   - Flagged tensions/gaps
   - Psychological markers (LIWC)
   Then ask for coherent narrative synthesis.

---

**Document Version:** 1.0
**Last Updated:** February 2026
**Status:** Research Complete
