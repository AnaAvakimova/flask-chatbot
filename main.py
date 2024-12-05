from flask import Flask, request, jsonify, send_from_directory, session

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize OpenAI client
openai_api_key = os.environ.get("OPENAI_API_KEY")
llm = ChatOpenAI(
    openai_api_key=openai_api_key, model="gpt-3.5-turbo")

# Retrieve and embed documents
with open('data/ana.txt', 'r', encoding='utf-8') as file:
    text = file.read()
    documents = [text]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
all_splits = text_splitter.create_documents(documents)
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = FAISS.from_documents(documents=all_splits, embedding=embeddings)


# Store conversation history in memory (for each session)
# conversation_history = [{
#     "role": "system",
#     "content": "You are a sarcastic assistant."
# }]


@app.route("/")
def index():
    # Serve the index.html file from the 'static' folder
    return send_from_directory("static", "index.html")


def retrieve_relevant_chunks(query):
    docs = vectorstore.similarity_search(query, k=3)
    return "\n".join([doc.page_content for doc in docs])


@app.route("/chat", methods=["POST"])
def chatbot():
    try:
        # Create a list to store all the messages for context
        message = request.json.get("message")
        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Retrieve session-specific conversation history
        if "conversation_history" not in session:
            session["conversation_history"] = [{
                "role": "system",
                "content": "You are a sarcastic assistant."
            }]

        # Query the vector store for relevant context from ana.txt
        relevant_context = retrieve_relevant_chunks(message)

        # Add the context to the conversation history
        conversation_history = session["conversation_history"]
        if relevant_context:
            conversation_history.append({
                "role": "system",
                "content": f"Here is some additional context to assist you:\n{relevant_context}"
            })

        conversation_history.append({"role": "user", "content": message})

        # Request gpt-4o for chat completion
        response = llm.invoke(conversation_history)
        # Print the response and add it to the messages list
        # chat_message = response.choices[0].message.content
        print(f"Bot: {response}")
        print(response.content)
        conversation_history.append({"role": "assistant", "content": response.content})
        return jsonify({"reply": response.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
