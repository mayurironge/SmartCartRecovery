from sqlalchemy import text
from backend.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))

        print("Connected Successfully!")
        print(result.fetchone()[0])

except Exception as e:
    print("Connection Failed!")
    print(e)