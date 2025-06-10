import matplotlib.pyplot as plt
import numpy as np

# Load the data
data = np.loadtxt("power.dat")

# Split into time and power
time = data[:, 0]
power = data[:, 1]

# Plot
plt.figure(figsize=(10, 5))
plt.plot(time, power, label="Power")

# Reverse the x-axis: t_max to 0
plt.gca().invert_xaxis()

plt.xlabel("Time (s)")
plt.ylabel("Power")
plt.title("Power vs. Time (Reversed Time Axis)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

