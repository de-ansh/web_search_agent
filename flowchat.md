graph TD
    %% User Interface Layer
    A[User Input: Search Query] --> B[Next.js Frontend]
    B --> C[API Request to Backend]
    
    %% Backend API Layer
    C --> D[FastAPI Backend Server]
    D --> E[Query Processing Pipeline]
    
    %% Query Validation
    E --> F[Query Validator]
    F --> G{Valid Query?}
    G -->|No| H[Return Error:<br/>Invalid Query]
    G -->|Yes| I[Query Normalizer]
    
    %% Similarity Detection
    I --> J[Embedding Service]
    J --> K[Generate Query Embedding]
    K --> L[Similarity Detector]
    L --> M{Similar Query<br/>Found in Cache?}
    
    %% Cache Hit Path
    M -->|Yes| N[Retrieve Cached Results]
    N --> O[Generate Combined Summary<br/>from Cached Data]
    O --> P[Return Cached Results<br/>with Overview]
    
    %% Cache Miss Path - Web Search
    M -->|No| Q[Web Scraper Engine]
    Q --> R[Multi-Engine Search<br/>Bing, Yahoo, DuckDuckGo]
    R --> S[Get Top 4 Search Results]
    
    %% Parallel Content Processing
    S --> T[Parallel Page Processing]
    T --> U1[Process Page 1]
    T --> U2[Process Page 2]
    T --> U3[Process Page 3]
    T --> U4[Process Page 4]
    
    %% Individual Page Processing
    U1 --> V1[Scrape Content<br/>12s timeout]
    U2 --> V2[Scrape Content<br/>12s timeout]
    U3 --> V3[Scrape Content<br/>12s timeout]
    U4 --> V4[Scrape Content<br/>12s timeout]
    
    V1 --> W1[Clean & Extract Text]
    V2 --> W2[Clean & Extract Text]
    V3 --> W3[Clean & Extract Text]
    V4 --> W4[Clean & Extract Text]
    
    W1 --> X1[AI Summarizer<br/>OpenAI/HuggingFace]
    W2 --> X2[AI Summarizer<br/>OpenAI/HuggingFace]
    W3 --> X3[AI Summarizer<br/>OpenAI/HuggingFace]
    W4 --> X4[AI Summarizer<br/>OpenAI/HuggingFace]
    
    %% Results Aggregation
    X1 --> Y[Collect Successful Results]
    X2 --> Y
    X3 --> Y
    X4 --> Y
    
    Y --> Z[Generate Comprehensive Summary]
    Z --> AA[Content Summarizer]
    AA --> BB[Create Perplexity-style Overview]
    
    %% Storage & Response
    BB --> CC[Store Query & Results]
    CC --> DD[Update Similarity Cache]
    DD --> EE[Return Complete Results<br/>with AI Overview]
    
    %% Response Path
    P --> FF[Frontend Receives Results]
    EE --> FF
    FF --> GG[Display AI Overview]
    FF --> HH[Display Source Details]
    H --> II[Display Error Message]
    
    %% Data Storage Components
    JJ[(Similarity Cache<br/>JSON File)] --> L
    DD --> JJ
    
    KK[(Query History<br/>& Embeddings)] --> L
    CC --> KK
    
    %% AI Services Detail
    subgraph AI[AI Services Layer]
        LL[Embedding Service<br/>sentence-transformers]
        MM[Query Validator<br/>OpenAI GPT-3.5]
        NN[Content Summarizer<br/>OpenAI/HuggingFace]
    end
    
    F --> MM
    J --> LL
    AA --> NN
    
    %% Core Components Detail
    subgraph Core[Core Components]
        OO[Query Validator<br/>AI-powered validation]
        PP[Similarity Detector<br/>Embedding-based search]
        QQ[Web Scraper<br/>Playwright automation]
    end
    
    F --> OO
    L --> PP
    Q --> QQ
    
    %% Technology Stack
    subgraph Frontend[Frontend Stack]
        RR[Next.js 14 App Router]
        SS[TypeScript]
        TT[Tailwind CSS]
        UU[Axios HTTP Client]
    end
    
    subgraph Backend[Backend Stack]
        VV[FastAPI]
        WW[Playwright]
        XX[Python 3.9+]
        YY[UV Package Manager]
    end
    
    %% Error Handling
    subgraph Error[Error Handling]
        ZZ[Timeout: 20s total]
        AAA[Fallback: Partial results]
        BBB[Graceful degradation]
    end
    
    T --> ZZ
    
    %% Performance Optimizations
    subgraph Perf[Performance Features]
        CCC[Parallel Processing]
        DDD[12s per page timeout]
        EEE[Smart caching]
        FFF[Optimized AI models]
    end
    
    T --> CCC
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style D fill:#e8f5e8
    style Q fill:#fff3e0
    style AA fill:#fce4ec
    style JJ fill:#f1f8e9
    style KK fill:#f1f8e9
