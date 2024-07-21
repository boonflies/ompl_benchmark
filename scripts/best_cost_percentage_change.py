import subprocess
import sys
import sqlite3
import pandas as pd
import plotly.express as px
from plotly.io import write_image
import numpy as np

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

# Ensure kaleido is installed for image export
try:
    import kaleido
except ImportError:
    install('kaleido')

# Connect to SQLite database
print("Connecting to database...")
conn = sqlite3.connect('mydatabase_gaussian.db')

# Query the progress data
print("Fetching data from database...")
progress_query = """
    SELECT REPLACE(plannerConfigs.name, 'geometric_', '') AS name, progress.*
    FROM plannerConfigs
    INNER JOIN runs ON plannerConfigs.id = runs.plannerid
    INNER JOIN progress ON runs.id = progress.runid
"""

# Load data into DataFrame
progress_df = pd.read_sql_query(progress_query, conn)

# Close the connection
conn.close()

# Print the first few rows of progress_df for debugging
print("First few rows of progress_df:")
print(progress_df.head())

# Create 20 equally spaced intervals within the range of 0 to 100
intervals = np.linspace(0, 100, 21)  # 21 points to create 20 intervals

# Assign interval labels to each time point
progress_df['interval'] = pd.cut(progress_df['time'], bins=intervals, labels=False)

# Compute median best cost for each planner over these intervals
median_best_cost_df = progress_df.groupby(['interval', 'name'])['best_cost'].median().reset_index()

# Map interval numbers to the start of the interval
interval_mapping = {i: int(intervals[i]) for i in range(len(intervals) - 1)}
median_best_cost_df['interval_label'] = median_best_cost_df['interval'].map(interval_mapping)

# Calculate percentage change in best cost over intervals
percentage_change_df = median_best_cost_df.copy()
percentage_change_df.sort_values(by=['name', 'interval'], inplace=True)
percentage_change_df['best_cost_change'] = percentage_change_df.groupby('name')['best_cost'].pct_change() * 100
percentage_change_df['best_cost_change'].fillna(0, inplace=True)  # Replace NaN values with 0

# Save all data to an Excel file
with pd.ExcelWriter('best_cost_analysis.xlsx') as writer:
    # Sheet 1: Complete best cost info
    progress_df.to_excel(writer, sheet_name='Complete_Best_Cost_Info', index=False)
    
    # Sheet 2: Median best cost for 20 intervals
    median_best_cost_df.to_excel(writer, sheet_name='Median_Best_Cost_By_Interval', index=False)
    
    # Sheet 3: Percentage change in best cost over time
    percentage_change_df.to_excel(writer, sheet_name='Percentage_Change_Best_Cost', index=False)

print("Saved best cost analysis to best_cost_analysis.xlsx")

# Plotting
print("Creating median best cost plot for all planners...")
fig = px.line(
    median_best_cost_df, 
    x='interval_label', 
    y='best_cost', 
    color='name', 
    title='Median Best Cost over Time for All Planners (20 Intervals)', 
    line_shape='linear'
)
fig.update_layout(
    xaxis_title='Time Interval', 
    yaxis_title='Best Cost',
    xaxis=dict(tickmode='array', tickvals=list(interval_mapping.values()), ticktext=[str(val) for val in interval_mapping.values()])
)

# Save plot as image and PDF
fig.write_image("median_best_cost_over_time.png")
fig.write_image("median_best_cost_over_time.pdf")

print("Saved median best cost plot to median_best_cost_over_time.pdf")
