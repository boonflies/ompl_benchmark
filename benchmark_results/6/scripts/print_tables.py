import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('mydatabase_uniform.db')

# Create a cursor object
cursor = conn.cursor()

# Execute SQL query to list tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

# Fetch all results
tables = cursor.fetchall()

# Print the list of tables
print("Tables in the database:")
for table in tables:
    print(table[0])

# Close the connection
conn.close()

