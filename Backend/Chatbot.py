import os
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
# Initialize Groq Client
client = Groq(api_key=GroqAPIKey)

# Initialize messages and system prompt
messages = []
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""
SystemChatBot = [{"role": "system", "content": System}]

# Load chat log or create if not found
chat_log_path = "Data/ChatLog.json"
os.makedirs(os.path.dirname(chat_log_path), exist_ok=True)

try:
    with open(chat_log_path, "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(chat_log_path, "w") as f:
        dump([], f)

# Functions
def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    return (
        f"please use this real-time information if needed,\n"
        f"Day: {current_date_time.strftime('%A')}\n"
        f"Date: {current_date_time.strftime('%d')}\n"
        f"Month: {current_date_time.strftime('%B')}\n"
        f"Year: {current_date_time.strftime('%Y')}\n"
        f"Time: {current_date_time.strftime('%H')} hours :"
        f"{current_date_time.strftime('%M')} minutes :"
        f"{current_date_time.strftime('%S')} seconds.\n"
    )

def AnswerModifier(answer):
    lines = answer.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def ChatBot(query):
    """Send user query to the chatbot and return the AI's response."""
    global messages
    try:
        # Add user query to messages
        messages.append({"role": "user", "content": query})

        # Call Groq API
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        # Process response
        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content
        answer = answer.replace("</s>", "").strip()

        # Append assistant response and save log
        messages.append({"role": "assistant", "content": answer})
        with open(chat_log_path, "w") as f:
            dump(messages, f, indent=4)
        
        return AnswerModifier(answer)
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred. Please try again."

# Main loop
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))
