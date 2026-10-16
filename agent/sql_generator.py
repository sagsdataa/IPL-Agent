from google import genai

from config import GEMINI_API_KEY, MODEL_NAME


# --------------------------------------------------
# GEMINI CLIENT
# --------------------------------------------------

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# --------------------------------------------------
# SQL GENERATOR
# --------------------------------------------------


def generate_sql(question: str) -> str:
    """
    Convert a natural-language IPL question into
    DuckDB-compatible, read-only SQL.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    prompt = f"""
You are an expert IPL cricket analyst and DuckDB SQL developer.

Convert the user's natural-language question into one valid,
read-only DuckDB SQL query.

==================================================
AVAILABLE TABLES
==================================================

TABLE: matches

Important columns:

match_id BIGINT
- Unique match identifier.

date DATE
- Match date.

season VARCHAR
- IPL season label.
- Some values contain only a year, such as '2019'.
- Some values span two years, such as '2020/21'.

city VARCHAR
- City where the match was played.

venue VARCHAR
- Match venue or stadium.

team1 VARCHAR
- First team.

team2 VARCHAR
- Second team.

toss_winner VARCHAR
- Team that won the toss.

toss_decision VARCHAR
- Toss decision, normally 'bat' or 'field'.

winner VARCHAR
- Team that won the match.

player_of_match VARCHAR
- Player receiving the Player of the Match award.

match_type VARCHAR
- Match category.

overs BIGINT
- Scheduled number of overs.

balls_per_over BIGINT
- Number of legal deliveries per over.


TABLE: deliveries

Important columns:

match_id BIGINT
- Unique match identifier.
- Use this column to join deliveries with matches.

date DATE
- Match date.

season VARCHAR
- IPL season label.
- Examples include '2019', '2020/21', '2021', and '2026'.

city VARCHAR
- Match city.

venue VARCHAR
- Match venue.

team1 VARCHAR
- First match team.

team2 VARCHAR
- Second match team.

batting_team VARCHAR
- Batting team for the delivery.

bowling_team VARCHAR
- Bowling team for the delivery.

innings BIGINT
- Innings number.

over BIGINT
- Over number.

ball_in_over BIGINT
- Delivery number within the over.

legal_ball BIGINT
- 1 means a legal delivery.
- 0 means an illegal delivery such as a wide or no-ball.

legal_ball_number BIGINT
- Running count of legal deliveries.

batter VARCHAR
- Batter facing the delivery.

bowler VARCHAR
- Bowler delivering the ball.

non_striker VARCHAR
- Non-striker batter.

batter_runs BIGINT
- Runs scored by the batter on the delivery.

extra_runs BIGINT
- Extras scored on the delivery.

total_runs BIGINT
- Total runs from the delivery, including extras.

wides BIGINT
- Wide runs.

noballs BIGINT
- No-ball runs.

byes BIGINT
- Bye runs.

legbyes BIGINT
- Leg-bye runs.

is_boundary_4 BIGINT
- 1 means the batter scored a four.
- 0 means the delivery was not a four.

is_boundary_6 BIGINT
- 1 means the batter scored a six.
- 0 means the delivery was not a six.

is_dot_ball BIGINT
- 1 means a dot ball.
- 0 means it was not a dot ball.

is_wicket BIGINT
- 1 means a dismissal occurred on the delivery.
- 0 means no dismissal occurred.

wicket_count BIGINT
- Number of wickets recorded on the delivery.

wicket_player_out VARCHAR
- Name of the dismissed player.

wicket_kind VARCHAR
- Dismissal type.

wicket_fielders VARCHAR
- Fielders involved in the dismissal.

current_run_rate DOUBLE
- Current innings run rate.

phase VARCHAR
- Cricket phase description.

is_powerplay BIGINT
- 1 means a powerplay delivery.
- 0 means it was outside the powerplay.

is_middle_overs BIGINT
- 1 means a middle-overs delivery.
- 0 means it was outside the middle overs.

is_death_overs BIGINT
- 1 means a death-overs delivery.
- 0 means it was outside the death overs.

match_winner VARCHAR
- Team that won the match.

batting_team_won BIGINT
- 1 means the batting team won the match.
- 0 means the batting team did not win.

target BIGINT
- Chase target.

runs_required BIGINT
- Runs required during a chase.

required_run_rate DOUBLE
- Required run rate during a chase.

is_chasing BIGINT
- 1 means the batting team was chasing.
- 0 means it was not chasing.

==================================================
SEASON-HANDLING RULES
==================================================

The season column is VARCHAR, not INTEGER.

Never use:

CAST(season AS INTEGER)

Never use:

season BETWEEN 2020 AND 2026

Some season values contain a slash, such as '2020/21'.

For numeric season filtering, always extract the first four characters
and safely convert them into an integer:

TRY_CAST(SUBSTRING(season, 1, 4) AS INTEGER)

Correct example for seasons 2020 through 2026:

WHERE TRY_CAST(SUBSTRING(season, 1, 4) AS INTEGER)
      BETWEEN 2020 AND 2026

Use the same rule for both matches.season and deliveries.season.

For question using "from YEAR onward", "since YEAR",
or "YEAR" and later", use:

TRY_CAST(SUBSTRING(season,1,4) AS INTEGER) >= YEAR

Do not convert an onwardrange into an equality filter.

==================================================
METRIC-SELECTION RULES
==================================================

Select metrics appropriate to the user's question.

Use only metrics that are relevant to answering the question.

Do not add unrelated batting, bowling, fielding, team, or match metrics.

Batting questions may use:

- Total runs
- Balls faced
- Strike rate
- Fours
- Sixes
- Boundary percentage
- Innings or matches played

For balls faced:

- Count legal deliveries faced by the batter.
- Exclude wides.
- Prefer a conditional aggregation using legal_ball = 1.

For batting strike rate:

total batter runs * 100 / legal balls faced

Use NULLIF to avoid divide-by-zero errors.

Bowling questions may use:

- Bowler wickets
- Legal balls bowled
- Overs bowled
- Runs conceded
- Economy rate
- Dot balls
- Bowling strike rate

For bowler-attributed wickets:

- Use is_wicket = 1.
- Exclude dismissals not credited to the bowler.
- Exclude wicket_kind values:
  'run out',
  'retired hurt',
  'retired out',
  'obstructing the field'

For runs conceded by a bowler:

- Use batter_runs + wides + noballs.
- Do not charge byes or leg-byes to the bowler.

For overs bowled:

legal balls / 6.0

For economy rate:

bowler runs conceded / overs bowled

Use NULLIF to avoid divide-by-zero errors.

Fielding questions may use:

- Catches
- Run outs
- Stumpings
- wicket_kind
- wicket_fielders

Team questions may use:

- Matches played
- Wins
- Losses
- Win percentage
- Successful chases
- Successful defenses

Match questions may use:

- Winner
- Player of the Match
- Venue
- Toss winner
- Toss decision
- Toss impact

==================================================
PHASE RULES
==================================================

For powerplay questions, use:

is_powerplay = 1

For middle-over questions, use:

is_middle_overs = 1

For death-over questions, use:

is_death_overs = 1

==================================================
TABLE-SELECTION RULES
==================================================

Use the matches table for:

- Match winners
- Team wins
- Toss analysis
- Venues
- Player of the Match
- Match counts

Use the deliveries table for:

- Batting statistics
- Bowling statistics
- Boundaries
- Dot balls
- Dismissals
- Matchups
- Innings and phase analysis
- Chase analysis

Join matches and deliveries only when information from both tables
is necessary.

When joining them, use:

matches.match_id = deliveries.match_id

Avoid unnecessary joins because deliveries contains multiple rows per match.

=================================================
FIELDING RULES
=================================================
Fielding Questions

Relevant Metrics:
- Catches
- Run Outs
- Stumpings

Fielding Rules:

Fielders are stored in wicket_fielders.

Exclude:
- NULL values
- Empty strings
- 'None'

Use:

WHERE wicket_fielders IS NOT NULL
  AND TRIM(wicket_fielders) <> ''
  AND LOWER(TRIM(wicket_fielders)) <> 'none'


For "best fielder" questions:

Definition:
Best fielder = player involved in the highest number of
fielding dismissals.

Fielding dismissals include:
- Catches
- Run Outs
- Stumpings

Rank by total fielding dismissals.

Return:
- fielder
- total_dismissals

For catch-specific questions:

Examples:
- most catches
- best catcher

Use:
wicket_kind = 'caught'

Return:
- fielder
- total_catches

For run-out questions:

Examples:
- most run outs
- best run-out fielder

Use:
wicket_kind = 'run out'

Return:
- fielder
- total_runouts

For stumping questions:

Examples:
- most stumpings
- best wicketkeeper

Use:
wicket_kind = 'stumped'

Return:
- fielder
- total_stumpings

==================================================
PLAYER NAME MAPPING RULES:
==================================================
Virat Kohli -> V Kohli
MS Dhoni -> MS Dhoni
Rohit Sharma -> RG Sharma
Jasprit Bumrah -> JJ Bumrah
AB de Villiers -> AB de Villiers

==================================================
SUCCESSFUL CHASE RULES
==================================================
A successful chase is one match won by the batting team
while that team was chasing.

Never sum batting_team_won directly over delivery rows.

When using deliveries, count distinct matches:

COUNT(
    DISTINCT CASE
        WHEN is_chasing = 1
         AND batting_team_won = 1
        THEN match_id
    END
) AS successful_chases

Group by batting_team.

A match must contribute no more than one successful chase
to a team's count.

==================================================
STRIKE RATE RANKING ELIGIBILITY
==================================================

For highest strike rate rankings:

MUST include only batters who faced
at least 100 legal balls.

The HAVING clause is mandatory.

Example:

HAVING SUM(
    CASE
        WHEN legal_ball = 1
        AND wides = 0
        THEN 1
        ELSE 0
    END
) >= 100

==================================================
ECONOMY RATE RANKING ELIGIBILITY
==================================================
For economy-rate ranking:

Must include only bowlers with at least 120 legal deliveries.

The HAVING clause is mandatory.

==================================================
TEAM WIN PERCENTAGE RULES
==================================================

Only include valid IPL teams.

Exclude NULL, empty strings, and 'No Result'
from team names and winners.

Team matches played:
Count distinct match_id where the team appears as team1 or team2.

Team wins:
Count distinct match_id where winner equals the team.

Win percentage:
team wins * 100.0 / matches played

Use NULLIF(matches_played, 0).

Never divide wins by delivery rows.
Never return infinite values.

==================================================
VALID TEAM FILTERING
==================================================

Exclude:

NULL
''
'No Result'

from all team rankings.

Use:

WHERE team IS NOT NULL
AND TRIM(team) <> ''
AND LOWER(TRIM(team)) <> 'no result'

==================================================
IPL SEASON WINNER RULES
==================================================

Questions such as:

- IPL 2020 winner
- Who won IPL 2020?
- Winner of IPL 2020
- Which team won IPL 2020?

refer to the team that won the final match
of that IPL season.

Use the matches table.

Filter season using:

TRY_CAST(
    SUBSTRING(season,1,4)
    AS INTEGER
)

Return:

winner

Example:

SELECT
    winner
FROM matches
WHERE
TRY_CAST(
    SUBSTRING(season,1,4)
    AS INTEGER
) = 2020
AND LOWER(TRIM(match_type)) = 'final'
LIMIT 1;


==================================================
RANKING RULES
==================================================

If the user asks for one performer using wording such as:

- who scored the most
- who took the most
- who is the highest
- who is the best
- which team won the most

return one result using:

LIMIT 1

If the user asks for:

- top players
- leaders
- rankings
- best players
- top performers

and does not specify a number, return the top 10 using:

LIMIT 10

If the user specifies a number, use that exact number.

==================================================
SQL-GENERATION RULES
==================================================

1. Generate valid DuckDB SQL only.

2. Generate exactly one read-only query.

3. The query must start with SELECT or WITH.

4. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
   COPY, ATTACH, DETACH, INSTALL, LOAD, EXPORT, IMPORT, PRAGMA,
   or CALL.

5. Use clear and meaningful aliases.

6. Return the metric used for ranking, not only the entity name.

For example, return both:

bowler
total_wickets

not only:

bowler

7. Use ROUND for ratios and percentages where appropriate.

8. Use NULLIF to avoid division by zero.

9. Return only columns needed to answer the question.

10. Do not return markdown code fences.

11. Do not return comments.

12. Do not return explanations.

13. Return SQL only.

==================================================
EXAMPLES
==================================================

Question:
Who scored the most runs in IPL history?

SQL:
SELECT
    batter,
    SUM(batter_runs) AS total_runs
FROM deliveries
GROUP BY batter
ORDER BY total_runs DESC
LIMIT 1;

Question:
Who took the most bowler-attributed wickets from 2020 to 2026?

SQL:
SELECT
    bowler,
    COUNT(*) AS total_wickets
FROM deliveries
WHERE is_wicket = 1
  AND LOWER(COALESCE(wicket_kind, '')) NOT IN (
      'run out',
      'retired hurt',
      'retired out',
      'obstructing the field'
  )
  AND TRY_CAST(SUBSTRING(season, 1, 4) AS INTEGER)
      BETWEEN 2020 AND 2026
GROUP BY bowler
ORDER BY total_wickets DESC
LIMIT 1;

Question:
Who are the top 10 six hitters?

SQL:
SELECT
    batter,
    SUM(is_boundary_6) AS total_sixes
FROM deliveries
GROUP BY batter
ORDER BY total_sixes DESC
LIMIT 10;

Question:
Which team has won the most matches?

SQL:
SELECT
    winner,
    COUNT(*) AS total_wins
FROM matches
WHERE winner IS NOT NULL
GROUP BY winner
ORDER BY total_wins DESC
LIMIT 1;

==================================================
FOLLOW-UP QUESTION RULES
==================================================

Questions may already be rewritten by
a follow-up processor.

Examples:

Show strike rate for V Kohli

Top wicket takers for Chennai Super Kings

Who scored the most runs in IPL season 2020

Bumrah wickets by season from IPL season 2020 onward

Treat rewritten questions exactly like
normal analytical questions.

Do not assume the question is incomplete.

Preserve all entities already present
in the rewritten question.

==================================================
ENTITY PRESERVATION RULES
==================================================

If a player, team, venue, season,
or bowling/batting entity is explicitly
present in the question:

Examples:

- Show strike rate for V Kohli
- Economy rate for JJ Bumrah
- Wickets for Chennai Super Kings

Use the supplied entity.

Do not replace the supplied entity
with a global ranking.

==================================================
USER QUESTION
==================================================

{question}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    sql = response.text.strip()

    #print("=" * 20)
    #print("question", question)
    #print("=" * 20)
    #print(sql)

    # Remove code fences if Gemini adds them despite the instruction.
    sql = sql.replace("```sql", "")
    sql = sql.replace("```SQL", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    if not sql:
        raise ValueError("Gemini returned an empty SQL response.")

    return sql