from src.load import create_connection

connection = create_connection()

if connection:
    print("Database connection test passed!")
    connection.close()