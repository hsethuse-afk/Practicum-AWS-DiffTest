#!/bin/bash
# Batch script to run type inference on all test cases

echo 'Running differential tests...'
echo ''

for test_dir in diff_test_cases/*/; do
    if [ -f "$test_dir/before.py" ]; then
        test_id=$(basename "$test_dir")
        echo "Testing: $test_id"

        # Run on before version
        python -m righttyper "$test_dir/before.py" > "$test_dir/before_types.out" 2>&1

        # Run on after version
        python -m righttyper "$test_dir/after.py" > "$test_dir/after_types.out" 2>&1

        # Compare results
        if diff -q "$test_dir/before_types.out" "$test_dir/after_types.out" > /dev/null; then
            echo "  ✓ No difference in type inference"
        else
            echo "  ⚠ Type inference differs!"
            diff "$test_dir/before_types.out" "$test_dir/after_types.out" > "$test_dir/type_diff.txt"
        fi
        echo ''
    fi
done

echo 'All tests completed!'
