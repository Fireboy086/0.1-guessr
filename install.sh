#!/bin/bash

# Installation script for Spotify Guessing Game CLI

echo "Installing Spotify Guessing Game CLI..."

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 not found. Please install Python3 and pip3."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Create credentials if needed
if [ ! -f credentials.ini ]; then
    echo "No credentials.ini found. You'll need to set up Spotify credentials when you run the game."
fi

# Make the main script executable
chmod +x spotify_guessr.py

echo "Installation complete! Run the game with: python3 spotify_guessr.py" 