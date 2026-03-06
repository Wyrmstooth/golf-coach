#!/bin/bash
# Launch Golf Coach Streamlit App

echo "🏌️ Starting Golf Coach Pro..."
echo ""
conda run -n golfpose streamlit run golf_coach_app.py
