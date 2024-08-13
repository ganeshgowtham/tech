flowchart TD
    A(User query) --> B(LLM Wrappers)
    B --> C{Cache hit?}
    C -- Yes --> D(Response generated)
    C -- No --> E(LLM generation)
    E --> F(Cache Store)
    E --> G(Vector Store)
    B --> H(Generate Embeddings)
    H --> I(Similarity Evaluation)
    I --> G
    I --> F
    F --> C
    G --> I