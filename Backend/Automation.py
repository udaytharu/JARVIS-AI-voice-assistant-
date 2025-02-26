from AppOpener import close, open as appopen
from pywhatkit import search as pywhatkit_search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
env_vars = dotenv_values(".env")
GROQ_API_KEY = env_vars.get("GroqAPIKey")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
)

# Initialize Groq client and session
try:
    client = Groq(api_key=GROQ_API_KEY)
    logging.info("Groq client initialized successfully")
except Exception as e:
    logging.warning(f"Failed to initialize Groq client: {e}. Using fallback for content generation.")
    client = None

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

# Chat history for content generation
messages = []
SYSTEM_PROMPT = {
    "role": "system",
    "content": f"Hello, I'm {os.environ.get('Username', 'Assistant')}. You're a content writer."
}

def GoogleSearch(topic: str) -> bool:
    logging.debug(f"GoogleSearch: {topic}")
    try:
        pywhatkit_search(topic)
        return True
    except Exception as e:
        logging.error(f"Google search failed: {e}")
        return False

def Content(topic: str) -> bool:
    """Generate content and open it in Notepad."""
    def open_notepad(file_path: str) -> bool:
        try:
            default_text_editor = "notepad.exe" if os.name == "nt" else "gedit"
            subprocess.Popen([default_text_editor, file_path])
            logging.info(f"Opened {file_path} in {default_text_editor}")
            return True
        except Exception as e:
            logging.error(f"Failed to open Notepad: {e}")
            return False

    def content_writer_ai(prompt: str) -> str:
        """Generate content using Groq API or a fallback."""
        if client:
            try:
                messages.append({"role": "user", "content": prompt})
                completion = client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[SYSTEM_PROMPT] + messages,
                    max_tokens=2048,
                    temperature=0.7,
                    top_p=1,
                    stream=True,
                    stop=None
                )
                answer = "".join(chunk.choices[0].delta.content or "" for chunk in completion)
                messages.append({"role": "assistant", "content": answer})
                logging.debug(f"Generated AI content for '{prompt}'")
                return answer
            except Exception as e:
                logging.error(f"AI content generation failed: {e}")
                return f"Error: {e}"
        else:
            # Fallback content if Groq fails
            logging.warning("Groq client unavailable, using fallback content")
            return f"This is a fallback response for '{prompt}' because the AI service is unavailable."

    topic = topic.replace("content", "").strip()
    logging.debug(f"Content: Generating for topic '{topic}'")
    content_by_ai = content_writer_ai(topic)
    
    # Always write content, even if it's an error message
    os.makedirs("Data", exist_ok=True)
    file_path = os.path.join("Data", f"{topic.lower().replace(' ', '')}.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content_by_ai)
        logging.debug(f"Content written to {file_path}")
        return open_notepad(file_path)
    except Exception as e:
        logging.error(f"Failed to write or open file: {e}")
        return False

def YoutubeSearch(topic: str) -> bool:
    logging.debug(f"YoutubeSearch: {topic}")
    try:
        url = f"https://www.youtube.com/results?search_query={topic}"
        webbrowser.open(url)
        return True
    except Exception as e:
        logging.error(f"YouTube search failed: {e}")
        return False

def PlayYoutube(query: str) -> bool:
    logging.debug(f"PlayYoutube: {query}")
    try:
        playonyt(query)
        return True
    except Exception as e:
        logging.error(f"YouTube playback failed: {e}")
        return False

def OpenApp(app: str) -> bool:
    logging.debug(f"OpenApp: {app}")
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception:
        def extract_link(html: str) -> list[str]:
            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a", {"jsname": "UWckNb"})
            return [link.get("href") for link in links if link.get("href")]

        url = f"https://www.google.com/search?q={app}+official+site"
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            links = extract_link(response.text)
            if links:
                webbrowser.open(links[0])
                return True
            logging.warning(f"No valid links found for {app}")
            return False
        except Exception as e:
            logging.error(f"Web fallback failed for {app}: {e}")
            return False

def CloseApp(app: str) -> bool:
    logging.debug(f"CloseApp: {app}")
    if "chrome" in app.lower():
        try:
            subprocess.run(["taskkill", "/IM", "chrome.exe", "/F"], check=True)
            logging.info("Chrome closed successfully")
            return True
        except subprocess.CalledProcessError:
            logging.error("Failed to close Chrome")
            return False
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        logging.info(f"{app} closed successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to close {app}: {e}")
        return False

def System(command: str) -> bool:
    logging.debug(f"System: {command}")
    actions = {
        "mute": "volume mute",
        "unmute": "volume mute",
        "volume up": "volume up",
        "volume down": "volume down"
    }
    action = actions.get(command.strip().lower())
    if action:
        try:
            keyboard.press_and_release(action)
            return True
        except Exception as e:
            logging.error(f"System command '{command}' failed: {e}")
            return False
    logging.warning(f"Unknown system command: {command}")
    return False

async def TranslateAndExecute(commands: list[str]) -> list[bool]:
    logging.debug(f"TranslateAndExecute: {commands}")
    funcs = []
    for command in commands:
        command = command.strip()
        if not command:
            continue
        if command.startswith("open "):
            funcs.append(asyncio.to_thread(OpenApp, command.removeprefix("open ").strip()))
        elif command.startswith("close "):
            funcs.append(asyncio.to_thread(CloseApp, command.removeprefix("close ").strip()))
        elif command.startswith("play "):
            funcs.append(asyncio.to_thread(PlayYoutube, command.removeprefix("play ").strip()))
        elif command.startswith("content "):
            funcs.append(asyncio.to_thread(Content, command.removeprefix("content ").strip()))
        elif command.startswith("write "):  # Added to support "write " for content generation
            funcs.append(asyncio.to_thread(Content, command.removeprefix("write ").strip()))
        elif command.startswith("google search "):
            funcs.append(asyncio.to_thread(GoogleSearch, command.removeprefix("google search ").strip()))
        elif command.startswith("youtube search "):
            funcs.append(asyncio.to_thread(YoutubeSearch, command.removeprefix("youtube search ").strip()))
        elif command.startswith("system "):
            funcs.append(asyncio.to_thread(System, command.removeprefix("system ").strip()))
        elif command.startswith("general "):
            logging.info(f"General query not implemented: {command.removeprefix('general ')}")
        elif command.startswith("realtime "):
            logging.info(f"Realtime query not implemented: {command.removeprefix('realtime ')}")
        else:
            logging.warning(f"No function found for: {command}")

    if not funcs:
        logging.debug("No valid commands to execute")
        return []

    results = await asyncio.gather(*funcs, return_exceptions=True)
    processed_results = [False if isinstance(r, Exception) else r for r in results]
    logging.debug(f"Execution results: {processed_results}")
    return processed_results

async def Automation(commands: list[str]) -> bool:
    logging.debug(f"Automation starting with commands: {commands}")
    results = await TranslateAndExecute(commands)
    if not results:
        logging.warning("No valid commands executed")
        return False
    success = all(results)
    logging.debug(f"Automation completed: {success}")
    if not success:
        logging.error(f"Some commands failed: {results}")
    return success

if __name__ == "__main__":
    async def test_automation():
        test_commands = ["write command as you want"]
        logging.info(f"Executing test commands: {test_commands}")
        success = await Automation(test_commands)
        logging.info(f"All commands executed successfully: {success}")

    asyncio.run(test_automation())