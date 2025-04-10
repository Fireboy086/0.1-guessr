# Python API for React App

This simple Flask API serves data from a Python file to your React application.

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the Flask API:
   ```
   python app.py
   ```

The API will run on http://localhost:5000.

## API Endpoints

- GET `/api/items` - Returns the list of items from data.py

## Customizing Data

Edit the `data.py` file to modify the list of items that will be served to your React app. 