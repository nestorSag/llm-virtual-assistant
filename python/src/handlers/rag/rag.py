## requirements
# langchain==0.2.1 
# langchain-community==0.2.1
# pgvector==0.2.5 
# psycopg2-binary==2.9.9 
# pydantic-settings==2.1.0 
# instructor==0.3.5 
# tiktoken==0.7.0
# boto3==1.34.101 
# langchain_aws==0.1.6 

############ imports
import typing as t
import json
import logging

import boto3
from boto3 import Session

from langchain_community.vectorstores.pgvector import DistanceStrategy, PGVector
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate


############ create session
# Configure the logger
logger = logging.getLogger(__name__)

# Use the session to create a client
session = boto3.Session()
credentials = session.get_credentials()

############ retrieve parameters from SSM
def get_ssm_parameter(session: Session, parameter_name: str, prefix:str = '/lynceus-rag/'):
    """Retrieve a parameter's value from AWS SSM Parameter Store.

    Args:
        session (Session): the boto3 session to use to retrieve the parameters
        parameter_name (str): the name of the parameter
        prefix (str, optional): Parameter's prefix. Defaults to '/lynceus-rag/'.

    """
    ssm = session.client('ssm')
    response = ssm.get_parameter(
        Name = prefix+parameter_name
    )
    return response['Parameter']['Value']

def get_db_secret_value(secret_arn: str) -> str:
    """Get the secret value from the secret manager

    Args:
        secret_arn (str): ARN of the secret

    Returns:
        str: Value of the secret
    """
    client = boto3.client('secretsmanager')
    get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(get_secret_value_response['SecretString'])

# Setup env variables
VECTOR_DB_INDEX = get_ssm_parameter(session, 'VECTOR_DB_INDEX')
PG_VECTOR_DB_NAME = get_ssm_parameter(session, 'PG_VECTOR_DB_NAME')
PG_VECTOR_PORT = get_ssm_parameter(session, 'PG_VECTOR_PORT')
PG_VECTOR_SECRET_ARN = get_ssm_parameter(session, 'PG_VECTOR_SECRET_ARN')
PG_VECTOR_DB_HOST = get_ssm_parameter(session, 'PG_VECTOR_DB_HOST')
S3_BUCKET_NAME = get_ssm_parameter(session, 'S3_BUCKET_NAME')
EMBEDDING_MODEL_ID = get_ssm_parameter(session, "EMBEDDING_MODEL_ID")

def get_vector_store(session: Session) -> PGVector:
    logger.info(f"Retrieve secret from {PG_VECTOR_SECRET_ARN}")
    credentials = get_db_secret_value(PG_VECTOR_SECRET_ARN)

    br = session.client("bedrock-runtime")
    bedrock_embedding = BedrockEmbeddings(client=br, model_id=EMBEDDING_MODEL_ID)


    connection_string = PGVector.connection_string_from_db_params(
        driver="psycopg2",
        host=PG_VECTOR_DB_HOST,
        port=PG_VECTOR_PORT,
        database=PG_VECTOR_DB_NAME,
        user=credentials['username'],
        password=credentials['password']
    )

    vector_store = PGVector(
        connection_string=connection_string,
        collection_name=VECTOR_DB_INDEX,
        embedding_function=bedrock_embedding,
        distance_strategy=DistanceStrategy.COSINE,
    )
    return vector_store

# instantiate vector store as global object
vector_store = get_vector_store(session)

def get_rag_connection(
    llm_model_id: str,
    prompt: str,
    k: int = 5,
) -> t.Callable[[str], str]:
    """Create a connection a specified RAG model

    Parameters
    ----------
    llm_model_id : str, optional
        LLM model ID in AWS Bedrock.
    prompt : str, optional
        Prompt to use for the RAG mode.
    k : int, optional
        Number of documents to retrieve, by default 5

    Returns
    -------
    t.Callable[str, str]
        Function that takes a user query and returns the LLM's output
    """    
    retriever=vector_store.as_retriever(search_type="similarity",
                                    search_kwargs={'k': k})
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            ("human", "{input}"),
        ]
    )

    llm = ChatBedrock(
        model_id=llm_model_id,
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    chain = create_retrieval_chain(retriever, question_answer_chain)
    
    def invoke_rag(query: str) -> str:
        return chain.invoke({"input": query})["answer"]
    
    return invoke_rag



############ retrieve relevant docs (optional)

def retrieve(
    query: str,
    k: int,
) -> t.List[t.Dict[str, t.Any]]:
    """Retrieve relevant documents from the vector store

    Parameters
    ----------
    query : str
        Query to search for
    k : int
        Number of documents to retrieve

    Returns
    -------
    t.List[t.Dict[str, t.Any]]
        List of retrieved documents
    """    
    doc_scores = vector_store.similarity_search_with_relevance_scores(query, k=k)
    retrieved = []
    for doc, score in doc_scores:
        doc_dict = doc.dict()
        doc_dict["score"] = score
        retrieved.append(doc_dict)
    return retrieved

# for item in docs:
#     print(item)





############ retrieve embeddings (optional)
# conn = psycopg2.connect(host=PG_VECTOR_DB_HOST,
#         database=PG_VECTOR_DB_NAME,
#         user=credentials['username'],
#         password=credentials['password'])
# cur = conn.cursor()
# cur.execute("SELECT * FROM langchain_pg_embedding")
# ids = cur.fetchall()

# # Print metadata:
# # i[0] - document IDs
# # i[1] - embeddings
# # i[2] - plain text documents
# # i[3] - document metadata

# print([i[2] for i in ids])
