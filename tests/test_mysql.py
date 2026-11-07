import mysql.connector

try:
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Chandini@123",
        database="movie_analytics"
    )

    if connection.is_connected():
        print("Successfully connected to MySQL!")
        print("Database: movie_analytics")

    connection.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:", error)