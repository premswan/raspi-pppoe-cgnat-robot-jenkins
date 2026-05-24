#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

robot -d results \
  --variable RPI_HOST:192.168.1.2 \
  --variable RPI_USER:pi \
  --variable IFACE:eth0 \
  --variable CAPTURE_SECONDS:20 \
  --variable PACKET_COUNT:30 \
  tests/pppoe_cgnat_validation.robot
