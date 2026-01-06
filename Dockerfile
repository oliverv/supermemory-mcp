FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Make server executable
RUN chmod +x server.py

# Run the MCP server
CMD ["python", "server.py"]
