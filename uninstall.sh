#!/bin/bash
set -e

echo "Uninstalling ana..."

sudo rm -f /usr/local/bin/ana

read -p "Do you want to keep your calendar data? [Y/n] " answer
if [[ "$answer" =~ ^[Nn]$ ]]; then
    rm -f ~/.ana.json
    echo "Calendar data deleted."
else
    echo "Calendar data kept."
fi

echo "✔ ana uninstalled!"
