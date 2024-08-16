import streamlit as st
import requests

st.title("Quran Chatbot")

# Replace <your-host-ip> with the actual IP address of the host machine
API_URL = "http://10.0.1.212:8000/query"

# Function to ask a question to the FastAPI backend
def ask_question(question, history):
    response = requests.post(API_URL, json={"question": question, "history": history})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error: {response.status_code}")
        return None

# Input for user's question
prompt1 = st.text_input("Enter Your Question From Documents")

# Initialize the session state for history
if "history" not in st.session_state:
    st.session_state.history = []

if st.button("Ask Question") and prompt1:
    response = ask_question(prompt1, st.session_state.history)
    if response:
        st.write("Answer:", response["answer"])
        
        # Update history
        st.session_state.history.append({"question": prompt1, "answer": response["answer"]})
        
        # Display document similarity search results
        with st.expander("Document Similarity Search"):
            for doc_content in response["context"]:
                st.write(doc_content)
                st.write("--------------------------------")
