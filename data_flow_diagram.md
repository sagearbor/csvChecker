# CSV Quality Checker - Data Flow Diagram

To view this diagram:
1. Copy the Mermaid code below
2. Paste it into https://mermaid.live/ or any Mermaid viewer
3. Or use a Markdown editor that supports Mermaid

```mermaid
flowchart TD
    %% Input Layer
    A[User Uploads CSV File] --> B[Streamlit File Uploader]
    A1[User Configures Schema] --> B1[JSON Schema Parser]
    A2[User Configures Rules] --> B2[JSON Rules Parser]
    A3[User Sets Min Rows] --> B3[Configuration Input]
    
    %% Streamlit Frontend Processing
    B --> C[Temporary File Creation]
    B1 --> D[Schema Validation]
    B2 --> E[Rules Validation]
    B3 --> F[Parameter Setup]
    
    %% Error Handling
    D -->|Invalid JSON| G[Error Display]
    E -->|Invalid JSON| G
    
    %% Main Pipeline Entry
    C --> H[run_quality_checks()]
    D -->|Valid Schema| H
    E -->|Valid Rules| H
    F --> H
    
    %% Data Loading Phase
    H --> I[load_csv()]
    I --> J{File Load Success?}
    J -->|No| K[CSVLoadError]
    K --> L[Error Results]
    J -->|Yes| M[DataFrame Created]
    
    %% Data Quality Checks Phase
    M --> N[check_row_count()]
    M --> O[check_data_types()]
    M --> P[check_value_ranges()]
    
    %% Individual Check Processing
    N --> Q[Row Count Results]
    O -->|Schema Provided| R[Type Validation Results]
    O -->|No Schema| S[Skip Type Check]
    P -->|Rules Provided| T[Range Validation Results]
    P -->|No Rules| U[Skip Range Check]
    
    %% Results Aggregation
    Q --> V[Aggregate Check Results]
    R --> V
    S --> V
    T --> V
    U --> V
    L --> V
    
    %% Summary Calculation
    V --> W[Calculate Summary Statistics]
    W --> X[Generate Final Results]
    
    %% Frontend Display Processing
    X --> Y[format_results_summary()]
    X --> Z[get_detailed_issues()]
    
    %% UI Display Components
    Y --> AA[Summary Dashboard]
    Z --> BB[Detailed Issues View]
    X --> CC[Raw JSON Display]
    
    %% Summary Dashboard Elements
    AA --> DD[Row Count Metric]
    AA --> EE[Column Count Metric]
    AA --> FF[Checks Passed Metric]
    AA --> GG[Success Rate Metric]
    AA --> HH[Overall Status Badge]
    
    %% Detailed Issues Elements
    BB --> II[Row Count Issues]
    BB --> JJ[Data Type Mismatches]
    BB --> KK[Value Range Violations]
    BB --> LL[Missing Columns]
    
    %% Download Options
    Y --> MM[Download Summary TXT]
    X --> NN[Download Results JSON]
    
    %% Data Processing Details
    subgraph "Data Loader Module"
        I --> I1[File Existence Check]
        I1 --> I2[File Extension Validation]
        I2 --> I3[pandas.read_csv()]
        I3 --> I4[Empty DataFrame Check]
        I4 --> I5[Return DataFrame]
        I1 -->|Fail| I6[Raise CSVLoadError]
        I2 -->|Fail| I6
        I3 -->|Fail| I6
        I4 -->|Fail| I6
    end
    
    subgraph "Check Modules"
        N --> N1[Compare row count vs threshold]
        N1 --> N2[Generate row count result]
        
        O --> O1[Compare DataFrame dtypes vs schema]
        O1 --> O2[Identify type mismatches]
        O2 --> O3[Find missing columns]
        O3 --> O4[Generate type check result]
        
        P --> P1[Apply min/max range rules]
        P1 --> P2[Apply allowed values rules]
        P2 --> P3[Collect violations]
        P3 --> P4[Generate range check result]
    end
    
    subgraph "Results Processing"
        V --> V1[Count total checks]
        V1 --> V2[Count passed checks]
        V2 --> V3[Calculate success rate]
        V3 --> V4[Determine overall status]
    end
    
    %% Styling
    classDef inputNode fill:#e1f5fe
    classDef processNode fill:#f3e5f5
    classDef errorNode fill:#ffebee
    classDef resultNode fill:#e8f5e8
    classDef displayNode fill:#fff3e0
    
    class A,A1,A2,A3,B,B1,B2,B3 inputNode
    class C,D,E,F,H,I,M,N,O,P,V,W,X,Y,Z processNode
    class G,K,L,I6 errorNode
    class Q,R,T,AA,BB,CC,DD,EE,FF,GG,HH,II,JJ,KK,LL,MM,NN resultNode
    class S,U displayNode
```

## Data Flow Description

### 1. **Input Phase**
- User uploads CSV file through Streamlit interface
- User configures validation parameters (schema, rules, minimum rows)
- Configuration is parsed and validated

### 2. **Processing Phase**
- CSV file is temporarily stored and loaded via `data_loader.py`
- DataFrame undergoes three types of quality checks:
  - **Row Count**: Validates minimum row requirements
  - **Data Types**: Compares actual vs expected column types
  - **Value Ranges**: Validates numeric ranges and categorical values

### 3. **Results Phase**
- Individual check results are aggregated
- Summary statistics are calculated (pass/fail counts, success rate)
- Results are formatted for different display purposes

### 4. **Display Phase**
- **Summary Dashboard**: High-level metrics and status
- **Detailed View**: Specific violations and mismatches
- **Download Options**: Raw JSON and formatted summary

### 5. **Error Handling**
- File loading errors are caught and displayed
- Configuration validation prevents invalid inputs
- Each check module handles its own error cases

This flow ensures robust data validation with comprehensive user feedback and error handling at every stage.