from openai import OpenAI
import openai
from dotenv import dotenv_values
import speech_recognition as sr
import time
import asyncio
from queue import Queue
from threading import Event, Thread

import RobotCommander

# Initialize OpenAI client
OpenAI.api_key = dotenv_values('.env')["API_KEY"]
client = OpenAI(api_key=OpenAI.api_key)
client_input = None

score = 0

#(Text to Speech)
def generate_tts(text):
    try:
        # Correct parameter names as per API documentation
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )

        # Save the audio file
        with open("output.mp3", "wb") as output_file:
            for chunk in response.iter_bytes():
                output_file.write(chunk)
    except Exception as e:
        print(f"Error generating TTS: {e}")
#Testing
generate_tts("move forward")


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
        "right": "GPTCODE_TURN_RIGHT"
    }

    # 创建用于意图解析的 Prompt
    prompt = f"""
    User input: "{user_input}".
    Determine the user's intent based on these rules:
    - To continue the game, return: "{UNIQUE_KEYWORDS['continue']}".
    - To end the game, return: "{UNIQUE_KEYWORDS['end']}".
    - To ask about the score or points (e.g., "What is my current score?", "How many points do I have?", etc.), return: "{UNIQUE_KEYWORDS['score']}".
    - If the intent is unclear, return: "{UNIQUE_KEYWORDS['unsure']}".
    Respond with only one of these identifiers: "{', '.join(UNIQUE_KEYWORDS.values())}".
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that helps identify user intent."},
            {"role": "user", "content": prompt}
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
def listen_and_respond(point_queue, event_queue):
    print("""Hello, I am your badminton practice partner, and you can call me PiPi.
                 We have two rounds of practice: the first round is to familiarize yourself with the rules of singles badminton,
                 and the second round is to practice badminton hitting techniques.
                 Now, please stand in the position opposite me, and I will introduce the rules of singles badminton.""")
    generate_tts("""Hello, I am your badminton practice partner, and you can call me PiPi.
                 We have two rounds of practice: the first round is to familiarize yourself with the rules of singles badminton,
                 and the second round is to practice badminton hitting techniques.
                 Now, please stand in the position opposite me, and I will introduce the rules of singles badminton.
                  """)

    robot_commander = RobotCommander.RobotCommander()

    while True:
        client_input = listen()
        # await asyncio.sleep(1)
        if client_input:
            client_input = client_input = client_input.strip().lower()
            print(client_input)

        intent = process_user_input(client_input)
        # intent = "98asds8hjw"
        # Act based on the intent
        match intent:
            case "GPTCODE_CONTINUE": # match "continue"
                generate_tts("The game continues!")
                print("The game continues!")
            case "GPTCODE_END":  # match "end"
                generate_tts("The game has ended! Thank you for playing!")
                print("The game has ended! Thank you for playing!")
                break
            case "GPTCODE_SCORE":  # match "score"
                event = Event()
                event_queue.put(event)
                event.wait()
                score = point_queue.get()
                generate_tts(f"Your current score is {score} points.")
                print(f"Your current score is {score} points.")
            case "GPTCODE_TURN_LEFT":
                robot_commander.send_command("LEFT")
                generate_tts("Turning left")
                print("Turning left")
            case "GPTCODE_TURN_RIGHT":
                robot_commander.send_command("RIGHT")
                generate_tts("Turning right")
                print("Turning right")
            case _:  # match "unsure"
                generate_tts("I couldn't understand your intent. Please try again.")
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

    """

# obtain audio from the microphone
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something!")
    audio = r.listen(source)
# recognize speech using Whisper API
try:
    client_input = r.recognize_whisper_api(audio, api_key=OpenAI.api_key)
    print(f"Whisper API thinks you said {client_input}")
except sr.RequestError as e:
    print(f"Could not request results from Whisper API; {e}")



# Creating the request
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="I love u",
)

# Writing streamed content to a file
with open("output.mp3", "wb") as output_file:
    for chunk in response.iter_bytes():
        output_file.write(chunk)


#Speech to text
audio_file= open("output.mp3", "rb")

transcription = client.audio.transcriptions.create(
  model="whisper-1",
  file=audio_file
)
print(transcription.text)
"""




