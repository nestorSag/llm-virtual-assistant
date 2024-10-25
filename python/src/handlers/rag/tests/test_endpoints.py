import urllib.parse

# rag endpoint test
def test_endpoints():
    params = {"query": "what is your purpose?"}
    f"http://127.0.0.1:5000/rag?{urllib.parse.urlencode(params)}"

    # rag_test endpoint test
    params = {"query": "what is your purpose?", "k": 5, "prompt": "Your purpose is to assist process engineers in semiconductor factories."}
    f"http://127.0.0.1:5000/test_rag?{urllib.parse.urlencode(params)}"

    # retrieve endpoint test
    params = {"query": "what is your purpose?", "k": 5}
    f"http://127.0.0.1:5000/test_retrieval?{urllib.parse.urlencode(params)}"


### test containerised app through host port 5050
# docker run -e AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
#            -e AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
#            -e AWS_DEFAULT_REGION=$(aws configure get region) \
#            -p 5050:5000 rag-server:1.0
