#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <path_to_ui_file> <path_to_qss_file>"
    exit 1
fi

# Assign arguments to variables
UI_FILE="$1"
QSS_FILE="$2"

# Check if the UI file exists
if [ ! -f "$UI_FILE" ]; then
    echo "Error: UI file not found: $UI_FILE"
    exit 1
fi

# Check if the QSS file exists
if [ ! -f "$QSS_FILE" ]; then
    echo "Error: QSS file not found: $QSS_FILE"
    exit 1
fi

# Create a temporary Python script to apply the QSS and display the UI
TEMP_SCRIPT=$(mktemp)
cat <<EOF > "$TEMP_SCRIPT"
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6 import uic

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("$UI_FILE", self)  # Load the .ui file

        # Load and apply the QSS stylesheet
        with open("$QSS_FILE", "r") as f:
            self.setStyleSheet(f.read())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
EOF

# Run the temporary Python script
python3 "$TEMP_SCRIPT"

# Clean up temporary files
rm -f "$TEMP_SCRIPT"