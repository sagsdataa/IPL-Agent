from agent.sql_generator import generate_sql

question = """
Who scored the most runs in IPL history?
"""

sql = generate_sql(question)

print(sql)