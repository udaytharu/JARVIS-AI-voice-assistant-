from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextTOScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.ImageGeneration import GenerateImages
from dotenv import dotenv_values
from asyncio import run
from time import sleep, time, localtime, strftime
import subprocess
import threading
import json
import os
import logging
import sys
import pyaudio
import numpy as np

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
DefaultMessage = f'''{Username} 😄: Hello {Assistantname} 🌟, How are you?
{Assistantname} 🤖: Welcome {Username} 🎉, I am doing well. How may I help you today? 😊'''
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "write", "create presentation"]

# Ensure directories exist
os.makedirs("Data", exist_ok=True)
os.makedirs(os.path.join("Frontend", "Files"), exist_ok=True)

# Global variable to track last interaction time
last_interaction_time = time()

def DetectClap():
    """Detect clap sound using pyaudio."""
    CHUNK = 1024
    RATE = 44100
    THRESHOLD = 3000  # Adjust this threshold based on your microphone and environment noise

    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.float32)
        stream.stop_stream()
        stream.close()
        p.terminate()

        amplitude = np.abs(np.max(data))
        logging.debug(f"Clap detection: Amplitude = {amplitude}, Threshold = {THRESHOLD}")
        return amplitude > THRESHOLD
    except Exception as e:
        logging.error(f"Error in clap detection: {e}")
        return False

def ShowDefaultChatIfNOChats():
    chat_log_path = r"Data\ChatLog.json"
    try:
        with open(chat_log_path, "r", encoding='utf-8') as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                    file.write(DefaultMessage)
    except FileNotFoundError:
        with open(chat_log_path, "w", encoding='utf-8') as file:
            json.dump([], file)
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(DefaultMessage)

def ReadChatLogJson():
    chat_log_path = r"Data\ChatLog.json"
    try:
        with open(chat_log_path, 'r', encoding='utf-8') as file:
            chat_log_data = json.load(file)
        return chat_log_data
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"User: {entry['content']} 😄\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant: {entry['content']} 🌟\n"
    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    with open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8') as file:
        Data = file.read()
    if len(str(Data)) > 0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
            file.write(result)

def GreetUserByTime():
    """Greet the user based on the current time with a smooth transition."""
    current_hour = localtime().tm_hour
    if 5 <= current_hour < 12:
        greeting = f"Good morning Boss! I'm excited to assist you today!"
    elif 12 <= current_hour < 17:
        greeting = f"Good afternoon Boss! How can I make your day better?"
    else:
        greeting = f"Good evening Boss! I'm here to help you unwind or work tonight!"
    ShowTextTOScreen(f"{Assistantname} 🤖: {greeting}")
    TextToSpeech(greeting)
    sleep(1)  # Smooth transition after greeting

def CheckSystem():
    """Check the status of backend, frontend, and data components with progress feedback."""
    components = [("Backend", os.path.isdir("Backend")), ("Frontend", os.path.isdir("Frontend")), ("Data", os.path.isdir("Data"))]
    for component, exists in components:
        ShowTextTOScreen(f"{Assistantname} 🤖: Checking {component}... 🔍")
        sleep(0.5)  # Simulate check delay for smooth feedback
        if not exists:
            logging.error(f"{component} directory not found! 😞")
            ShowTextTOScreen(f"{Assistantname}: Error - {component} directory missing! 🚫")
            TextToSpeech(f"Error - {component} directory missing")
            return False
    logging.info("System components checked successfully. ✅")
    TextToSpeech("System components checked successfully.")
    return True

def InitialExecution():
    global last_interaction_time
    ShowTextTOScreen(f"{Assistantname} 🤖: System initializing... 🔄")
    TextToSpeech("System initializing")
    sleep(1)  # Initial delay for a smooth start

    if CheckSystem():
        ShowTextTOScreen(f"{Assistantname} 🤖: System ready! 🎉")
        TextToSpeech("System ready to roll")
        sleep(0.5)  # Pause before greeting
    else:
        ShowTextTOScreen(f"{Assistantname} 🤖: System initialization failed. Please fix issues and restart. 😞")
        TextToSpeech("System initialization failed. Please fix issues and restart.")
        sleep(2)  # Give user time to read error
        sys.exit(1)

    SetMicrophoneStatus("False")
    ShowDefaultChatIfNOChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    GreetUserByTime()  # Personalized greeting
    SetAssistantStatus("Available... ✅")
    last_interaction_time = time()  # Set initial interaction time

InitialExecution()

def ShutdownAssistant():
    """Graceful shutdown with user confirmation."""
    logging.info("Initiating shutdown... 🚪")
    SetAssistantStatus("Shutting down... 🔚")
    ShowTextTOScreen(f"{Assistantname}: Goodbye {Username}! Shutting down now. 👋 Confirm with 'yes' to proceed.")
    TextToSpeech("Goodbye! Shutting down now. Confirm with exit to proceed or say cancel ")
    sleep(3)  # Wait for user response
    if SpeechRecognition().lower() == "exit":
        for p in subprocesses:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
        sys.exit(0)
    else:
        SetAssistantStatus("Available... ✅")
        ShowTextTOScreen(f"{Assistantname}: Shutdown cancelled. I'm back! 😄")
        TextToSpeech("Shutdown cancelled. I'm back!")

def EnterSleepMode():
    """Enter sleep mode with a smooth transition."""
    global last_interaction_time
    ShowTextTOScreen(f"{Assistantname} 🤖: No activity detected. Entering sleep mode in 5 seconds... 🌙")
    TextToSpeech("No activity detected. Entering sleep mode in 5 seconds.")
    for i in range(5, 0, -1):
        ShowTextTOScreen(f"{Assistantname} 🤖: Sleeping in {i}... 😴")
        sleep(1)
    SetMicrophoneStatus("False")
    SetAssistantStatus("Sleeping... 😴")
    ShowTextTOScreen(f"{Assistantname}: Now sleeping. Wake me with a clap or voice! 🌙")
    TextToSpeech("Now sleeping. Wake me with a clap or voice!")
    last_interaction_time = time()

def WakeFromSleep():
    """Wake from sleep with a smooth transition."""
    SetMicrophoneStatus("True")
    SetAssistantStatus("Waking up... ☀️")
    ShowTextTOScreen(f"{Assistantname} 🤖: Waking up... please wait! ☀️")
    TextToSpeech("Waking up. Please wait!")
    sleep(1)  # Smooth wake transition
    ShowTextTOScreen(f"{Assistantname}: I'm back and ready to help! 😄👏")
    TextToSpeech("I'm back and ready to help!")

def MainExecution():
    global last_interaction_time
    TaskExecution = False
    ImageExecution = False
    PresentationExecution = False
    ImageGenerationQuery = ""
    PresentationDetails = {"topic": "", "presenter": "", "date": "", "company_name": "Your Company Name Here"}

    SetAssistantStatus("Listening... 👂")
    Query = SpeechRecognition()
    if Query:
        last_interaction_time = time()
        if GetAssistantStatus() == "Sleeping... 😴":
            WakeFromSleep()
    ShowTextTOScreen(f"{Username}: {Query} 😄")
    SetAssistantStatus("Thinking... 🤔")
    Decision = FirstLayerDMM(Query)

    logging.debug(f"Decision: {Decision}")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    Merged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate image" in queries:
            ImageGenerationQuery = queries.replace("generate image ", "")
            ImageExecution = True
        elif "create presentation" in queries:
            parts = queries.replace("create presentation ", "").split()
            if len(parts) >= 3:
                PresentationDetails["topic"] = parts[0]
                PresentationDetails["presenter"] = parts[1]
                PresentationDetails["date"] = parts[2]
            PresentationExecution = True

    for queries in Decision:
        if not TaskExecution:
            if any(queries.startswith(func) for func in Functions):
                TaskExecution = True

    if ImageExecution:
        ShowTextTOScreen(f"{Assistantname} 🤖: Executing image generation... 🎨")
        TextToSpeech("Executing image generation")
        with open(r"Frontend\Files\ImageGeneration.data", 'w') as file:
            file.write(f"{ImageGenerationQuery}, True")
        try:
            p1 = subprocess.Popen(
                ['python', r'Backend\ImageGeneration.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            subprocesses.append(p1)
            sleep(1)
            SetAssistantStatus("Available... ✅")
            ShowTextTOScreen(f"{Assistantname}: Image generated! 🎉")
            TextToSpeech("Image generated!")
        except Exception as e:
            logging.error(f"Error starting ImageGeneration.py: {e}")
            ShowTextTOScreen(f"{Assistantname}: Image generation failed. Retry? 😞")
            TextToSpeech("Image generation failed. Please retry.")
        return True

    if TaskExecution:
        SetAssistantStatus("Executing... 🚀")
        success = run(Automation(Decision))
        SetAssistantStatus("Available... ✅")
        if success:
            ShowTextTOScreen(f"{Assistantname}: Command completed! 🎉")
            TextToSpeech("Command completed!")
        else:
            ShowTextTOScreen(f"{Assistantname}: Command failed. Try again? 😞")
            TextToSpeech("Command failed. Please try again.")
        return success

    if G and R or R:
        SetAssistantStatus("Searching... 🔍")
        ShowTextTOScreen(f"{Assistantname} 🤖: Searching for your query... 🔍")
        TextToSpeech("Searching for your query")
        Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
        ShowTextTOScreen(f"{Assistantname}: {Answer} 🌐")
        SetAssistantStatus("Answering... 💬")
        TextToSpeech(Answer)
        return True

    for Queries in Decision:
        if "general" in Queries:
            SetAssistantStatus("Thinking... 🤔")
            QueryFinal = Queries.replace("general ", "")
            Answer = ChatBot(QueryModifier(QueryFinal))
            ShowTextTOScreen(f"{Assistantname}: {Answer} 🌟")
            SetAssistantStatus("Answering... 💬")
            TextToSpeech(Answer)
            return True
        elif "realtime" in Queries:
            SetAssistantStatus("Searching... 🔍")
            ShowTextTOScreen(f"{Assistantname} 🤖: Searching in real-time... 🔍")
            TextToSpeech("Searching in real-time")
            QueryFinal = Queries.replace("realtime ", "")
            Answer = ChatBot(QueryModifier(QueryFinal))
            ShowTextTOScreen(f"{Assistantname}: {Answer} 🌐")
            SetAssistantStatus("Answering... 💬")
            TextToSpeech(Answer)
            return True
        elif "exit" in Queries:
            ShutdownAssistant()
            return True

def FirstThread():
    global last_interaction_time
    while True:
        CurrentStatus = GetMicrophoneStatus()
        current_time = time()
        if CurrentStatus == "True" and (current_time - last_interaction_time) > 60:
            EnterSleepMode()
        elif CurrentStatus == "False" and GetAssistantStatus() == "Sleeping... 😴":
            try:
                if DetectClap():
                    logging.info("Clap detected! Waking up...")
                    WakeFromSleep()
                    last_interaction_time = time()
                elif (current_time - last_interaction_time) <= 60 and SpeechRecognition():
                    logging.info("Voice detected! Waking up...")
                    WakeFromSleep()
                    last_interaction_time = time()
            except Exception as e:
                logging.error(f"Error during wake check: {e}")
                sleep(0.1)  # Avoid tight loop on error
        elif CurrentStatus == "True":
            MainExecution()
        else:
            AIStatus = GetAssistantStatus()
            if "Available..." not in AIStatus and "Sleeping..." not in AIStatus:
                SetAssistantStatus("Available... ✅")
            sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    thread1 = threading.Thread(target=FirstThread, daemon=True)
    thread1.start()
    SecondThread()