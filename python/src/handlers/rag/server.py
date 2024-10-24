import os

from flask import Flask, request, jsonify
from .rag import get_rag_connection
app = Flask(__name__)

DEFAULT_PROMPT = (
    "You are an assistant to maintenance engineers in a semiconductor factory. "
    "Answer their questions using the provided context, referencing section numbers if possible."
    "If you don't know the answer, say you don't know. "
    "Context: {context}"
)

DEFAULT_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
DEFAULT_K = 5
DEFAULT_RAG = get_rag_connection(DEFAULT_MODEL_ID, DEFAULT_K, DEFAULT_PROMPT)

# /rag route to handle RAG queries
@app.route('/rag', methods=['GET'])
def rag():
    # Mandatory parameter 'query'
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "The 'query' parameter is required"}), 400

    # Call the RAG model with the query
    result = DEFAULT_RAG(query)

    # Return the result as a JSON response
    return jsonify(result)


# /rag route to test RAG configurations
@app.route('/test_rag', methods=['GET'])
def rag():
    # Mandatory parameter 'query'
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "The 'query' parameter is required"}), 400

    # Optional parameters with defaults
    model_id = request.args.get('model_id', DEFAULT_MODEL_ID)
    k = int(request.args.get('k', DEFAULT_K))  # Default top-k retrieval is 5
    prompt = request.args.get('prompt', DEFAULT_PROMPT)

    # Instantiate the RAG system using the provided parameters
    rag_model = get_rag_connection(model_id=model_id, k=k, prompt=prompt)

    # Call the RAG model with the query
    result = rag_model(query)

    # Return the result as a JSON response
    return jsonify(result)
    
# /rag route to test RAG configurations
@app.route('/test_retrieval', methods=['GET'])
def rag():
    # Mandatory parameter 'query'
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "The 'query' parameter is required"}), 400

    # Optional parameters with defaults
    model_id = request.args.get('model_id', DEFAULT_MODEL_ID)
    k = int(request.args.get('k', DEFAULT_K))  # Default top-k retrieval is 5
    prompt = request.args.get('prompt', DEFAULT_PROMPT)

    # Instantiate the RAG system using the provided parameters
    rag_model = get_rag_connection(model_id=model_id, k=k, prompt=prompt)

    # Call the RAG model with the query
    result = rag_model(query)

    # Return the result as a JSON response
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
