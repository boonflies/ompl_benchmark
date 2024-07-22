import subprocess
import sys
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install required packages if not already installed
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    install('pandas')
    install('matplotlib')
    install('seaborn')
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

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

# Box Plots
print("Creating colorful box plots for performance measures...")

# Set up the PDF file to save plots
pdf_filename = 'performance_box_plots.pdf'
with PdfPages(pdf_filename) as pdf:
    
    # Define a color palette with a color for each planner
    unique_planners = df['name'].unique()
    palette = sns.color_palette("husl", len(unique_planners))  # Use a color palette with distinct colors
    
    for column in performance_columns:
        plt.figure(figsize=(16, 10))  # Increased figure size for better readability
        sns.boxplot(data=df, x='name', y=column, palette=palette)
        plt.title(f'Box Plot of {column} for Each Planner')
        plt.xlabel('Planner Name')
        plt.ylabel(column)
        plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels and align them to the right
        
        # Save the plot to the PDF
        pdf.savefig()
        
        # Save the plot as an image file
        image_filename = f'{column}_box_plot.png'
        plt.savefig(image_filename, bbox_inches='tight')
        print(f'Saved box plot for {column} as {image_filename}')
        
        plt.close()

print(f'Box plots saved to {pdf_filename}')

