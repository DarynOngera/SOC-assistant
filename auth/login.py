from flask import Flask, request, jsonify
import jwt
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Secret key to encode and decode JWT tokens
app.config['SECRET_KEY'] = 'your-secret-key'

# Load user credentials from users.json
with open('users.json', 'r') as f:
    users = json.load(f)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username] == password:
        # Create a JWT token
        token = jwt.encode({
            'user': username,
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }, app.config['SECRET_KEY'])
        return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5001)