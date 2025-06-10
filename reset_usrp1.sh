#!/bin/bash
echo "[INFO] Resetting USRP1..."
echo "[INFO] Please manually unplug/replug the USB cable now."
read -p "[WAITING] Press Enter after plugging back in..."

echo "[INFO] Probing device to load firmware and FPGA..."
uhd_usrp_probe
