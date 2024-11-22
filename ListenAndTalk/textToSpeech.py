from openai import OpenAI
import openai
from dotenv import dotenv_values
import speech_recognition as sr
import time

# Initialize OpenAI client
OpenAI.api_key = dotenv_values('.env')["API_KEY"]
client = OpenAI(api_key=OpenAI.api_key)
#client_input = None

score = 0
keywords = ["serve target area", "Hit the target area","RightRectangle","LeftRectangle"]


#Respond with a preset action from Robot(Text to Speech)
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
#generate_tts("move forward")


#Automatic Response from OpenAi
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


# Robot logic based on recognized commands
def robot_action(command):
    if "yes" in command:
        print("Robot executing: drive Rectangle and ExplainServeTargetArea")
        generate_tts("""Please remember that when starting the serve, the shuttle should be served to the diagonal court. 
                     I will now walk around the hitting area, please observe carefully.""")
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
        

#obtain audio from the microphone
def listen():
 while True:
     recognizer = sr.Recognizer()
     with sr.Microphone() as source:
        print("Say something!")
        try:
            audio = recognizer.listen(source,timeout=5, phrase_time_limit=10)
            client_input = recognizer.recognize_whisper_api(audio, api_key=OpenAI.api_key)
            print(f"Recognized command: {client_input}")   
            return client_input
        except sr.WaitTimeoutError:
           print("No input detected within timeout")
           return None
        except sr.UnknownValueError:
            print("Could not understand the audio.")
           # return generate_tts("I could not understand what you said.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Whisper API; {e}")
          #  return generate_tts("There was an error processing your request.")
            return None

        # Speech recognition and command handling
def listen_and_respond():
    print("""Hello, I am your badminton practice partner, and you can call me PiPi. 
                 We have two rounds of practice: the first round is to familiarize yourself with the rules of singles badminton, 
                 and the second round is to practice badminton hitting techniques.
                 Now, please stand in the position opposite me, and I will introduce the rules of singles badminton.""")
    generate_tts("""Hello, I am your badminton practice partner, and you can call me PiPi. 
                 We have two rounds of practice: the first round is to familiarize yourself with the rules of singles badminton, 
                 and the second round is to practice badminton hitting techniques.
                 Now, please stand in the position opposite me, and I will introduce the rules of singles badminton.
                  """)
    generate_tts("Are you in position")
    print("Are you in position")
    while True:
        client_input = listen()
        if client_input:
            client_input = client_input.lower()
            print(client_input)
            if "stop" in client_input:
                generate_tts("Ending the session. Goodbye!")
                break
            if not robot_action(client_input):
                generate_tts("Sorry, I didn't understand the command.")
        else:
            print("Player did not respond.")

listen_and_respond()
    
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




