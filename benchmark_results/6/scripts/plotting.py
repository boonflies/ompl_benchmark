import subprocess
import sys
import sqlite3
import pandas as pd
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
sns.set(style="whitegrid")

# Plot 1: Distribution of times per planner
print("Creating boxplot for distribution of times per planner...")
plt.figure(figsize=(10, 6))
sns.boxplot(x='name', y='time', hue='name', data=runs_df, palette='Set3', legend=False)
sns.stripplot(x='name', y='time', data=runs_df, color='0.3', jitter=True)
plt.title('Distribution of Times per Planner')
plt.xlabel('Planner')
plt.ylabel('Time')
plt.xticks(rotation=45)
plt.savefig('boxplot_times.pdf')

# Plot 2: Best Cost over Time for all runs
print("Creating line plot for change in best cost over time...")
plt.figure(figsize=(10, 6))
sns.lineplot(x='time', y='best_cost', hue='name', data=progress_df, alpha=0.5)
plt.title('Change in Best Cost over Time')
plt.xlabel('Time')
plt.ylabel('Best Cost')
plt.legend(title='Planner')
plt.savefig('best_cost_over_time.pdf')

# Save plots to a single PDF file
print("Saving plots to PDF...")
with PdfPages('plots.pdf') as pdf:
    for plt in [plt.figure(i) for i in plt.get_fignums()]:
        pdf.savefig(plt)

print('Plots have been saved to plots.pdf')

