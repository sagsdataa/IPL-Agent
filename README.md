# 🏏 IPL Historical Intelligence Agent

A conversational analytics application for exploring historical Indian Premier League data using natural-language questions. The application combines Gemini-based SQL generation, DuckDB analytics, structured conversation memory, query guardrails, player-dimension enrichment, and Plotly visualizations.

## Key Features

- Natural-language IPL analytics
- Read-only DuckDB SQL generation
- Multi-turn conversational context
- Metric, time, entity, and explanation follow-ups
- Player and team alias resolution
- Incomplete-query clarification
- Garbage and non-IPL input rejection
- Player-dimension analysis by batting hand, bowling style, role, and country
- Grounded insight generation with direct-answer fallback
- Interactive bar and line charts
- Downloadable supporting data
- SQL, result, context, answer, and hallucination validation
- Golden regression test suite

## Architecture

```text
User Question
      ↓
Input Cleaning and Acknowledgement Detection
      ↓
Relevance and Incomplete-Query Evaluation
      ↓
Routing Layer
      ├── Time Follow-Up Resolver
      ├── Metric Follow-Up Resolver
      ├── Entity Follow-Up Resolver
      ├── Explanation Follow-Up
      └── New Analytical Question
      ↓
Contextual Question Builder
      ↓
Gemini SQL Generator
      ↓
SQL Safety Validator
      ↓
Read-Only DuckDB Execution
      ↓
Result and Context Validation
      ↓
Grounded Insight Generation
      ↓
Conversation-State Update
      ↓
Answer + Chart + Data + Generated SQL
```

## Technology Stack

- **Frontend:** Streamlit
- **Language:** Python
- **LLM:** Gemini
- **Analytics database:** DuckDB
- **Visualization:** Plotly
- **Data:** IPL matches, deliveries, and player dimension

## Conversational Routing

The routing layer identifies how every message should be processed.

### New Analytical Question

```text
Who scored the most runs in IPL?
```

The application generates validated SQL, executes it in DuckDB, and returns an answer with supporting data.

### Metric Follow-Up

```text
Who scored the most runs in IPL?
Strike rate?
```

Rewritten question:

```text
Show the strike rate for V Kohli?
```

### Time Follow-Up

```text
Who scored the most runs in IPL?
In 2020?
```

Rewritten question:

```text
Who scored the most runs in IPL season 2020?
```

### Entity Follow-Up

```text
Top 10 wicket takers
For CSK?
```

Rewritten question:

```text
Top 10 wicket takers for Chennai Super Kings
```

### Explanation Follow-Up

```text
Who scored the most runs in IPL?
Why?
```

The application reuses the previous answer, result, SQL, and context to generate an explanation.

### Incomplete Query

```text
Dhoni
```

The application recognizes `MS Dhoni` and asks which analysis the user wants to perform.

### Garbage Rejection

```text
erdfg 54 d
```

The application rejects the input without generating SQL or reusing previous analytical context.

## Conversation State

The application stores structured context from the latest successful analysis.

```python
{
    "last_question": None,
    "intent": None,
    "metric": None,
    "player": None,
    "team": None,
    "season": None,
    "venue": None,
    "phase": None,
    "primary_entity": None
}
```

The state is rebuilt after every successful analysis so stale filters do not leak into unrelated questions.

Example:

```text
Top 10 wicket takers
For CSK?
Who scored the most runs in IPL?
```

After the final question, the previous CSK filter is cleared and the state changes to `player = V Kohli` and `team = None`.

## Entity Resolution

The entity resolver converts aliases, abbreviations, and selected misspellings into canonical database values.

### Player Examples

```text
Kohli   → V Kohli
Kholi   → V Kohli
Dhoni   → MS Dhoni
ZA Khan → Z Khan
Bumrah  → JJ Bumrah
```

### Team Examples

```text
CSK → Chennai Super Kings
MI  → Mumbai Indians
RCB → Royal Challengers Bangalore
```

Canonical resolution ensures generated SQL uses values that match the DuckDB data.

## Player Dimension

The `player_dimension` table enriches ball-by-ball analytics with descriptive player attributes.

### Schema

```text
player_name
country
batting_hand
bowling_style
role
```

### Join Rules

For batting attributes:

```sql
deliveries.batter = player_dimension.player_name
```

For bowling attributes:

```sql
deliveries.bowler = player_dimension.player_name
```

### Supported Attribute Analysis

- Left-hand and right-hand batting
- Legbreak and offbreak bowling
- Left-arm orthodox and chinaman bowling
- Fast, medium-fast, and medium pace bowling
- Batter, bowler, allrounder, and wicketkeeper roles
- Indian, overseas, and country-specific analysis

### Bowling-Style Mappings

```text
Leg spinner:
LOWER(bowling_style) LIKE '%legbreak%'

Off spinner:
LOWER(bowling_style) LIKE '%offbreak%'

Left-arm orthodox:
LOWER(bowling_style) LIKE '%orthodox%'

Chinaman / left-arm wrist spin:
LOWER(bowling_style) LIKE '%chinaman%'
```

Left-arm pace analysis includes values such as:

```text
Left-arm medium
Left-arm medium-fast
Left-arm fast-medium
Left-arm Fast
```

It excludes orthodox and chinaman spin styles.

### Example Dimension Questions

```text
Best left-handed batters in IPL history
Most wickets by leg spinners
Best off spinners in IPL history
Most wickets by left-arm pacers
Top wicketkeeper batters
Top allrounders since 2020
Most runs by overseas players
Most wickets by Australian bowlers
```

## Analytics and Business Rules

The SQL generator uses explicit analytical definitions.

- Successful chases are counted once per distinct match, not once per delivery.
- Team win percentage uses match-level wins divided by matches played.
- Bowler-attributed wickets exclude dismissals such as run outs.
- Season filters use the first four characters of VARCHAR values such as `2020/21`.
- Strike-rate and economy rankings use minimum-workload eligibility rules.
- IPL season winners are identified using the winner of the latest dated match because the source dataset does not contain playoff-stage labels.
- Team and player rankings exclude null or invalid values where applicable.

## Guardrails

- Only one read-only `SELECT` or `WITH` query is allowed.
- Data-changing statements such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, and `CREATE` are blocked.
- Generated SQL is validated before execution.
- Query results are validated before insight generation.
- Context and answer validators check the analytical response structure.
- A hallucination checker compares generated narrative with retrieved context.
- A direct-answer fallback is used when narrative generation is unavailable.

## Golden Test Suite

The application is validated using a structured regression suite.

### Coverage

- New analytical questions
- Garbage rejection
- Incomplete-query detection
- Metric follow-ups
- Time and season follow-ups
- Entity follow-ups
- Explanation follow-ups
- Context reset validation
- SQL guardrails
- Winner queries
- Chart generation
- Player-dimension questions

### Representative Tests

```text
Who scored the most runs in IPL?
Top 10 wicket takers
Who won IPL 2020?
Best economy rate in IPL history
Most Player of the Match awards
Which venue hosted the most matches?
```

```text
Who scored the most runs in IPL?
Strike rate?
```

```text
Who scored the most runs in IPL?
In 2020?
```

```text
Top 10 wicket takers
For RCB?
```

```text
Who scored the most runs in IPL?
Why?
```

### Pass Criteria

- No stack traces during the regression suite
- Correct router selected for every test
- Garbage input never reuses previous context
- New standalone questions clear stale filters
- SQL remains read-only and uses the correct data grain
- Follow-up questions preserve the correct entity, metric, team, and season
- Charts match the returned result structure
- Narrative values remain grounded in query results

## Sample Questions

```text
Who scored the most runs in IPL history?
Top 10 wicket takers
Who won IPL 2020?
Which team has won the most matches?
Best leg spinners in IPL history
Most wickets by left-arm pacers
Top overseas allrounders
Best wicketkeeper batters
Most runs by left-handed batters
Most wickets by Australian players
```

## Project Structure

```text
IPL-Agent/
├── app.py
├── config.py
├── ipl.db
├── player_dimension.csv
├── agent/
│   ├── sql_generator.py
│   ├── insight_generator.py
│   ├── context_builder.py
│   ├── conversation_state.py
│   ├── entity_resolver.py
│   ├── metric_resolver.py
│   ├── time_resolver.py
│   ├── context_continuation_resolver.py
│   └── chart_generator.py
├── guardrails/
│   ├── relevance_validator.py
│   ├── sql_validator.py
│   ├── result_validator.py
│   ├── context_validator.py
│   ├── answer_validator.py
│   └── hallucination_checker.py
└── database/
    └── query_executor.py
```

## Run Locally

Activate the project virtual environment and start Streamlit:

```bash
python -m streamlit run app.py
```

Ensure the following are available in the project directory:

```text
ipl.db
player_dimension.csv
```

The Gemini API key and model name must be configured in `config.py` or through environment variables according to the project configuration.

## V1 Status

- Conversational analytics engine: complete
- Metric follow-ups: complete
- Time follow-ups: complete
- Entity follow-ups: complete
- Explanation follow-ups: complete
- Context reset: complete
- Player dimension: complete
- SQL guardrails: complete
- Charts and downloads: complete
- Golden regression suite: validated

## V2 Roadmap

The next planned capability is a Knowledge/RAG Agent for questions that are not stored in the structured analytics database.

Planned knowledge areas:

- Player biographies
- IPL rules and regulations
- Powerplay rules
- Impact Player rule
- Orange Cap and Purple Cap
- DLS method
- Team histories

Future hybrid architecture:

```text
User Question
      ↓
Capability Router
      ├── DuckDB Analytics Agent
      ├── Knowledge/RAG Agent
      └── Hybrid Response Composer
```

Example hybrid question:

```text
Tell me about MS Dhoni and show his IPL statistics.
```

The Knowledge Agent can retrieve biography content while the Analytics Agent calculates structured IPL statistics.

## Documentation

Detailed V1 technical documentation is included in:

```text
IPL_Historical_Intelligence_Agent_V1_Documentation.docx
```

## Author

**Sagir Mohd**

Global Lead Data Analyst focused on analytics, data transformation, Microsoft Fabric, Power BI, and practical AI-enabled decision-support solutions.
