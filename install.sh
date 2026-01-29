#!/bin/bash
set -e

if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install it first."
    exit 1
fi

echo "Installing ana..."

chmod +x ana
sudo cp ana /usr/local/bin/ana

echo "✔ ana installed!"