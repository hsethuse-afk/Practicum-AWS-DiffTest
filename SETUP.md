# Environment Builder - Docker Setup

## Goal

**Build isolated Docker container → Scan dependencies → Install packages → Run tests**

This is for **containerized testing** as per SOW Milestone 2.

---

## Fix Docker Permissions First

The "permission denied" error happens because your user can't access Docker. Fix it:

```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Apply the change (logout/login or run):
newgrp docker

# Test Docker works
docker ps
```

---

## Build Docker Environment

### Option 1: Using the Script (Easiest)

```bash
cd /home/intern/Practicum/Practicum-AWS-DiffTest
./build_env.sh src/testsample/a.py src/testsample/b.py
```

This does everything automatically.

### Option 2: Manual Steps

```bash
cd /home/intern/Practicum/Practicum-AWS-DiffTest

# Step 1: Scan and create requirements
python3 src/dt/env_builder/simple_setup.py src/testsample/a.py src/testsample/b.py

# Step 2: Build Docker
docker build -t difftest-env .
```

---

## Run Tests in Docker

```bash
docker run --rm -v $(pwd)/src:/app/src difftest-env \
  python /app/src/run_ab.py --a testsample/a.py --b testsample/b.py --func string_xor
```

---

## What Gets Built

1. **requirements_env.txt** - Auto-generated with all dependencies
2. **Docker image** `difftest-env` - Contains:
   - Python 3.11
   - All packages from requirements_env.txt
   - Your source code
   - Ready to run tests

---

## For Your Own Files

```bash
# Build environment
./build_env.sh path/to/your/a.py path/to/your/b.py

# Run tests
docker run --rm -v $(pwd)/src:/app/src difftest-env \
  python /app/src/run_ab.py --a your/a.py --b your/b.py --func your_function
```

---

## Troubleshooting

### "permission denied" when running docker

**Problem:** User not in docker group

**Fix:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "non-zero code: 1" during build

**Problem:** Missing packages or syntax error in requirements

**Fix:** Check `requirements_env.txt` - make sure all packages are valid

### Can't find Docker

**Problem:** Docker not installed

**Fix:**
```bash
sudo apt update
sudo apt install docker.io
sudo systemctl start docker
```

---

## Summary

**Three commands total:**

1. Fix Docker permissions (one time):
   ```bash
   sudo usermod -aG docker $USER && newgrp docker
   ```

2. Build environment:
   ```bash
   ./build_env.sh src/testsample/a.py src/testsample/b.py
   ```

3. Run tests:
   ```bash
   docker run --rm -v $(pwd)/src:/app/src difftest-env python /app/src/run_ab.py --a testsample/a.py --b testsample/b.py --func string_xor
   ```

**Everything runs in Docker. Fully containerized.**
