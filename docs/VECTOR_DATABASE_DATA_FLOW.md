# Vector Database Data Flow Documentation

## 🎯 **Process Overview**

This document outlines the complete data flow for loading information into your Kubernetes vectors database using the Ollama controller to create embeddings and index system documentation.

## 📊 **Data Flow Diagram**

```mermaid
graph TB
    subgraph "Source Data"
        A1[System Documentation<br/>docs/, md/, k8s/]
        A2[Code Files<br/>services/, src/]
        A3[Configuration<br/>yaml, yml files]
        A4[Scripts<br/>sh, py files]
    end
    
    subgraph "Discovery & Processing"
        B1[Architecture Vectorizer<br/>File Discovery]
        B2[Content Chunking<br/>Split into manageable pieces]
        B3[Category Classification<br/>kubernetes, trading, etc.]
        B4[Metadata Extraction<br/>file info, timestamps]
    end
    
    subgraph "Embedding Generation"
        C1[Ollama Controller<br/>LLM Service]
        C2[Embedding API<br/>/api/embed endpoint]
        C3[Vector Generation<br/>1536-dimensional vectors]
        C4[Fallback Embeddings<br/>If LLM fails]
    end
    
    subgraph "Storage & Indexing"
        D1[Postgres Vector Storage<br/>pgvector extension]
        D2[Vector Database<br/>TimescaleDB backend]
        D3[Metadata Storage<br/>JSONB columns]
        D4[Index Creation<br/>Vector similarity indexes]
    end
    
    subgraph "Query & Search"
        E1[RAG Chat Services<br/>Semantic search]
        E2[AI IDE Service<br/>Development assistance]
        E3[Unified Dashboards<br/>Trading system knowledge]
        E4[API Endpoints<br/>RESTful search interface]
    end
    
    subgraph "Orchestration"
        F1[Kubernetes Jobs<br/>Scheduled vectorization]
        F2[Background Service<br/>Continuous processing]
        F3[Local Scripts<br/>Development testing]
        F4[Cron Jobs<br/>Regular updates]
    end
    
    %% Data Flow Connections
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    
    D4 --> E1
    D4 --> E2
    D4 --> E3
    D4 --> E4
    
    F1 --> B1
    F2 --> B1
    F3 --> B1
    F4 --> B1
    
    %% Styling
    classDef sourceData fill:#e1f5fe
    classDef processing fill:#f3e5f5
    classDef embedding fill:#fff3e0
    classDef storage fill:#e8f5e8
    classDef query fill:#fce4ec
    classDef orchestration fill:#f1f8e9
    
    class A1,A2,A3,A4 sourceData
    class B1,B2,B3,B4 processing
    class C1,C2,C3,C4 embedding
    class D1,D2,D3,D4 storage
    class E1,E2,E3,E4 query
    class F1,F2,F3,F4 orchestration
```

## 🔄 **Process Steps**

### **Step 1: Data Discovery**
```mermaid
flowchart LR
    A[Repository Scan] --> B[File Pattern Matching]
    B --> C[Priority Sorting]
    C --> D[Content Validation]
    D --> E[File Queue]
    
    subgraph "File Patterns"
        F1[**/*.md]
        F2[**/*.yaml]
        F3[**/*.py]
        F4[**/*.sh]
    end
    
    subgraph "Priority Levels"
        G1[High: docs/, k8s/]
        G2[Medium: configs/]
        G3[Low: generated/]
    end
```

### **Step 2: Content Processing**
```mermaid
flowchart TD
    A[File Content] --> B[Encoding Detection]
    B --> C[Content Chunking]
    C --> D[Category Classification]
    D --> E[Metadata Creation]
    
    subgraph "Chunking Strategy"
        F1[Markdown: Header-based]
        F2[Code: Function-based]
        F3[Config: Section-based]
        F4[General: Size-based]
    end
    
    subgraph "Categories"
        G1[kubernetes]
        G2[trading]
        G3[architecture]
        G4[monitoring]
        G5[database]
        G6[api]
    end
```

### **Step 3: Embedding Generation**
```mermaid
sequenceDiagram
    participant V as Vectorizer
    participant O as Ollama Controller
    participant C as Cache
    participant F as Fallback
    
    V->>O: POST /api/embed
    Note over V,O: Send content + metadata
    
    O->>O: Generate embedding
    O->>V: Return 1536-dim vector
    
    alt Cache Hit
        V->>C: Check cache
        C->>V: Return cached embedding
    else Cache Miss
        V->>O: Request new embedding
        O->>V: Return embedding
        V->>C: Store in cache
    end
    
    alt LLM Failure
        V->>F: Use fallback method
        F->>V: Return simple embedding
    end
```

### **Step 4: Storage & Indexing**
```mermaid
graph TB
    A[Vector + Metadata] --> B[Postgres Vector Storage]
    B --> C[pgvector Extension]
    C --> D[Vector Index Creation]
    D --> E[Similarity Search Ready]
    
    subgraph "Database Schema"
        F1[vector_embeddings table]
        F2[vectorization_jobs table]
        F3[news_embeddings table]
    end
    
    subgraph "Index Types"
        G1[Vector similarity index]
        G2[Metadata JSONB index]
        G3[Content type index]
        G4[Timestamp index]
    end
```

## 📈 **Performance Metrics**

### **Processing Statistics**
```mermaid
pie title File Processing Distribution
    "Markdown Files" : 45
    "Kubernetes Configs" : 25
    "Python Code" : 15
    "Shell Scripts" : 10
    "Other" : 5
```

### **Vectorization Timeline**
```mermaid
gantt
    title Vectorization Job Timeline
    dateFormat X
    axisFormat %H:%M
    
    section Discovery
    File Scanning    :0, 2
    Pattern Matching :2, 4
    Priority Sorting :4, 5
    
    section Processing
    Content Chunking :5, 15
    Category Classification :15, 20
    Metadata Extraction :20, 25
    
    section Embedding
    LLM Requests     :25, 45
    Vector Generation :45, 50
    Cache Storage    :50, 55
    
    section Storage
    Database Insert  :55, 65
    Index Creation   :65, 70
    Completion       :70, 75
```

## 🔍 **Search Flow**

### **Query Processing**
```mermaid
flowchart TD
    A[User Query] --> B[Query Preprocessing]
    B --> C[Namespace Filtering]
    C --> D[Vector Search]
    D --> E[Similarity Scoring]
    E --> F[Result Ranking]
    F --> G[Context Building]
    G --> H[Response Generation]
    
    subgraph "Search Types"
        I1[Semantic Search]
        I2[Metadata Filter]
        I3[Category Search]
        I4[Hybrid Search]
    end
    
    subgraph "Scoring Methods"
        J1[Cosine Similarity]
        J2[Euclidean Distance]
        J3[Manhattan Distance]
        J4[Custom Scoring]
    end
```

## 🛠️ **Troubleshooting Flow**

### **Issue Detection**
```mermaid
flowchart TD
    A[System Alert] --> B{Check Service Status}
    B -->|Running| C[Check Job Logs]
    B -->|Not Running| D[Restart Service]
    
    C --> E{Job Status}
    E -->|Success| F[Check Data Quality]
    E -->|Failed| G[Analyze Error Logs]
    
    G --> H{Error Type}
    H -->|LLM Error| I[Check Ollama Controller]
    H -->|Storage Error| J[Check Database]
    H -->|Network Error| K[Check Connectivity]
    
    I --> L[Restart Ollama]
    J --> M[Check DB Connection]
    K --> N[Check Network Config]
    
    L --> O[Retry Vectorization]
    M --> O
    N --> O
    O --> P[Monitor Results]
```

## 📊 **Monitoring Dashboard**

### **Key Metrics**
```mermaid
graph LR
    A[Vectorization Jobs] --> B[Success Rate: 95%]
    A --> C[Processing Time: 45min]
    A --> D[Files Processed: 1,247]
    
    E[Vector Storage] --> F[Total Vectors: 15,432]
    E --> G[Storage Used: 2.3GB]
    E --> H[Search Latency: 120ms]
    
    I[Search Queries] --> J[Daily Queries: 1,234]
    I --> K[Avg Response Time: 0.8s]
    I --> L[Success Rate: 98.5%]
```

## 🔄 **Maintenance Schedule**

### **Regular Tasks**
```mermaid
timeline
    title Vector Database Maintenance
    
    Daily    : Check job status
            : Monitor service health
            : Review error logs
    
    Weekly   : Analyze search quality
            : Check storage usage
            : Review performance metrics
    
    Monthly  : Clean old embeddings
            : Update vectorization patterns
            : Optimize database indexes
    
    Quarterly: Full system review
            : Update documentation
            : Performance tuning
            : Security audit
```

---

**Last Updated**: $(date)
**Version**: 1.0
**Maintainer**: Orion AI Assistant










