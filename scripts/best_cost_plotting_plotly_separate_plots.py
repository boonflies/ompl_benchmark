import subprocess
import sys
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from matplotlib.backends.backend_pdf import PdfPages
from plotly.io import write_image

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install required packages if not already installed
try:
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    install('pandas')
    install('plotly')
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px

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

# Plot 2: Best Cost over Time for all runs
print("Creating line plot for change in best cost over time...")
fig2 = px.line(progress_df, x='time', y='best_cost', color='name', title='Change in Best Cost over Time', line_shape='linear')
fig2.update_layout(xaxis_title='Time', yaxis_title='Best Cost')

# Save line plot as image and add to PDF
fig2.write_image("best_cost_over_time.png")
fig2.write_image("best_cost_over_time.pdf")

# Save plots to a single PDF file
print("Saving plots to PDF...")
pdf_path = "plots.pdf"
with PdfPages(pdf_path) as pdf:
    for fig in [fig1, fig2]:
        fig.write_image(pdf, format='pdf')

print(f'Plots have been saved to {pdf_path}')

