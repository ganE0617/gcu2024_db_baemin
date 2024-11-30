#!/bin/bash

# Start code-server in the background
code-server --bind-addr 0.0.0.0:80 --auth none &

# Start the Python application
python3 /app/app.py