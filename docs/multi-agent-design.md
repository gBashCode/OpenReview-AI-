# OpenReview AI — Multi-Agent Review Workflow Design

OpenReview AI employs an autonomous multi-agent pipeline modeled with LangGraph to perform deep, contextual code reviews while preventing hallucinations and noise.

---

## 1. Agent Topology & Pipeline Stages

```
                        [ Pull Request Diff ]
                                  │
                                  ▼
                     [ Diff Context Analyzer ]
                 (Extracts AST, symbols, hunks)
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  [ Security Agent ]    [ Performance Agent ]    [ Quality & Style Agent ]
  - OWASP Top 10        - Algorithmic Big-O      - Clean code principles
  - Secret scanning     - N+1 query detection    - Naming conventions
  - Injection vectors   - Memory leaks           - DRY & SOLID rules
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                      [ Quality Arbiter Agent ]
                      - Deduplicates findings
                      - Validates against AST
                      - Filters false positives
                      - Generates unified diff fixes
                                  │
                                  ▼
                     [ GitHub Comment Publisher ]
```

---

## 2. Specialized Roles

### 1. Diff Context Analyzer
- Converts raw unified diffs into file-by-file syntax trees.
- Queries `pgvector` store to retrieve relevant architectural conventions, guidelines, and historical PR reviews.

### 2. Security Agent
- Evaluates code for injection vulnerabilities, insecure deserialization, broken access control, missing rate limits, and credentials in code.
- Categorizes findings by severity: `info`, `warning`, `error`, `critical`.

### 3. Performance Agent
- Identifies unindexed joins, unbuffered file reads, unneeded re-computations, and slow queries.
- Suggests optimized algorithms or caching strategies.

### 4. Quality Arbiter
- Ensures that suggestions adhere to the project's formatting and conventions.
- Synthesizes an executive markdown summary with category scores (0.0 to 100.0).
- Generates precise, verified replacement patches formatted for GitHub suggestion blocks.
