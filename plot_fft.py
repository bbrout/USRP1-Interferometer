import matplotlib.pyplot as plt
import numpy as np

# --- Constants
c = 299792.458  # speed of light in km/s

# --- Read frequency header (in Hz)
with open("fft.dat", "r") as f:
    header = f.readline().strip().split(",")
    freqs = np.array([float(x) for x in header[1:]])  # in Hz
    freqs = freqs / 1e6  # Convert to MHz

# --- Load data
data = np.loadtxt("fft.dat", delimiter=",", skiprows=1)

# --- Read central frequency f0 from file (in Hz), then convert to MHz
with open("freq.dat", "r") as f:
    f0 = float(f.readline().strip()) / 1e6  # Convert to MHz
print(f"[DEBUG] Central Frequency f0 = {f0:.6f} MHz")

# --- Plot
fig, ax1 = plt.subplots(figsize=(10, 8))

for i, row in enumerate(data):
    time = row[0]
    power = 10 * np.log10(row[1:] + 1e-12)
    offset = i * 0.1
    ax1.plot(freqs, power + offset, label=f"{time:.1f}s")

# Show legend for time labels
ax1.legend(loc='upper right', fontsize='small', title="Time (s)")

# Axis labels and title
ax1.set_xlabel(f"Delta Frequency (KHz) from Central Frequency: {f0} MHz")
ax1.set_ylabel("Relative Power (dB + offset)")
ax1.set_title("FFT Time Evolution")

xtick_freqs = ax1.get_xticks()  # These are absolute freqs in MHz
delta_freqs = (xtick_freqs - f0) * 1e9

print("[DEBUG] delta freqs (Hz):", delta_freqs)
print(f"[DEBUG] x-axis limits (MHz): {ax1.get_xlim()}")

ax1.set_xticklabels([f"{x:.3f}" for x in delta_freqs])

# Disable offset notation on x-axis (no +1.413e3 nonsense)
#ax1.ticklabel_format(useOffset=False, style='plain', axis='x')

ax1.grid(True)

# DO NOT ALTER BELOW THIS LINE **************************************************

# --- Add secondary axis with Δv (km/s)

delta_f = delta_freqs *1e-3   # Convert Hz to MHz
print("[DEBUG] deltaf =", delta_f)

delta_v = c * (delta_f / f0)  # km/s
print(f"[DEBUG] delta_v =", delta_v)

# --- Top axis
ax2 = ax1.secondary_xaxis('top')
ax2.set_xticks(xtick_freqs)
ax2.set_xticklabels([f"{v:.0f}" for v in delta_v])
ax2.set_xlabel("Δv (km/s)")

plt.tight_layout()
plt.show()

