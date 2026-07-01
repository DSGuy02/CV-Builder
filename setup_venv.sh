#!/usr/bin/env bash
# setup_venv.sh — Create and activate a Python virtual environment for cv_builder

set -e

VENV_DIR=".venv"

echo "Setting up virtual environment in '$VENV_DIR'..."
python3 -m venv "$VENV_DIR"

echo "Activating and installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r requirements.txt

echo ""
echo "Setup complete."
echo ""
echo "To activate the environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Then build your CV with:"
echo "  python cv_builder.py input/cv_template.md"
