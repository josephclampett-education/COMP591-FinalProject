from openai import OpenAI
from dotenv import dotenv_values
import speech_recognition as sr
import time
import asyncio
from queue import Queue
from threading import Event, Thread
from enum import Enum, auto

import RobotCommander

# Initialize OpenAI client
OpenAI.api_key = dotenv_values('.env')["API_KEY"]
client = OpenAI(api_key=OpenAI.api_key)
client_input = None

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
        # Correct parameter names as per API documentation
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )

        print(f"TTS: {text}")

        # Save the audio file
        with open("output.mp3", "wb") as output_file:
            for chunk in response.iter_bytes():
                output_file.write(chunk)
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
                audio = recognizer.listen(source,timeout=10, phrase_time_limit=10)
                client_input = recognizer.recognize_whisper_api(audio, api_key=OpenAI.api_key)
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
        "continue": "GPTCODE_CONTINUE",
        "end": "GPTCODE_END",
        "score": "GPTCODE_SCORE",
        "unsure": "GPTCODE_UNSURE",
        "left": "GPTCODE_TURN_LEFT",
        "right": "GPTCODE_TURN_RIGHT",
        "grab": "GPTCODE_GRAB"
    }
    
    prompt = f"""
    The user will send requests to control a robot. Please respond only with one of the following commands: "{', '.join(UNIQUE_KEYWORDS.values())}"
    - To continue the game, return: "{UNIQUE_KEYWORDS['continue']}".
    - To end the game, return: "{UNIQUE_KEYWORDS['end']}".
    - To ask about the score or points (e.g., "What is my current score?", "How many points do I have?", etc.), return: "{UNIQUE_KEYWORDS['score']}".
    - To turn the robot left, return: "{UNIQUE_KEYWORDS['left']}
    - To turn the robot right, return: "{UNIQUE_KEYWORDS['right']}
    - To grab things with the robot, return: "{UNIQUE_KEYWORDS['grab']}
    - If the intent is unclear, return: "{UNIQUE_KEYWORDS['unsure']}".
    Respond with only one of these identifiers: "{', '.join(UNIQUE_KEYWORDS.values())}".
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=10,
        temperature=0
    )

    # Extract the content of the response
    responseChoices = response.choices
    responseChoice = responseChoices[0]
    responseMessage = responseChoice.message
    responseContent = responseMessage.content
    intent = responseContent.strip()
    return intent

# Speech recognition and command handling
def listen_and_respond(point_queue, event_queue, robot_commander):
    # Intro text
    multimodal_out("""Hello, I am your badminton practice partner.
                      We have two rounds of practice: the first round is to familiarize yourself with the rules of singles badminton and the second round is to practice badminton hitting techniques.
                      Now, please stand in the position opposite me, and I will introduce the rules of singles badminton.""")

    time.sleep(2)

    # Explain court text
    multimodal_out("""1. Serving rules: The birdy must be served diagonally to the opponent's service court. You start from the right service court when your score is even; If your score is odd, you start from the left service court.
                        2. Hitting rules: For singles, the boundaries are narrower than doubles: the inner side lines and the back boundary line are used.""")
    
    serialExplainEvent = Event()

    serialExplainEvent.clear()
    multimodal_out("Left court")
    event_queue.put((serialExplainEvent, EventType.INSTRUCT_LEFT_SERVICE_BOUNDS))
    serialExplainEvent.wait()
    
    serialExplainEvent.clear()
    multimodal_out("Right court court")
    event_queue.put((serialExplainEvent, EventType.INSTRUCT_RIGHT_SERVICE_BOUNDS))
    serialExplainEvent.wait()

    serialExplainEvent.clear()
    multimodal_out("Full court")
    event_queue.put((serialExplainEvent, EventType.INSTRUCT_FULL_COURT_BOUNDS))
    serialExplainEvent.wait()

    serialExplainEvent.clear()
    multimodal_out("You can hit the ball when you hear a beep.")
    event_queue.put((serialExplainEvent, EventType.HIT_START))
    serialExplainEvent.wait()
    
    while True:
        client_input = listen()
        # await asyncio.sleep(1)
        if client_input:
            client_input = client_input = client_input.strip().lower()
            print(f"USERINPUT: {client_input}")

        intent = process_user_input(client_input)
        
        # Act based on the intent
        match intent:
            case "GPTCODE_CONTINUE": # match "continue"
                multimodal_out("The game continues!")
            case "GPTCODE_END":  # match "end"
                robot_commander.send_command("END")
                multimodal_out("The game has ended! Thank you for playing!")
                break
            case "GPTCODE_SCORE":  # match "score"
                event = Event()
                event_queue.put((event, "SCORE"))
                event.wait()
                score = point_queue.get()
                multimodal_out(f"Your current score is {score} points.")
            case _:
                multimodal_out("I couldn't understand your intent. Please try again.")
                print("I couldn't understand your intent. Please try again.")

        # if "stop" in client_input:
        #    generate_tts("Ending the session. Goodbye!")
            #   break
        """
        if not robot_action(client_input):
                generate_tts("Sorry, I didn't understand the command.")
        else:
            print("Player did not respond.")
            """