import subprocess
import sys
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.io as pio

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install required packages if not already installed
try:
    import pandas as pd
    import plotly.express as px
except ImportError:
    install('pandas')
    install('plotly')
    import pandas as pd
    import plotly.express as px

# Connect to SQLite database
print("Connecting to database...")
conn = sqlite3.connect('mydatabase_gaussian.db')

# Query the data with planner names
query = """
    SELECT REPLACE(plannerConfigs.name, 'geometric_', '') AS name, runs.*
    FROM plannerConfigs
    INNER JOIN runs ON plannerConfigs.id = runs.plannerid
"""
df = pd.read_sql_query(query, conn)

# Save DataFrame to CSV for further use
df.to_csv('your_data.csv', index=False)

# Close the connection
conn.close()

# Data Processing
# Load data from CSV
df = pd.read_csv('your_data.csv')

# Clean column names
df.columns = df.columns.str.strip()

# Define performance measure columns
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
    
    for planner_name in df['name'].unique():
        # Filter data for the current planner
        planner_data = df[df['name'] == planner_name]
        
        # Calculate average for each performance measure column
        avg_performance = planner_data[performance_columns].mean()
        
        # Add to the summary DataFrame
        avg_performance_df[planner_name] = avg_performance
    
    # Transpose for better readability
    avg_performance_df = avg_performance_df.T
    
    # Save the average performance measures to a new sheet
    avg_performance_df.to_excel(writer, sheet_name='Performance Averages')

    # Calculate percentage changes
    def calculate_percentage_change(df1, df2):
        return ((df2 - df1) / df1) * 100

    # Create a DataFrame for percentage changes
    percent_change_df = pd.DataFrame()
    planner_names = avg_performance_df.index

    # Create all pairwise comparisons
    for i, name1 in enumerate(planner_names):
        for j, name2 in enumerate(planner_names):
            if i < j:
                percent_change_df[f'{name1} vs {name2}'] = calculate_percentage_change(
                    avg_performance_df.loc[name1], avg_performance_df.loc[name2]
                )
    
    # Save the percentage change data to a new sheet
    percent_change_df.to_excel(writer, sheet_name='Percentage Changes')

print('Data, performance averages, and percentage changes have been exported to performance_summary.xlsx')

# Box Plots with Plotly
print("Creating colorful box plots with Plotly...")

# Define a color map for each planner
color_map = px.colors.qualitative.Plotly  # or use another color palette if desired

for column in performance_columns:
    fig = px.box(
        df, 
        x='name', 
        y=column, 
        color='name', 
        color_discrete_sequence=color_map, 
        title=f'Box Plot of {column} for Each Planner'
    )
    
    # Update layout for better readability
    fig.update_layout(
        xaxis_title='Planner Name',
        yaxis_title=column,
        xaxis=dict(tickmode='array', tickangle=45),
        title=dict(x=0.5)
    )
    
    # Save the plot as an image file
    image_filename = f'{column}_box_plot.png'
    fig.write_image(image_filename, scale=2)
    print(f'Saved box plot for {column} as {image_filename}')
    
    # Save the plot as an interactive HTML file
    html_filename = f'{column}_box_plot.html'
    fig.write_html(html_filename)
    print(f'Saved interactive box plot for {column} as {html_filename}')

print('Colorful box plots saved as images and HTML files.')

