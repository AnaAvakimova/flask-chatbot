from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = Flask(__name__)
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
# Store conversation history in memory (for each session)
conversation_history = [{
    "role": "system",
    "content": "You are a sarcastic assistant."
}]


@app.route("/")
def index():
    # Serve the index.html file from the 'static' folder
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chatbot():
    global conversation_history

    try:
        # Create a list to store all the messages for context
        message = request.json.get("message")
        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Add each new message to the list
        conversation_history.append({"role": "user", "content": message})

        # Request gpt-4o for chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history
        )
        # Print the response and add it to the messages list
        chat_message = response.choices[0].message.content
        print(f"Bot: {chat_message}")
        conversation_history.append({"role": "assistant", "content": chat_message})
        return jsonify({"reply": chat_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
