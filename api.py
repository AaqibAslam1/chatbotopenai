import os
import pickle
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings  
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chat_models import ChatOpenAI
import uvicorn
import time

app = FastAPI()

# Initialize the OpenAI client
client = ChatOpenAI(
    api_key=os.getenv("AIML_API_KEY"),  # Ensure the API key is securely handled
    base_url="https://api.aimlapi.com",
    model="gpt-4-turbo"  
)

# Prompt template for handling the conversation and context
prompt_template = ChatPromptTemplate.from_template(
"""
You are a helpful assistant. Please answer the questions based on the provided context. Recall previous interactions and maintain continuity in the conversation.
Refer to the context as Quran. When you talk about the Quran always give reference to what passage you are talking about.

<context>
{context}
<context>

Previous questions and answers:
{history}

Current question: {input}

Answer in the language the question is asked.
"""
)

class QueryRequest(BaseModel):
    question: str

history = []
vectors_list = []
final_documents_list = []

def build_context():
    history_text = ""
    for interaction in history:
        history_text += f"Question: {interaction['question']}\nAnswer: {interaction['answer']}\n\n"
    return history_text

def load_embeddings(embeddings_files):
    global vectors_list, final_documents_list
    for embeddings_file in embeddings_files:
        if os.path.exists(embeddings_file):
            with open(embeddings_file, "rb") as f:
                vectors, final_documents = pickle.load(f)
                vectors_list.append(vectors)
                final_documents_list.extend(final_documents)
        else:
            raise FileNotFoundError(f"Embeddings file {embeddings_file} not found.")

@app.on_event("startup")
async def startup_event():
    embeddings_files = [
        "tafsir_english_embeddings.pkl",
        "quran_english_embeddings.pkl"  
    ]
    load_embeddings(embeddings_files)

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.post("/query")
async def query_documents(query: QueryRequest):
    global history, vectors_list, final_documents_list
    if not vectors_list or not final_documents_list:
        raise HTTPException(status_code=500, detail="Embeddings not loaded.")

    history_text = build_context()
    context = {
        'context': final_documents_list,
        'history': history_text,
        'input': query.question
    }

    # Create the document processing chain
    document_chain = create_stuff_documents_chain(client, prompt_template)

    combined_responses = []
    start = time.process_time()
    for vectors in vectors_list:
        retriever = vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        response = retrieval_chain.invoke(context)
        combined_responses.append(response)
    response_time = time.process_time() - start

    # Combine responses from multiple embeddings
    combined_answer = "\n".join([response['answer'] for response in combined_responses])
    history.append({"question": query.question, "answer": combined_answer})

    return {"answer": combined_answer, "response_time": response_time, "context": [doc.page_content for response in combined_responses for doc in response["context"]]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
