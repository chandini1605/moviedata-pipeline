import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database="movie_analytics"
    )

    if connection.is_connected():
        print("Successfully connected to MySQL!")

    connection.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:", error)