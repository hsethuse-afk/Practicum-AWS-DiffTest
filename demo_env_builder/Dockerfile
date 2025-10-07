FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install hypothesis for testing
RUN pip install hypothesis

# Copy all necessary files
COPY code_a.py code_b.py test_differential.py ./

CMD ["/bin/bash"]
