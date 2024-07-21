import subprocess
import sys
import pandas as pd
import sqlite3

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install pandas and openpyxl if not already installed
try:
    import pandas as pd
    import openpyxl
except ImportError:
    install('pandas')
    install('openpyxl')
    import pandas as pd
    import openpyxl

# Connect to SQLite database
conn = sqlite3.connect('mydatabase_gaussian.db')

# Query the data
query = 'SELECT * FROM runs'

# Load data into a DataFrame
df = pd.read_sql_query(query, conn)

# Save DataFrame to CSV
df.to_csv('your_data.csv', index=False)

# Close the connection
conn.close()

# Data Processing

# Load data from CSV
df = pd.read_csv('your_data.csv')

# Print column names to verify
print("Columns in the CSV:", df.columns.tolist())

# Clean column names
df.columns = df.columns.str.strip()

# Print cleaned column names
print("Cleaned Columns in the CSV:", df.columns.tolist())

# Define the planner IDs and columns for performance measures
planner_ids = [1, 2, 3, 4, 5]
performance_columns = [
    'approximate_solution', 'best_cost', 'correct_solution', 'correct_solution_strict',
    'graph_motions', 'graph_states', 'iterations', 'memory', 'simplification_time',
    'simplified_correct_solution', 'simplified_correct_solution_strict',
    'simplified_solution_clearance', 'simplified_solution_length',
    'simplified_solution_segments', 'simplified_solution_smoothness',
    'solution_clearance', 'solution_difference', 'solution_length',
    'solution_segments', 'solution_smoothness', 'solved', 'status', 'time',
    'valid_segment_fraction'
]

# Create a new Excel writer object
with pd.ExcelWriter('performance_summary.xlsx', engine='openpyxl') as writer:
    
    # Create a sheet for the raw data
    df.to_excel(writer, sheet_name='Raw Data', index=False)
    
    # Create a DataFrame to store the average performance measures
    avg_performance_df = pd.DataFrame()
    
    for planner_id in planner_ids:
        # Filter data for the current planner
        planner_data = df[df['plannerid'] == planner_id]
        
        # Calculate average for each performance measure column
        avg_performance = planner_data[performance_columns].mean()
        
        # Add to the summary DataFrame
        avg_performance_df[f'Planner {planner_id}'] = avg_performance
    
    # Transpose for better readability
    avg_performance_df = avg_performance_df.T
    
    # Save the average performance measures to a new sheet
    avg_performance_df.to_excel(writer, sheet_name='Performance Averages')

    # Calculate percentage changes
    def calculate_percentage_change(df1, df2):
        return ((df2 - df1) / df1) * 100

    # Create a DataFrame for percentage changes
    percent_change_df = pd.DataFrame()

    # Comparison: Planner 1 vs Planner 2
    percent_change_df['Planner 1 vs Planner 2'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 1'], avg_performance_df.loc['Planner 2']
    )
    
    # Comparison: Planner 1 vs Planner 3
    percent_change_df['Planner 1 vs Planner 3'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 1'], avg_performance_df.loc['Planner 3']
    )
    
    # Comparison: Planner 1 vs Planner 4
    percent_change_df['Planner 1 vs Planner 4'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 1'], avg_performance_df.loc['Planner 4']
    )

    # Comparison: Planner 1 vs Planner 5
    percent_change_df['Planner 1 vs Planner 5'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 1'], avg_performance_df.loc['Planner 5']
    )
    
    # Comparison: Planner 2 vs Planner 3
    percent_change_df['Planner 2 vs Planner 3'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 2'], avg_performance_df.loc['Planner 3']
    )
    
    # Comparison: Planner 2 vs Planner 3
    percent_change_df['Planner 2 vs Planner 4'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 2'], avg_performance_df.loc['Planner 4']
    )
    
    # Comparison: Planner 2 vs Planner 5
    percent_change_df['Planner 2 vs Planner 3'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 2'], avg_performance_df.loc['Planner 5']
    )

    
    # Comparison: Planner 3 vs Planner 4
    percent_change_df['Planner 3 vs Planner 4'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 3'], avg_performance_df.loc['Planner 4']
    )

    
    # Comparison: Planner 3 vs Planner 5
    percent_change_df['Planner 3 vs Planner 5'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 3'], avg_performance_df.loc['Planner 5']
    )

    
    # Comparison: Planner 4 vs Planner 5
    percent_change_df['Planner 4 vs Planner 5'] = calculate_percentage_change(
        avg_performance_df.loc['Planner 4'], avg_performance_df.loc['Planner 5']
    )


    # Save the percentage change data to a new sheet
    percent_change_df.to_excel(writer, sheet_name='Percentage Changes')

print('Data, performance averages, and percentage changes have been exported to performance_summary.xlsx')

