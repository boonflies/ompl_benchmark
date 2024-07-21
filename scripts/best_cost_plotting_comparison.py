import subprocess
import sys
import sqlite3
import pandas as pd
import plotly.express as px
from plotly.io import write_image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
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

# Print the first few rows of progress_df for debugging
print("First few rows of progress_df:")
print(progress_df.head())

# Define planner pairs
planner_pairs = [(1, 2), (2, 3), (3, 4), (4, 5)]

# Function to create and save line plot for given planner pair
def plot_best_cost_comparison(planner1, planner2, data, filename):
    # Determine the range of runid for each planner
    start1, end1 = (planner1 - 1) * 25 + 1, planner1 * 25
    start2, end2 = (planner2 - 1) * 25 + 1, planner2 * 25
    
    # Filter data for the two planners
    df_pair = data[(data['runid'].between(start1, end1)) | (data['runid'].between(start2, end2))]
    
    if df_pair.empty:
        print(f"No data for planner pair {planner1} vs {planner2}")
        return

    # Plotting
    fig = px.line(df_pair, x='time', y='best_cost', color='name', title=f'Best Cost over Time: Planner {planner1} vs Planner {planner2}', line_shape='linear')
    fig.update_layout(xaxis_title='Time', yaxis_title='Best Cost')
    fig.write_image(filename)
    print(f"Saved plot for planner pair {planner1} vs {planner2} as {filename}")

# Plot for each pair and save images
print("Creating line plots for planner pairs...")
image_files = []
for planner1, planner2 in planner_pairs:
    filename = f"best_cost_{planner1}_vs_{planner2}.png"
    plot_best_cost_comparison(planner1, planner2, progress_df, filename)
    image_files.append(filename)

# Save all plots to a single PDF file
print("Saving plots to PDF...")
pdf_path = "plots.pdf"
with PdfPages(pdf_path) as pdf:
    for img_file in image_files:
        img = mpimg.imread(img_file)
        plt.figure()
        plt.imshow(img)
        plt.axis('off')
        pdf.savefig()
        plt.close()
        print(f"Added {img_file} to PDF")

print(f'Plots have been saved to {pdf_path}')

