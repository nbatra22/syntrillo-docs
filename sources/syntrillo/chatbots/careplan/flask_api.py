from flask import Flask, request, jsonify
from bedrock_operations import get_final_answer

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.json
    query = data.get('query', '')
    model = data.get('model', 'claude-3-sonnet')  # Default to Claude 3 Sonnet if not specified

    if not query:
        return jsonify({"error": "Query is required"}), 400

    if model not in ['claude-3-sonnet', 'claude-3-5-sonnet']:
        return jsonify({"error": "Invalid model specified. Choose 'claude-3-sonnet' or 'claude-3-5-sonnet'"}), 400
    try:
        answer = get_final_answer(query, model)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
