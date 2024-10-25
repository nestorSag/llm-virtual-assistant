import logging
import os
import sys
import traceback

from flask import Flask, request, jsonify
from rag import get_rag_connection, retrieve

app = Flask(__name__)
# Set up logging to `stdout`
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)  # You can set to DEBUG, WARNING, etc., as needed
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

DEFAULT_PROMPT = (
    "You are an assistant to maintenance engineers in a semiconductor factory. "
    "Answer their questions using the provided context, referencing section numbers if possible."
    "If you don't know the answer, say you don't know. "
    "Context: {context}"
)

# DEFAULT_MODEL_ID = "meta.llama3-8b-instruct-v1:0"
# DEFAULT_MODEL_ID = "meta.llama3-70b-instruct-v1:0"
DEFAULT_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
DEFAULT_K = 5
DEFAULT_RAG = get_rag_connection(llm_model_id=DEFAULT_MODEL_ID, prompt=DEFAULT_PROMPT, k=DEFAULT_K)

# /rag route to handle RAG queries
@app.route('/rag', methods=['GET'])
def rag():
    # Mandatory parameter 'query'
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "The 'query' parameter is required"}), 400

    # Call the RAG model with the query
    try:
        result = DEFAULT_RAG(query)
        # Return the result as a JSON response
        return jsonify({"output": result})
    
    except Exception as e:
        trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": trace}), 500


# /rag route to test RAG configurations
@app.route('/test_rag', methods=['GET'])
def test_rag():
    # Mandatory parameter 'query'
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "The 'query' parameter is required"}), 400

    # Optional parameters with defaults
    model_id = request.args.get('model_id', DEFAULT_MODEL_ID)
    k = int(request.args.get('k', DEFAULT_K))  # Default top-k retrieval is 5
    prompt = request.args.get('prompt', DEFAULT_PROMPT)
    # add context interpolation to prompt if not already present
    if "{context}" not in prompt:
        prompt =f"{prompt}. Context: {{context}}"
    try:
        # Instantiate the RAG system using the provided parameters
        rag_model = get_rag_connection(llm_model_id=model_id, k=k, prompt=prompt)

        # Call the RAG model with the query
        result = rag_model(query)
        # Return the result as a JSON response
        return jsonify({"output": result})
    
    except Exception as e:
        trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": trace}), 500
    
# /rag route to test RAG configurations
@app.route('/test_retrieval', methods=['GET'])
def test_retrieval():
    # Mandatory parameter 'query'
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "The 'query' parameter is required"}), 400

    # Optional parameters with defaults
    k = int(request.args.get('k', DEFAULT_K))  # Default top-k retrieval is 5

    try:
        retrieved = retrieve(query, k)
        # Return the result as a JSON response
        return jsonify({"output": retrieved})
    
    except Exception as e:
        trace = traceback.format_exc()
        return jsonify({"error": str(e), "trace": trace}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
