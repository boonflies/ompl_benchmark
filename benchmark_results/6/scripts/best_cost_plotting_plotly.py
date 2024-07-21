import subprocess
import sys
import sqlite3
import pandas as pd
import plotly.express as px
from matplotlib.backends.backend_pdf import PdfPages

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

# Query the runs and progress data
print("Fetching data from database...")
runs_query = """
    SELECT REPLACE(plannerConfigs.name, 'geometric_', '') AS name, runs.*
    FROM plannerConfigs
    INNER JOIN runs ON plannerConfigs.id = runs.plannerid
"""
progress_query = """
    SELECT REPLACE(plannerConfigs.name, 'geometric_', '') AS name, progress.*
    FROM plannerConfigs
    INNER JOIN runs ON plannerConfigs.id = runs.plannerid
    INNER JOIN progress ON runs.id = progress.runid
"""

# Load data into DataFrames
runs_df = pd.read_sql_query(runs_query, conn)
progress_df = pd.read_sql_query(progress_query, conn)

# Close the connection
conn.close()

# Plotting
# Plot 1: Distribution of times per planner
print("Creating boxplot for distribution of times per planner...")
fig1 = px.box(runs_df, x='name', y='time', points="all", title='Distribution of Times per Planner')
fig1.update_layout(xaxis_title='Planner', yaxis_title='Time')

# Save boxplot as image and add to PDF
fig1.write_image("boxplot_times.png")
fig1.write_image("boxplot_times.pdf")

# Plot 2: Best Cost over Time for pairs of planners
print("Creating line plots for change in best cost over time for planner pairs...")
planner_pairs = [
    ('Planner1', 'Planner2'),
    ('Planner1', 'Planner3'),
    ('Planner2', 'Planner3')
]

# Save plots to a single PDF file
print("Saving plots to PDF...")
pdf_path = "plots.pdf"
with PdfPages(pdf_path) as pdf:
    for fig in [fig1]:
        fig.write_image(pdf, format='pdf')

    for planner1, planner2 in planner_pairs:
        filtered_df = progress_df[progress_df['name'].isin([planner1, planner2])]
        fig = px.line(filtered_df, x='time', y='best_cost', color='name', title=f'Change in Best Cost over Time: {planner1} vs {planner2}', line_shape='linear')
        fig.update_layout(xaxis_title='Time', yaxis_title='Best Cost')
        fig.write_image(f"best_cost_{planner1}_vs_{planner2}.png")
        fig.write_image(pdf, format='pdf')

print(f'Plots have been saved to {pdf_path}')

