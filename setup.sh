#!/bin/bash

# Golf Swing Analysis - Quick Start Script

echo "======================================"
echo "Golf Swing Analysis - Module 1 Setup"
echo "======================================"
echo ""

# Check if conda environment exists
if conda env list | grep -q "golfpose"; then
    echo "✓ Conda environment 'golfpose' found"
    echo "  Activating environment..."
    source activate golfpose
else
    echo "✗ Conda environment 'golfpose' not found"
    echo "  Please create it first:"
    echo "  conda create -n golfpose python=3.9"
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create output directory
echo ""
echo "Creating output directory..."
mkdir -p output
mkdir -p output/annotated_swings

# Run dataset analyzer
echo ""
echo "======================================"
echo "Step 1: Analyzing CaddieSet Dataset"
echo "======================================"
python dataset_analyzer.py

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. For LIVE pose analysis:"
echo "   python live_pose_analysis.py"
echo ""
echo "2. For swing sequence testing:"
echo "   python test_swing_phases.py"
echo ""
echo "Press any key to exit..."
read -n 1
