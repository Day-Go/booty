"""
Mock Project Main Application
"""

import os
from flask import Flask, jsonify
from database.connection import get_db_connection
from services.user_service import UserService

app = Flask(__name__)

# Load configuration
app.config.from_pyfile('../config/app_config.py')

# Initialize services
user_service = UserService()

@app.route('/')
def index():
    """Root endpoint that returns a welcome message"""
    return jsonify({
        'message': 'Welcome to the Mock Project API',
        'version': '1.0.0'
    })

@app.route('/users')
def get_users():
    """Endpoint to retrieve all users"""
    users = user_service.get_all_users()
    return jsonify(users)

@app.route('/users/<int:user_id>')
def get_user(user_id):
    """Endpoint to retrieve a single user"""
    user = user_service.get_user_by_id(user_id)
    if user:
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    # Set up database connection before running
    conn = get_db_connection()
    print(f"Connected to database: {conn.engine.url}")
    
    # Start the Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)