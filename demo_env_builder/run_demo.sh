#!/bin/bash
#
# Complete Demo - Environment Builder for Differential Testing
#

set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║        ENVIRONMENT BUILDER DEMO - Milestone 2                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Scan Dependencies
echo "Step 1: Scanning dependencies from code_a.py and code_b.py..."
echo "----------------------------------------------------------------"
python3 scan_dependencies.py code_a.py code_b.py requirements.txt
echo ""

# Step 2: Show requirements
echo "Step 2: Generated requirements.txt:"
echo "----------------------------------------------------------------"
cat requirements.txt
echo ""

# Step 3: Build Docker
echo "Step 3: Building Docker container with dependencies..."
echo "----------------------------------------------------------------"
sudo docker build -t difftest-demo .
echo ""
echo "✓ Docker image 'difftest-demo' built successfully!"
echo ""

# Step 4: Run differential tests
echo "Step 4: Running differential tests in Docker..."
echo "----------------------------------------------------------------"
sudo docker run --rm difftest-demo python test_differential.py

