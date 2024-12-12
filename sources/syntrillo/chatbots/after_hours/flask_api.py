from flask import Flask, request, jsonify
from bedrock_operations import process_query
from dotenv import load_dotenv
from flask_cors import CORS
from models import db, Messages
import pymysql
import os


# Load environment variables from the .env file
load_dotenv()

# Configure your Flask application
app = Flask(__name__)
CORS(app)

# Get database credentials from environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'syntrillo$ChatbotsInformation')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Register your SQLAlchemy instance with your Flask app
db.init_app(app)

with app.app_context():
    db.create_all() 


@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query', '')
    model = data.get('model', 'claude-3-sonnet')  # Default to Claude 3 Sonnet if not specified
    user_id = data.get('user_id')
    session_id = data.get('session_id')

    if not query:
        return jsonify({"error": "Query is required"}), 400
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    if not session_id:
        return jsonify({"error": "Session ID is required"}), 400

    if model not in ['claude-3-sonnet', 'claude-3-5-sonnet']:
        return jsonify({"error": "Invalid model specified. Choose 'claude-3-sonnet' or 'claude-3-5-sonnet'"}), 400
    try:
        answer = process_query(query, model, user_id, session_id)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
