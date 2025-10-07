#!/bin/bash
# Simple script to build Docker environment for differential testing

set -e

if [ $# -lt 2 ]; then
    echo "Usage: ./build_env.sh <file_a> <file_b>"
    echo "Example: ./build_env.sh src/testsample/a.py src/testsample/b.py"
    exit 1
fi

FILE_A="$1"
FILE_B="$2"

echo "=== Building Docker Environment ==="
echo "File A: $FILE_A"
echo "File B: $FILE_B"
echo ""

# Step 1: Scan and create requirements
echo "Step 1: Scanning dependencies..."
python3 src/dt/env_builder/simple_setup.py "$FILE_A" "$FILE_B"

# Step 2: Build Docker image
echo ""
echo "Step 2: Building Docker image..."
docker build -t difftest-env .

echo ""
echo "✓ Docker environment built successfully!"
echo ""
echo "Run tests with:"
echo "  docker run --rm -v \$(pwd)/src:/app/src difftest-env python /app/src/run_ab.py --a testsample/a.py --b testsample/b.py --func string_xor"
