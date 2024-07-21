import subprocess
import sys

# Function to install a package
def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# Install required packages if not already installed
try:
    import plotly.express as px
    import numpy as np
    import pandas as pd
except ImportError:
    install('plotly')
    import plotly.express as px
    import numpy as np
    import pandas as pd

# Generate sample data
np.random.seed(42)
time = np.arange(0, 100)
best_cost = np.exp(-0.05 * time) + np.random.normal(0, 0.02, size=time.shape)

# Create a DataFrame
data = pd.DataFrame({
    'Time': time,
    'Best Cost': best_cost
})

# Create an interactive line plot
fig = px.line(data, x='Time', y='Best Cost', title='Change in Best Cost Over Time',
              labels={'Time': 'Time', 'Best Cost': 'Best Cost'}, markers=True)

# Show the plot
fig.show()

