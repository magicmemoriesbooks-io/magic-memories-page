#!/bin/bash
echo "Post-merge setup: checking dependencies..."
pip install -q -r requirements.txt 2>/dev/null || true
echo "Post-merge setup complete."
