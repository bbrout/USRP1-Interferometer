#!/bin/bash
# load_4rx_fpga.sh
# Load the 4RX FPGA image onto the USRP1 device

FPGA_IMAGE_PATH="${1:-./usrp1_fpga_4rx.rbf}"

if [ ! -f "$FPGA_IMAGE_PATH" ]; then
    echo "Error: FPGA image not found at $FPGA_IMAGE_PATH"
    exit 1
fi

echo "Loading FPGA image from: $FPGA_IMAGE_PATH"

uhd_usrp_probe --args="type=usrp1,fpga=$FPGA_IMAGE_PATH"

if [ $? -eq 0 ]; then
    echo "FPGA image loaded successfully."
else
    echo "Failed to load FPGA image."
    exit 1
fi
