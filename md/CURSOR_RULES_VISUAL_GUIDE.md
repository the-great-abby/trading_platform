# Cursor Rules Visual Guide

## 🎯 Overview

This guide provides visual representations of the optimized cursor rules system using Mermaid diagrams. The system has been streamlined for better performance, maintainability, and user experience.

## 📁 Current File Structure

```
.cursor/rules/
├── core.mdc              # Universal rules (always active)
├── python.mdc            # Python development patterns
├── infrastructure.mdc    # Docker, Kubernetes, security
├── data.mdc              # Database and data management
├── trading.mdc           # Trading system specific
├── styles.mdc            # AI response style configuration
├── quick-styles.md       # Quick reference guide
├── visual-overview.md    # Visual system explanation
└── diagrams.md           # All Mermaid diagrams
```

## 🔄 System Architecture

### File Structure Overview
```mermaid
graph TD
    A[.cursor/rules/] --> B[core.mdc]
    A --> C[python.mdc]
    A --> D[infrastructure.mdc]
    A --> E[data.mdc]
    A --> F[trading.mdc]
    A --> G[styles.mdc]
    A --> H[quick-styles.md]
    
    B --> B1[Universal Rules<br/>Always Active]
    C --> C1[Python Development<br/>*.py, requirements.txt]
    D --> D1[Docker, Kubernetes<br/>Security, Deployment]
    E --> E1[Database, Data<br/>Migrations, Processing]
    F --> F1[Trading System<br/>Strategies, AI, Risk]
    G --> G1[AI Response Styles<br/>Dynamic Switching]
    H --> H1[Quick Reference<br/>Style Commands]
    
    style B fill:#e1f5fe
    style C fill:#f3e5f5
    style D fill:#e8f5e8
    style E fill:#fff3e0
    style F fill:#fce4ec
    style G fill:#f1f8e9
    style H fill:#fafafa
```

### Rule Application Flow
```mermaid
flowchart TD
    A[File Opened in Cursor] --> B{File Type?}
    
    B -->|All Files| C[core.mdc<br/>Universal Rules]
    B -->|Python Files| D[python.mdc<br/>Python Patterns]
    B -->|Infrastructure| E[infrastructure.mdc<br/>Docker/K8s/Security]
    B -->|Database/Data| F[data.mdc<br/>DB & Data Management]
    B -->|Trading System| G[trading.mdc<br/>Trading Patterns]
    
    C --> H[AI Assistant<br/>Orion Identity]
    D --> I[Virtual Environments<br/>Python Best Practices]
    E --> J[Containerization<br/>Security & Deployment]
    F --> K[Migrations<br/>Data Processing]
    G --> L[Strategy Development<br/>Risk Management]
    
    H --> M[Apply Rules<br/>Generate Response]
    I --> M
    J --> M
    K --> M
    L --> M
    
    style C fill:#e1f5fe
    style D fill:#f3e5f5
    style E fill:#e8f5e8
    style F fill:#fff3e0
    style G fill:#fce4ec
```

## 🎨 Dynamic Style Switching

### Style State Machine
```mermaid
stateDiagram-v2
    [*] --> Default: make mcp-style-default
    
    Default --> Debug: make mcp-style-debug
    Default --> Teach: make mcp-style-teach
    Default --> Review: make mcp-style-review
    Default --> Arch: make mcp-style-arch
    Default --> Minimal: make mcp-style-minimal
    Default --> Verbose: make mcp-style-verbose
    
    Debug --> Default: make mcp-style-default
    Teach --> Default: make mcp-style-default
    Review --> Default: make mcp-style-default
    Arch --> Default: make mcp-style-default
    Minimal --> Default: make mcp-style-default
    Verbose --> Default: make mcp-style-default
    
    note right of Default
        Technical Assistant
        Professional & Friendly
        Solution-focused
    end note
    
    note right of Debug
        Troubleshooting Mode
        Analytical & Methodical
        Error Analysis
    end note
    
    note right of Teach
        Educational Mode
        Concept Breakdown
        Progressive Learning
    end note
    
    note right of Review
        Code Review Mode
        Quality Focus
        Best Practices
    end note
    
    note right of Arch
        Architecture Mode
        System Design
        Scalability Planning
    end note
    
    note right of Minimal
        Quick Answers
        Essential Info Only
        Action-oriented
    end note
    
    note right of Verbose
        Comprehensive Mode
        Detailed Explanations
        Multiple Perspectives
    end note
```

## 🧠 Rule Categories Mind Map

```mermaid
mindmap
  root((Cursor Rules))
    Core
      AI Assistant Identity
      Development Workflow
      Code Quality
      Security & Best Practices
      Documentation
      Error Handling
      Performance
    Python
      Virtual Environments
      Package Management
      Code Style & Structure
      Project Organization
      Async Programming
      Testing & Quality
      Logging & Monitoring
      Error Handling
      Performance
      Security
    Infrastructure
      Docker & Containerization
      Kubernetes Operations
      Deployment Strategy
      Security Practices
      Service Management
      Configuration Management
      Monitoring & Observability
    Data
      Database Schema Changes
      Migration Best Practices
      Database Operations
      Data Management
      Trading Data Management
      Data Processing
      Performance Optimization
      Backup and Recovery
      Data Security
    Trading
      Configuration Management
      AI Integration
      Trading Strategy Development
      Backtesting Framework
      Risk Management
      Data Management
      Performance Monitoring
      API Design
      Testing
      Deployment
    Styles
      Communication Style
      Technical Approach
      Project-Specific Behavior
      Response Structure
      Style Switching
      Quick Commands
```

## 🔄 Development Workflow Integration

```mermaid
sequenceDiagram
    participant U as User
    participant C as Cursor
    participant R as Rules System
    participant S as Style System
    
    U->>C: Open Python file
    C->>R: Load applicable rules
    R->>C: core.mdc + python.mdc
    
    U->>C: Ask for help with async code
    C->>S: Check current style
    S->>C: Default (Technical Assistant)
    C->>U: Provide async guidance
    
    U->>U: Run: make mcp-style-teach
    U->>S: Switch to teaching mode
    S->>C: Update AI response style
    
    U->>C: Ask about Docker deployment
    C->>R: Load infrastructure rules
    R->>C: core.mdc + infrastructure.mdc
    C->>U: Provide teaching-style Docker guidance
    
    U->>U: Run: make mcp-style-debug
    U->>S: Switch to debugging mode
    S->>C: Update AI response style
    
    U->>C: Report database migration issue
    C->>R: Load data rules
    R->>C: core.mdc + data.mdc
    C->>U: Provide debugging-style migration help
```

## 📊 Optimization Benefits

```mermaid
graph LR
    subgraph "Before Optimization"
        A1[11 Files<br/>35KB Total]
        A2[Redundant Rules]
        A3[Scattered Concepts]
        A4[Slow Loading]
    end
    
    subgraph "After Optimization"
        B1[7 Files<br/>18KB Total]
        B2[Consolidated Rules]
        B3[Logical Grouping]
        B4[Fast Loading]
    end
    
    A1 -.->|47% Reduction| B1
    A2 -.->|Eliminated| B2
    A3 -.->|Organized| B3
    A4 -.->|Improved| B4
    
    style A1 fill:#ffebee
    style B1 fill:#e8f5e8
    style A2 fill:#ffebee
    style B2 fill:#e8f5e8
    style A3 fill:#ffebee
    style B3 fill:#e8f5e8
    style A4 fill:#ffebee
    style B4 fill:#e8f5e8
```

## 🎯 Usage Examples

### Quick Style Switching
```bash
# Switch to different AI response styles
make mcp-style-debug    # For troubleshooting
make mcp-style-teach    # For learning
make mcp-style-review   # For code review
make mcp-style-arch     # For system design
make mcp-style-minimal  # For quick answers
make mcp-style-verbose  # For detailed analysis

# Check current style
make mcp-style-current

# List all available styles
make mcp-style-list
```

### Rule Application Examples
```mermaid
flowchart TD
    A[User Task] --> B{Task Type?}
    
    B -->|Python Development| C[python.mdc Active]
    B -->|Database Work| D[data.mdc Active]
    B -->|Infrastructure| E[infrastructure.mdc Active]
    B -->|Trading System| F[trading.mdc Active]
    
    C --> G[Virtual Environment<br/>Package Management<br/>Code Style]
    D --> H[Migrations<br/>Data Processing<br/>Performance]
    E --> I[Docker/K8s<br/>Security<br/>Deployment]
    F --> J[Strategies<br/>AI Integration<br/>Risk Management]
    
    G --> K[AI Response with<br/>Python Best Practices]
    H --> L[AI Response with<br/>Database Expertise]
    I --> M[AI Response with<br/>Infrastructure Knowledge]
    J --> N[AI Response with<br/>Trading Domain Expertise]
    
    K --> O[Enhanced Development<br/>Experience]
    L --> O
    M --> O
    N --> O
    
    style C fill:#f3e5f5
    style D fill:#fff3e0
    style E fill:#e8f5e8
    style F fill:#fce4ec
```

## 📈 Performance Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **File Count** | 11 files | 7 files | 47% reduction |
| **Total Size** | 35KB | 18KB | 49% reduction |
| **Loading Speed** | Slow | Fast | Significant improvement |
| **Maintainability** | Complex | Simple | Much easier |
| **Context Matching** | Basic | Optimized | Better accuracy |

## 🎨 Visual Documentation Files

- **[Visual Overview](.cursor/rules/visual-overview.md)** - Comprehensive system explanation
- **[Diagrams](.cursor/rules/diagrams.md)** - All Mermaid diagrams in one place
- **[Quick Styles](.cursor/rules/quick-styles.md)** - Style switching reference

## 🚀 Benefits Summary

### **For Developers**
- **Visual understanding** of the rules system
- **Quick style switching** without file creation
- **Context-aware assistance** based on file type
- **Consistent patterns** across all development areas

### **For Teams**
- **Clear documentation** with visual diagrams
- **Easy maintenance** with logical organization
- **Reduced conflicts** when multiple people edit rules
- **Scalable structure** for future additions

### **For Performance**
- **Faster rule loading** with fewer files
- **Better context matching** with optimized globs
- **Reduced memory usage** with consolidated rules
- **Improved responsiveness** in Cursor

The visual guide makes the cursor rules system much more accessible and easier to understand, while the optimized structure provides better performance and maintainability. 