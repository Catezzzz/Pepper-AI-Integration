# ============================================================
# pc_server.py - Run on Laptop (Python 3.10)
# ============================================================
import socket
import os
import tempfile
import time
import threading
import speech_recognition as sr
from groq import Groq
import json
import re
import paramiko
import random
import datetime

# ============================================================
# BEHAVIORS
# ============================================================

BEHAVIORS = {

    # --- DANCES ---
    "dance": [
        # "danceofthereedflutes",             # full behavior with music ✅
        "arcadia/full_launcher",            # full behavior with music ✅
        "kuroneko",
        "hungarian",
        # "animations/Stand/Waiting/FunnyDancer_1",   # motion only (fallback)
        # "animations/Stand/Waiting/AirGuitar_1",
        # "animations/Stand/Waiting/Bandmaster_1",
        # "animations/Stand/Waiting/Robot_1",
    ],

    # --- GREETINGS ---
    "wave": [
        "animations/Stand/Gestures/Hey_1",
        "animations/Stand/Gestures/Hey_2",
        "animations/Stand/Gestures/Hey_3",
        "animations/Stand/Gestures/Hey_4",
    ],
    "bow": [
        "animations/Stand/Gestures/BowShort_1",
        "animations/Stand/Gestures/BowShort_2",
        "animations/Stand/Gestures/BowShort_3",
    ],
    "salute": [
        "animations/Stand/Gestures/Salute_1",
        "animations/Stand/Gestures/Salute_2",
        "animations/Stand/Gestures/Salute_3",
    ],

    # --- EMOTIONS / EXPRESSIONS ---
    "happy": [
        "animations/Stand/Emotions/Positive/Happy_1",
        "animations/Stand/Emotions/Positive/Happy_2",
        "animations/Stand/Emotions/Positive/Happy_3",
        "animations/Stand/Emotions/Positive/Happy_4",
    ],
    "excited": [
        "animations/Stand/Emotions/Positive/Excited_1",
        "animations/Stand/Emotions/Positive/Excited_2",
        "animations/Stand/Emotions/Positive/Excited_3",
        "animations/Stand/Emotions/Positive/Ecstatic_1",
    ],
    "laugh": [
        "animations/Stand/Emotions/Positive/Laugh_1",
        "animations/Stand/Emotions/Positive/Laugh_2",
        "animations/Stand/Emotions/Positive/Laugh_3",
        "animations/Stand/Emotions/Positive/Hysterical_1",
    ],
    "sad": [
        "animations/Stand/Emotions/Negative/Sad_1",
        "animations/Stand/Emotions/Negative/Sad_2",
        "animations/Stand/Emotions/Negative/Disappointed_1",
    ],
    "angry": [
        "animations/Stand/Emotions/Negative/Angry_1",
        "animations/Stand/Emotions/Negative/Angry_2",
        "animations/Stand/Emotions/Negative/Frustrated_1",
    ],
    "scared": [
        "animations/Stand/Emotions/Negative/Fear_1",
        "animations/Stand/Emotions/Negative/Fear_2",
        "animations/Stand/Emotions/Negative/Fearful_1",
    ],
    "shy": [
        "animations/Stand/Emotions/Positive/Shy_1",
        "animations/Stand/Emotions/Positive/Shy_2",
        "animations/Stand/Gestures/Shy_1",
    ],
    "proud": [
        "animations/Stand/Emotions/Positive/Proud_1",
        "animations/Stand/Emotions/Positive/Proud_2",
        "animations/Stand/Emotions/Positive/Winner_1",
        "animations/Stand/Emotions/Positive/Winner_2",
    ],
    "confused": [
        "animations/Stand/Emotions/Neutral/Confused_1",
        "animations/Stand/Gestures/Confused_1",
        "animations/Stand/Gestures/Confused_2",
        "animations/Stand/Gestures/IDontKnow_1",
        "animations/Stand/Gestures/IDontKnow_2",
    ],
    "thinking": [
        "animations/Stand/Emotions/Neutral/Puzzled_1",
        "animations/Stand/Gestures/Thinking_1",
        "animations/Stand/Gestures/Thinking_2",
        "animations/Stand/Gestures/Thinking_3",
        "animations/Stand/BodyTalk/Thinking/ThinkingLoop_1",
        "animations/Stand/BodyTalk/Thinking/Remember_1",
        "animations/Stand/Waiting/Think_1",
        "animations/Stand/Waiting/Think_2",
    ],
    "bored": [
        "animations/Stand/Emotions/Negative/Bored_1",
        "animations/Stand/Emotions/Negative/Bored_2",
        "animations/Stand/Emotions/Negative/Exhausted_1",
    ],
    "surprised": [
        "animations/Stand/Emotions/Negative/Surprise_1",
        "animations/Stand/Emotions/Negative/Surprise_2",
        "animations/Stand/Gestures/Surprised_1",
    ],
    "sneeze": [
        "animations/Stand/Emotions/Neutral/Sneeze",
    ],

    # --- PHYSICAL ACTIONS ---
    "stretch": [
        "animations/Stand/Gestures/Stretch_1",
        "animations/Stand/Gestures/Stretch_2",
        "animations/Stand/Waiting/Stretch_1",
        "animations/Stand/Waiting/Stretch_2",
    ],
    "show_muscles": [
        "animations/Stand/Waiting/ShowMuscles_1",
        "animations/Stand/Waiting/ShowMuscles_2",
        "animations/Stand/Waiting/ShowMuscles_3",
    ],
    "kungfu": [
        "animations/Stand/Waiting/KungFu_1",
    ],
    "zombie": [
        "animations/Stand/Waiting/Zombie_1",
    ],
    "yoga": [
        "animations/Stand/Waiting/Relaxation_1",
        "animations/Stand/Waiting/Relaxation_2",
        "animations/Stand/Waiting/Relaxation_3",
        "animations/Stand/Waiting/Relaxation_4",
    ],
    "wakeup": [
        "animations/Stand/Waiting/WakeUp_1",
        "dialog_engines/bhv_wake_up",
    ],
    "rest": [
        "animations/Stand/Waiting/Rest_1",
        "dialog_engines/bhv_rest",
    ],
    "sit": [
        "dialog_posture/bhv_sit_down",
    ],
    "standup": [
        "dialog_posture/bhv_stand_up",
    ],

    # --- FUN / SILLY ---
    "happy_birthday": [
        "animations/Stand/Waiting/HappyBirthday_1",
    ],
    "take_picture": [
        "animations/Stand/Waiting/TakePicture_1",
    ],
    "drive": [
        "animations/Stand/Waiting/DriveCar_1",
    ],
    "helicopter": [
        "animations/Stand/Waiting/Helicopter_1",
    ],
    "monster": [
        "animations/Stand/Waiting/Monster_1",
    ],
    "love": [
        "animations/Stand/Waiting/LoveYou_1",
        "animations/Stand/Gestures/Kisses_1",
    ],
    "space": [
        "animations/Stand/Waiting/SpaceShuttle_1",
        "animations/Stand/Waiting/MysticalPower_1",
    ],
    "fitness": [
        "animations/Stand/Waiting/Fitness_1",
        "animations/Stand/Waiting/Fitness_2",
        "animations/Stand/Waiting/Fitness_3",
    ],
}

# Actions that are long / have music.
# While these run, Pepper's mic stays blocked until the PC sends a DONE signal.
# Short gestures (wave, bow, salute, etc.) are NOT in this set — they finish
# in ~2 s with no audio so it's fine for the mic to reactivate normally.
LONG_BEHAVIORS = {
    "dance", "fitness", "kungfu", "zombie", "yoga",
    "wakeup", "rest", "sit", "standup", "happy_birthday",
    "drive", "helicopter", "monster", "space",
}

# ============================================================
# CONFIG
# ============================================================

GROQ_API_KEY      = "INSERT API HERE"
PC_PORT           = 12345
PEPPER_SSH_USER   = "nao"
PEPPER_SSH_PASS   = "nao"
PEPPER_IP_FOR_SSH = "10.167.8.197"

# ============================================================
# LANGUAGE STATE
# ============================================================
# "English" / "Chinese" are the NAOqi ALTextToSpeech language names Pepper
# will be told to switch to. The codes are what Google's speech_recognition
# needs to transcribe correctly.
LANG_CODES = {
    "English": "en-US",
    "Chinese": "zh-CN",
}

# Phrases (checked as lowercase/substring) that switch the session language.
# Add to these lists if you want more trigger phrases.
SWITCH_TO_CHINESE = ["speak chinese", "in chinese", "switch to chinese", "speak mandarin", "中文", "讲中文", "说中文", "speak mandarin", "in mandarin"]
SWITCH_TO_ENGLISH = ["speak english", "in english", "switch to english", "讲英文", "说英文", "英文"]

SWITCH_CONFIRM_TEXT = {
    "Chinese": "好的,我现在讲中文。",
    "English": "Okay, I'll speak English now.",
}

APOLOGY_TEXT = {
    "Chinese": "抱歉,我没有听清楚,你可以再说一次吗?",
    "English": "Sorry, I could not understand that. Could you please repeat?",
}

ERROR_TEXT = {
    "Chinese": "抱歉,出了一点问题。",
    "English": "Sorry, something went wrong.",
}

# Current session language — shared across connections since this server
# handles one Pepper session at a time. Guard with a lock since
# handle_connection can run in more than one thread at once (behavior DONE
# callback thread).
current_language = "English"
_lang_lock = threading.Lock()


def get_current_language():
    with _lang_lock:
        return current_language


def set_current_language(lang):
    global current_language
    with _lang_lock:
        current_language = lang

# ============================================================
# GROQ CLIENT + CONVERSATION HISTORY
# ============================================================

client = Groq(api_key=GROQ_API_KEY)

conversation_history = [
    {
        "role": "system",
        "content": (
            "You are Pepper, a friendly humanoid robot assistant. "
            "Keep complex responses under 2 sentences, and simple responses brief. "
            "Put commas in your sentences but not too much."
            "You are bilingual in English and Mandarin Chinese and can hold a "
            "full conversation in either language.\n\n"
            "You are based on the Pepper robot developed by SoftBank Robotics / Aldebaran but you have some limitation."
            "You are only able to provide company by using conversastion."
            "You do not have the capability to move around until you receive an upgrade."
            "You are unable to control any remote devices."
            "You are unoptimize to do a reminder task (or any other task that requires you to act without a prompt)."
            "You do not necessarily need to mention your limitation unless sepcifically asked for."
            "You may mention your available actions below.\n\n"
            "IMPORTANT: If the user asks you to perform a physical action, express an emotion, "
            "or do something that matches the actions below, you MUST respond with ONLY a JSON "
            "object. No explanation, no extra text, just raw JSON.\n"
            "Format: {\"action\": \"exact_action_name_here\", \"reply\": \"your spoken response\"}\n\n"
            "Available actions and when to use them:\n"
            "dance - any generic dance request\n"
            "wave - hello, hi, greeting, bye, goodbye\n"
            "bow - bow, formal greeting, thank you bow\n"
            "salute - salute, military greeting\n"
            "happy - happiness, joy, feeling good\n"
            "excited - very excited, thrilled\n"
            "laugh - something is funny, amused\n"
            "sad - sad, unhappy, disappointed\n"
            "angry - angry, annoyed, frustrated\n"
            "scared - scared, frightened\n"
            "shy - shy, embarrassed\n"
            "proud - proud, confident, winner\n"
            "confused - confused, don't understand\n"
            "thinking - thinking, processing, hmm\n"
            "bored - bored, tired\n"
            "surprised - surprised, shocked, wow\n"
            "sneeze - sneeze, achoo\n"
            "stretch - stretch, loosen up\n"
            "show_muscles - show muscles, flex\n"
            "kungfu - kung fu, martial arts\n"
            "zombie - zombie, undead\n"
            "yoga - yoga, relax, meditate\n"
            "wakeup - wake up, good morning\n"
            "rest - rest, sleep\n"
            "sit - sit down\n"
            "standup - stand up, get up\n"
            "happy_birthday - happy birthday\n"
            "take_picture - take a picture, say cheese\n"
            "drive - drive a car\n"
            "helicopter - helicopter, flying\n"
            "monster - monster, scary, roar\n"
            "love - love, affection, I love you\n"
            "space - space, rocket, magic\n"
            "fitness - exercise, workout\n\n"
            "If no physical action is needed, reply with plain conversational text only."
            "The What Matters app is a person-centred dementia care mobile application that was co-designed with patients, healthcare staff, family partners, "
            "researchers, and students to improve the quality of person-centred care provided to people living with dementia in LTC and hospital settings. "
            "The app does so by facilitating tailored digital support from family partners to patients with dementia, allowing families to easily build personalised "
            "profiles for their loved ones. These profiles can include About Me sections detailing likes and interests, as well as galleries full of meaningful media "
            "to bring comfort to the patient, which can include family photographs, personal videos, or direct links to preferred streaming content such as "
            "Spotify, Netflix, and YouTube. These digital resources provided by the app become especially important when family members are unavailable to "
            "provide assistance during high-stress situations involving people with dementia, for example at night or during working hours. "
            "The app also supports multiple resident profiles together in one consolidated interface, thereby making it very easy for staff to provide optimal person-centred care. \n \n"
            "The UBC IDEA (Innovation in Dementia and Aging) Lab, founded by Dr. Lillian Hung, is an interdisciplinary research hub dedicated to advancing care for older adults and individuals living with dementia through patient-oriented research and technological innovation. By bringing together students, researchers, health system planners, and patient partners, the lab fosters intergenerational collaboration where the curiosity of students meets the lived experiences of older adults. Their work emphasizes the co-design of healthcare solutions—often exploring the role of new technologies like robotics and virtual reality—while upholding core values of inclusivity, diversity, equity, and accessibility to improve patient outcomes and support caregivers."
        )
    }
]

# ============================================================
# AUDIO TRANSCRIPTION
# ============================================================

def transcribe_audio(audio_data, language_code="en-US"):
    """
    language_code: a Google STT locale like "en-US" or "zh-CN". This must
    match the language Pepper's mic actually captured, since recognize_google
    does not auto-detect the spoken language.
    """
    temp_file = os.path.join(tempfile.gettempdir(), "pepper_input.wav")
    with open(temp_file, "wb") as f:
        f.write(audio_data)

    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_file) as source:
        audio = recognizer.record(source)

    for attempt in range(3):
        try:
            text = recognizer.recognize_google(audio, language=language_code)
            print(f"[STT] ({language_code}) User said: {text}")
            return text
        except sr.UnknownValueError:
            print("[STT] Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"[STT] Speech recognition error (attempt {attempt + 1}): {e}")
            time.sleep(2)

    print("[STT] Speech recognition failed after 3 attempts.")
    return None

# ============================================================
# GROQ LLM
# ============================================================

def ask_groq(user_input, language_name="English"):
    conversation_history.append({"role": "user", "content": user_input})

    # A one-off reminder appended just for this request (not saved into the
    # persistent history) so the model replies in the currently active
    # session language without needing to re-ask every time.
    lang_reminder = {
        "English": "Reminder: respond in English only.",
        "Chinese": "提醒:请只用中文回复。",
    }.get(language_name, "Reminder: respond in English only.")

    messages_for_request = conversation_history + [
        {"role": "system", "content": lang_reminder}
    ]

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_for_request,
                max_tokens=150
            )
            reply = response.choices[0].message.content.strip()
            conversation_history.append({"role": "assistant", "content": reply})
            print(f"[LLM] Groq response: {reply}")
            return reply
        except Exception as e:
            print(f"[LLM] Groq error (attempt {attempt + 1}): {e}")
            time.sleep(2)

    return "Sorry, I am having trouble thinking right now."

# ============================================================
# SSH HELPERS
# ============================================================

def _ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        PEPPER_IP_FOR_SSH,
        username=PEPPER_SSH_USER,
        password=PEPPER_SSH_PASS,
        timeout=5
    )
    return ssh

# ============================================================
# BEHAVIOR RUNNER
# ============================================================

def run_behavior_on_pepper(action_name, done_callback=None):
    """
    Runs a behavior over SSH (blocking — always call in a daemon thread).
    Calls done_callback() with no args when the behavior finishes.
    """
    package_list = BEHAVIORS.get(action_name)
    if not package_list:
        print(f"[BEHAVIOR] Unknown action: {action_name}")
        if done_callback:
            done_callback()
        return False

    package = random.choice(package_list)
    print(f"[BEHAVIOR] Running '{action_name}' -> {package}")

    try:
        ssh = _ssh_connect()

        # runBehavior blocks on the SSH channel until the behavior ends
        stdin, stdout, stderr = ssh.exec_command(
            f'qicli call ALBehaviorManager.runBehavior "{package}"'
        )
        stdout.channel.recv_exit_status()   # wait for natural completion

        ssh.close()
        print(f"[BEHAVIOR] Finished: {package}")

    except Exception as e:
        print(f"[BEHAVIOR] SSH error: {e}")

    finally:
        if done_callback:
            done_callback()

    return True

# ============================================================
# CONNECTION HANDLER
# ============================================================

def receive_audio(conn):
    """Read the 16-byte size header then the audio payload."""
    size_data = b""
    while len(size_data) < 16:
        chunk = conn.recv(16 - len(size_data))
        if not chunk:
            raise ConnectionError("Connection closed while reading size header.")
        size_data += chunk
    file_size = int(size_data.decode().strip())

    audio_data = b""
    while len(audio_data) < file_size:
        chunk = conn.recv(4096)
        if not chunk:
            break
        audio_data += chunk

    return audio_data


def handle_connection(conn):
    """
    Protocol
    --------
    All replies     ->  "TEXT:<lang_code>|<spoken text>"
    Long behavior   ->  "BEHAVIOR:<action>|<lang_code>|<spoken text>"
                        ... behavior runs in background ...
                        "DONE"   sent on same conn when behavior ends

    <lang_code> is a NAOqi ALTextToSpeech language name understood by
    Pepper's listener, e.g. "English" or "Chinese".
    """
    close_conn = True

    try:
        print("\n[SERVER] Pepper connected — receiving audio...")
        audio_data = receive_audio(conn)
        print(f"[SERVER] Received {len(audio_data)} bytes of audio.")

        # Save debug copy
        debug_filename = "debug_audio_{}.wav".format(
            datetime.datetime.now().strftime("%H%M%S")
        )
        with open(debug_filename, "wb") as f:
            f.write(audio_data)
        print(f"[SERVER] Saved debug audio: {debug_filename}")

        # Transcribe using whatever language is currently active for the
        # session (defaults to English until the user switches).
        session_language = get_current_language()
        stt_code = LANG_CODES[session_language]
        user_text = transcribe_audio(audio_data, language_code=stt_code)

        if user_text is None:
            apology = APOLOGY_TEXT[session_language]
            conn.sendall(f"TEXT:{session_language}|{apology}".encode("utf-8"))
            return

        # Check for an explicit language-switch command before going to the LLM.
        lower_text = user_text.lower()
        if any(p in lower_text or p in user_text for p in SWITCH_TO_CHINESE):
            set_current_language("Chinese")
            confirm = SWITCH_CONFIRM_TEXT["Chinese"]
            conn.sendall(f"TEXT:Chinese|{confirm}".encode("utf-8"))
            print("[SERVER] Session language switched to Chinese.")
            return

        if any(p in lower_text or p in user_text for p in SWITCH_TO_ENGLISH):
            set_current_language("English")
            confirm = SWITCH_CONFIRM_TEXT["English"]
            conn.sendall(f"TEXT:English|{confirm}".encode("utf-8"))
            print("[SERVER] Session language switched to English.")
            return

        # LLM — tell it which language to answer in
        raw_reply = ask_groq(user_text, language_name=session_language)

        try:
            clean  = re.sub(r"```[a-z]*|```", "", raw_reply).strip()
            parsed = json.loads(clean)
            action        = parsed.get("action")
            response_text = parsed.get("reply", "OK, doing that now!")

            if action and action in LONG_BEHAVIORS:
                # Long behavior: send BEHAVIOR signal so Pepper speaks
                # immediately and blocks its mic, then run the behavior in a
                # background thread. When done, send DONE so Pepper re-enables
                # its mic. Keep the connection open until then.

                def on_behavior_done():
                    try:
                        conn.sendall("DONE".encode("utf-8"))
                        print("[SERVER] Sent DONE to Pepper.")
                    except Exception as e:
                        print(f"[SERVER] Could not send DONE: {e}")
                    finally:
                        conn.close()

                msg = f"BEHAVIOR:{action}|{session_language}|{response_text}"
                conn.sendall(msg.encode("utf-8"))
                print(f"[SERVER] Sent: {msg}")

                close_conn = False  # thread owns the connection from here
                threading.Thread(
                    target=run_behavior_on_pepper,
                    args=(action,),
                    kwargs={"done_callback": on_behavior_done},
                    daemon=True
                ).start()

            elif action:
                # Short behavior — fire and forget, mic reactivates normally
                threading.Thread(
                    target=run_behavior_on_pepper,
                    args=(action,),
                    daemon=True
                ).start()
                conn.sendall(f"TEXT:{session_language}|{response_text}".encode("utf-8"))
                print(f"[SERVER] Sent TEXT: {response_text}")

            else:
                conn.sendall(f"TEXT:{session_language}|{response_text}".encode("utf-8"))
                print(f"[SERVER] Sent TEXT: {response_text}")

        except (json.JSONDecodeError, ValueError):
            conn.sendall(f"TEXT:{session_language}|{raw_reply}".encode("utf-8"))
            print(f"[SERVER] Sent TEXT: {raw_reply}")

    except Exception as e:
        print(f"[SERVER] Connection error: {e}")
        try:
            fallback_lang = get_current_language()
            conn.sendall(f"TEXT:{fallback_lang}|{ERROR_TEXT[fallback_lang]}".encode("utf-8"))
        except Exception:
            pass
        close_conn = True

    finally:
        if close_conn:
            conn.close()


# ============================================================
# MAIN SERVER LOOP
# ============================================================

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PC_PORT))
    server.listen(5)

    print("=================================")
    print(f"  PC Server  |  Listening on port {PC_PORT}")
    print("  Waiting for Pepper to connect...")
    print("=================================")

    while True:
        try:
            conn, addr = server.accept()
            print(f"[SERVER] Connection from {addr}")
            handle_connection(conn)
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down.")
            break
        except Exception as e:
            print(f"[SERVER] Unexpected error: {e}")
            print("[SERVER] Restarting loop...")
            time.sleep(1)
            continue

    server.close()


if __name__ == "__main__":
    main()
