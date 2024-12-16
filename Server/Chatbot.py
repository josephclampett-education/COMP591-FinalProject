import os
from openai import OpenAI
from dotenv import dotenv_values
import speech_recognition as sr
import time
import io
import pygame as pygame
from queue import Queue
from threading import Event, Thread
from enum import Enum, auto

score = 0

class EventType(Enum):
    GET_SCORE = auto()
    INSTRUCT_LEFT_SERVICE_BOUNDS = auto()
    INSTRUCT_RIGHT_SERVICE_BOUNDS = auto()
    INSTRUCT_FULL_COURT_BOUNDS = auto()
    HIT_START = auto()
    END = auto()

#(Text to Speech)
def multimodal_out(text):
    try:
        print(f"TTS: {text}")

        # Correct parameter names as per API documentation
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )

        # Create an in-memory audio stream
        audio_data = io.BytesIO()

        # Write the audio response to the in-memory stream
        for chunk in response.iter_bytes():
            audio_data.write(chunk)

        # Rewind the stream to the beginning
        audio_data.seek(0)

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load the audio stream directly into pygame mixer
        pygame.mixer.music.load(audio_data, 'mp3')

        # Play the audio
        pygame.mixer.music.play()

        # Wait until the audio finishes playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Error generating TTS: {e}")

#Automatic Response from OpenAi
"""
def chatgpt_response(input_text):
    response_text = ""  # Initialize a variable to store the response
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": input_text}],
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="")  # Stream the content to the console
                response_text += content  # Append to the response_text
    except Exception as e:
        print(f"Error during streaming: {e}")
        return "An error occurred while processing your request."
    return response_text  # Return the full response text after streaming

#chatgpt_response("Whats your name")
"""


# Robot logic based on recognized commands
"""
def robot_action(command):
    if "yes" in command:
        print("Robot executing: drive Rectangle and ExplainServeTargetArea")
        generate_tts("lease remember that when starting the serve, the shuttle should be served to the diagonal court.
                     I will now walk around the hitting area, please observe carefully.")
        time.sleep(10)
        return True
    elif "point" or "score" or "grade" in command:
        print("Robot is checking points")
        generate_tts(f"You got {score} points")
        return True
    else:
        print("No keyword matched. Asking ChatGPT for a response.")
        generate_tts(chatgpt_response(command))
        return False
"""

#user's Input, speech to text
def listen():
    recognizer = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            print("Say something!")
            try:
                audio = recognizer.listen(source, timeout = 10, phrase_time_limit = 10)
                client_input = recognizer.recognize_whisper_api(audio)
                print(f"Recognized command: {client_input}")
                return client_input
            except sr.WaitTimeoutError:
                print("No input detected within timeout")
                return None
            except sr.UnknownValueError:
                print("Could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Whisper API; {e}")
                return None


def process_user_input(user_input):
    # Prompt ChatGPT to analyze the user's intent
    UNIQUE_KEYWORDS = {
        "end": "GPTCODE_END",
        "score": "GPTCODE_SCORE",
        "unsure": "GPTCODE_UNSURE"
    }

    prompt = f"""
    The user will send requests to control a robot or will ask questions about the rules of badminton. If their intent matches one of the listed commands, please respond only with one of the following responses: "{', '.join(UNIQUE_KEYWORDS.values())}"
    - To end the game if the player explicitly asks to end the game (i.e. do not listen to 'bye'), return: "{UNIQUE_KEYWORDS['end']}".
    - To ask about the score or points (e.g., "What is my current score?", "How many points do I have?", etc.), return: "{UNIQUE_KEYWORDS['score']}".

    If they ask a general question about the rules of badminton, respond with only an answer to their question.

    Finally, if the intent is unclear, return: "{UNIQUE_KEYWORDS['unsure']}".
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=100,
        temperature=0
    )

    # Extract the content of the response
    responseChoices = response.choices
    responseChoice = responseChoices[0]
    responseMessage = responseChoice.message
    responseContent = responseMessage.content
    cleanedResponse = responseContent.strip()
    return cleanedResponse

OpenAI.api_key = dotenv_values('.env')["API_KEY"]
client = OpenAI(api_key=OpenAI.api_key)
client_input = None
DEBUG = False

# Speech recognition and command handling
def listen_and_respond(point_queue, event_queue):
    os.environ["OPENAI_API_KEY"] = OpenAI.api_key

    if not DEBUG:
        # Intro text
        multimodal_out("""Hello, I am your badminton practice partner. We have two rounds of practice: the first round is designed to familiarize yourself with the rules of singles badminton and the second round is to practice badminton hitting techniques. Now, please stand in the position opposite me, and I will introduce the rules of singles badminton.""")

        # Explain court text
        multimodal_out("""1, Serving rules: The birdy must be served diagonally to the opponent's service court. You start from the right service court when your score is even; If your score is odd, you start from the left service court. 2, Hitting rules: For singles, the boundaries are narrower than doubles: the inner side lines and the back boundary line are used.""")

    serialExplainEvent = Event()

    serialExplainEvent.clear()
    multimodal_out("Now I will show you the left service court area")
    event_queue.put((serialExplainEvent, EventType.INSTRUCT_LEFT_SERVICE_BOUNDS))
    serialExplainEvent.wait()

    # serialExplainEvent.clear()
    # multimodal_out("Now I will show you the right service court area")
    # event_queue.put((serialExplainEvent, EventType.INSTRUCT_RIGHT_SERVICE_BOUNDS))
    # serialExplainEvent.wait()

    # serialExplainEvent.clear()
    # multimodal_out("Now I will show you the full court area for singles badminton")
    # event_queue.put((serialExplainEvent, EventType.INSTRUCT_FULL_COURT_BOUNDS))
    # serialExplainEvent.wait()

    serialExplainEvent.clear()
    multimodal_out("You can hit the ball when you hear a beep. Please feel free to ask any questions you may have.")
    event_queue.put((serialExplainEvent, EventType.HIT_START))
    serialExplainEvent.wait()

    while True:
        client_input = listen()
        # await asyncio.sleep(1)
        if client_input:
            client_input = client_input = client_input.strip().lower()
            print(f"USERINPUT: {client_input}")

            response = process_user_input(client_input)

            # Act based on the intent
            match response:
                case "GPTCODE_END":  # match "end"
                    multimodal_out("The game has ended! Thank you for playing!")
                    event_queue.put((Event(), EventType.END))
                    break
                case "GPTCODE_SCORE":  # match "score"
                    event = Event()
                    event_queue.put((event, EventType.GET_SCORE))
                    event.wait()
                    score = point_queue.get()
                    multimodal_out(f"Your current score is {score} points.")
                case "GPTCODE_UNSURE":
                    print("UNSURE")
                    # multimodal_out("I couldn't understand your intent. Please try again.")
                case _:
                    multimodal_out(response)

        # if "stop" in client_input:
        #    generate_tts("Ending the session. Goodbye!")
            #   break
        """
        if not robot_action(client_input):
                generate_tts("Sorry, I didn't understand the command.")
        else:
            print("Player did not respond.")
            """