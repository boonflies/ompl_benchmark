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

# Filter the DataFrame to only include rows where time is between 0 and 100
filtered_df = progress_df[(progress_df['time'] >= 0) & (progress_df['time'] <= 100)]

# Create 20 equally spaced intervals within the range of 0 to 100
intervals = np.linspace(0, 100, 21)  # 21 points to create 20 intervals

# Assign interval labels to each time point
filtered_df['interval'] = pd.cut(filtered_df['time'], bins=intervals, labels=False)

# Compute median best cost for each planner over these intervals
median_best_cost_df = filtered_df.groupby(['interval', 'name'])['best_cost'].median().reset_index()

# Map interval numbers to the start of the interval
interval_mapping = {i: int(intervals[i]) for i in range(len(intervals) - 1)}
median_best_cost_df['interval_label'] = median_best_cost_df['interval'].map(interval_mapping)

# Plotting
print("Creating median best cost plot for all planners...")
fig = px.line(
    median_best_cost_df, 
    x='interval_label', 
    y='best_cost', 
    color='name', 
    title='Best Cost vs Time', 
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

