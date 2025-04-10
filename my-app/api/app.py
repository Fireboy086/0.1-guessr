from flask import Flask, jsonify
from flask_cors import CORS
from data import items

app = Flask(__name__)
# Configure CORS to allow requests from any origin
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify(items)

# Adding a simple health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "API is running"})

if __name__ == '__main__':
    # Running on 0.0.0.0 makes it accessible from other devices on the network
    # Using port 5001 to avoid conflicts with AirPlay on macOS (port 5000)
    app.run(debug=True, host='0.0.0.0', port=5001) 