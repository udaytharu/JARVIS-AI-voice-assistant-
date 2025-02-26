import os
import requests
import datetime
import json
from dotenv import dotenv_values
from groq import Groq

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
Google_API_KEY = env_vars.get("Google_API_KEY")
CSE_ID = env_vars.get("CSE_ID")  # Default CSE ID

# Validate API keys
if not GroqAPIKey or not Google_API_KEY:
    raise ValueError("⚠️ Missing API Keys! Please check your .env file.")

# Initialize Groq Client
client = Groq(api_key=GroqAPIKey)

# Chat log file path
CHAT_LOG_PATH = "Data/ChatLog.json"
os.makedirs(os.path.dirname(CHAT_LOG_PATH), exist_ok=True)

# Load chat history
try:
    with open(CHAT_LOG_PATH, "r") as f:
        messages = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    messages = []

# System instructions
System = f"""Hello, I am {Username}, You are a very accurate AI chatbot named {Assistantname} with real-time web search.
*** Always search the internet first before answering. ***
*** Provide professional and well-structured answers using correct grammar. ***
*** Never say "I don't know"—always attempt to find relevant information. ***"""

# Function to fetch real-time search results using Google Custom Search API
def GoogleSearch(query):
    try:
        print("🔎 Searching Google for:", query)  # Debugging
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={Google_API_KEY}&cx={CSE_ID}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract relevant search results
        results = data.get("items", [])
        if not results:
            return "⚠️ No relevant search results found."

        # Format search results
        search_summary = f"🔎 **Search results for:** `{query}`\n\n"
        extracted_texts = []
        for result in results[:5]:  # Limit to top 5 results
            title = result.get("title", "No Title")
            snippet = result.get("snippet", "No Description Available.")
            link = result.get("link", "#")
            extracted_texts.append(f"{title}: {snippet}")
            search_summary += f"🔹 **{title}**\n📄 {snippet}\n🔗 [Read more]({link})\n\n"

        # Return formatted response + extracted text (for AI processing)
        return search_summary.strip(), "\n".join(extracted_texts)

    except requests.exceptions.RequestException as e:
        return f"⚠️ Error fetching search results: {e}", ""

# Function to get real-time system information
def SystemInformation():
    now = datetime.datetime.now()
    return f"""🕒 **Real-time Information**
- Day: {now.strftime("%A")}
- Date: {now.strftime("%d %B %Y")}
- Time: {now.strftime("%H:%M:%S")}
"""

# Function to refine AI response
def AnswerModifier(answer):
    return "\n".join(line.strip() for line in answer.split('\n') if line.strip())

# Main chatbot function
def RealtimeSearchEngine(prompt):
    global messages

    # Append user message
    messages.append({"role": "user", "content": prompt})

    # Get real-time search results
    search_summary, extracted_search_text = GoogleSearch(prompt)

    # Construct system context (search results go into AI model)
    system_context = [
        {"role": "system", "content": System},
        {"role": "system", "content": SystemInformation()},
        {"role": "system", "content": search_summary},
        {"role": "system", "content": f"Relevant search data:\n{extracted_search_text}"}
    ]

    # Call Groq's AI Model
    try:
        print("🧠 Processing AI response...")  # Debugging
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=system_context + messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=True,
            stop=None
        )

        # Extract response text
        answer = "".join(chunk.choices[0].delta.content for chunk in completion if chunk.choices[0].delta.content).strip()

    except Exception as e:
        answer = f"⚠️ AI system error: {e}"

    # Save assistant response and chat history
    messages.append({"role": "assistant", "content": answer})
    with open(CHAT_LOG_PATH, "w") as f:
        json.dump(messages, f, indent=4)

    return AnswerModifier(answer)

# Run chatbot in terminal loop
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))