#!/bin/bash

# Demonstration script for custom class differential testing
# This script runs both test functions and shows the output

echo "=========================================="
echo "Custom Class Differential Testing Demo"
echo "=========================================="
echo ""

echo "Test 1: find_closest_points"
echo "------------------------------------------"
python ../src/run_ab.py \
  --a a1.py \
  --b b1.py \
  --func find_closest_points \
  --max-examples 50 \
  --log INFO

echo ""
echo ""
echo "Test 2: calculate_centroid"
echo "------------------------------------------"
python ../src/run_ab.py \
  --a a1.py \
  --b b1.py \
  --func calculate_centroid \
  --max-examples 50 \
  --log INFO

echo ""
echo "=========================================="
echo "Tests Complete!"
echo "=========================================="
