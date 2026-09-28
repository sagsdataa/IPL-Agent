
from agent.context_builder import build_context
from agent.sql_generator import generate_sql
from database.query_executor import run_query

question = "Compare Virat Kohli and Rohit Sharma?"


sql = generate_sql(question)
print(sql)
#----------------------------------

result = run_query(sql)

context = build_context(
    question,
    result
)
print(context)