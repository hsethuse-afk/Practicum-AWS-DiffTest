# Demo Summary - How To Run

## Complete Clean Implementation ✅

Everything you need is in `demo_env_builder/` directory.

## Files Created

```
demo_env_builder/
├── code_a.py              ← Original version (numpy + pandas)
├── code_b.py              ← Refactored version (with changes)
├── scan_dependencies.py   ← Scans code, creates requirements.txt
├── Dockerfile             ← Docker setup
├── test_differential.py   ← Runs differential tests
├── run_demo.sh            ← COMPLETE AUTOMATED DEMO
└── README.md              ← Full documentation
```

## How To Run (2 Options)

### Option 1: Full Automated Demo (Recommended)

```bash
cd demo_env_builder
./run_demo.sh
```

**That's it!** It will:
1. Scan dependencies from code_a.py and code_b.py
2. Create requirements.txt (numpy, pandas)
3. Build Docker image with dependencies
4. Run differential tests in Docker
5. Show behavioral differences

### Option 2: Step by Step

```bash
cd demo_env_builder

# Step 1: Scan dependencies
python3 scan_dependencies.py code_a.py code_b.py

# Step 2: Build Docker
docker build -t difftest-demo .

# Step 3: Run tests
docker run --rm difftest-demo python test_differential.py
```

## What You'll See

```
Found imports: ['datetime', 'numpy', 'pandas']
Third-party packages: ['numpy', 'pandas']
✓ Created requirements.txt

Docker image 'difftest-demo' built successfully!

Test Function: analyze_sales_data
  Test 1: ✗ DIFF
    A: {..., 'high_value_items': 2}
    B: {..., 'high_value_items': 1, 'median_value': 600}

Result: Shows behavioral differences!
```

## SOW Alignment

✅ Automated dependency scanning  
✅ Docker-based isolation  
✅ Requirements.txt generation  
✅ Differential testing  
✅ Works with real packages (numpy, pandas)  

**Milestone 2 requirements achieved!**

## Key Points

- ✅ **Standalone** - Completely separate from main codebase
- ✅ **Simple** - Clean, focused implementation
- ✅ **Automated** - One command runs everything
- ✅ **Containerized** - Fully Docker-based
- ✅ **Real dependencies** - Actual third-party packages
- ✅ **Shows differences** - Detects behavioral changes

## To Run The Demo

Just do:
```bash
cd /home/intern/Practicum/Practicum-AWS-DiffTest/demo_env_builder
./run_demo.sh
```

