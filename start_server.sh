#!/bin/bash

# Navigate to the project directory
cd /home/ubuntu/ai_receptionist

# Activate the virtual environment
source venv/bin/activate

# Run the FastAPI server using uvicorn in the background
# We use --host 0.0.0.0 to make it accessible from the internet
# We use --port 443 and enable SSL with the Cloudflare Origin certificates
nohup uvicorn main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem > server.log 2>&1 &

echo "Server is starting in the background..."
echo "Logs are being written to server.log"
echo "You can check the status using: ps aux | grep uvicorn"
