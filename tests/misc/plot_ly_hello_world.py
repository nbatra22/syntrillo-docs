import kaleido
import plotly

print(plotly.__version__)
print(kaleido.__version__)

import numpy as np
import plotly.graph_objects as go

# Generate data
x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

# Create plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Sin(x)'))

# Update layout
fig.update_layout(title='Sinusoidal Curve', xaxis_title='x', yaxis_title='Sin(x)')

# Save plot as JPG
fig.write_image("ignore__sinusoidal_curve.jpg", format='jpg')



