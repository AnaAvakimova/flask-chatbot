import json

from flask import Flask, request, jsonify, send_from_directory, session
from openai import OpenAI
import os
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "secret-key-for-development")

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Initialize function calling
function_signature = {
    "name": "get_cryptocurrency_current_price",
    "description": "Get current price for a given cryptocurrency in USD",
    "parameters": {
        "type": "object",
        "properties": {
            "currency": {
                "type": "string",
                "description": "Fullname of the cryptocurrency starting with lowercase letter",
            },
        },
        "required": ["currency"],
    }

}


def get_cryptocurrency_current_price(currency):
    """Returns current price for a given cryptocurrency in USD"""
    try:
        response = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={currency}&vs_currencies=usd')
        response.raise_for_status()
        return response.json().get(currency, {}).get('usd', 0)
    except requests.RequestException as e:
        print(f"Error fetching cryptocurrency price: {e}")
        return None


functions = {
    "get_cryptocurrency_current_price": get_cryptocurrency_current_price
}


@app.route("/")
def index():
    """Renders the home page"""
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chatbot():
    """Returns chat message"""
    try:
        message = request.json.get("message")
        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Retrieve session-specific conversation history
        if "conversation_history" not in session:
            session["conversation_history"] = [{
                "role": "system",
                "content": "You are a sarcastic assistant."
            }]
        conversation_history = session["conversation_history"]

        # Add user message to the list
        conversation_history.append({"role": "user", "content": message})
        session["conversation_history"] = conversation_history

        # Request gpt-4o for chat completion and add assistant answer to the conversation list
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            functions=[
                function_signature
            ]
        )
        chat_message = response.choices[0].message.content
        function_call = response.choices[0].message.function_call
        print(f"Bot: {chat_message}")
        # Convert function_call to dict if it exists, otherwise None
        function_call_dict = None
        if function_call:
            function_call_dict = {
                "name": function_call.name,
                "arguments": function_call.arguments
            }

        conversation_history.append({
            "role": "assistant",
            "content": chat_message,
            "function_call": function_call_dict  # Store as dict instead of FunctionCall object
        })
        session["conversation_history"] = conversation_history

        # Run function calling if it's in the response
        if function_call:
            function_name = function_call.name
            kwargs = json.loads(function_call.arguments)
            function = functions.get(function_name)
            result = function(**kwargs)
            print(result)

            conversation_history.append({
                "role": "function",
                "name": function_name,
                "content": str(result)
            })
            session["conversation_history"] = conversation_history

            new_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                functions=[
                    function_signature
                ]

            )
            print('new', new_response)
            chat_message = new_response.choices[0].message.content
            conversation_history.append({"role": "assistant", "content": chat_message})
            session["conversation_history"] = conversation_history
            return jsonify({"reply": chat_message})

        # Print the response and add it to the messages list
        return jsonify({"reply": chat_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
