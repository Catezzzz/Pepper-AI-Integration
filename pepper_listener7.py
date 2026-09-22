# -*- coding: utf-8 -*-
# pepper_listener.py - Python 2.7, NAOqi
# Now with rms logging, and return to posture after animated speech
import sys
import os
import socket
import wave
import time
import audioop
import threading
from naoqi import ALProxy, ALModule, ALBroker

PEPPER_IP   = "10.167.8.197"
PEPPER_PORT = 9559
PC_IP       = "10.167.8.216"
PC_PORT     = 12345

ACTIVATION_THRESHOLD = 1700
SILENCE_THRESHOLD    = 1450
MAX_TOTAL_DURATION   = 16.0  # hard ceiling — stops here regardless
SILENCE_AFTER        = 1
MIN_DURATION         = 4.0
SAMPLE_RATE          = 16000

# Path to the tablet HTML file deployed alongside this script
TABLET_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "pepper_status.html")

tts     = ALProxy("ALTextToSpeech",   PEPPER_IP, PEPPER_PORT)
anim    = ALProxy("ALAnimatedSpeech", PEPPER_IP, PEPPER_PORT)
leds    = ALProxy("ALLeds",           PEPPER_IP, PEPPER_PORT)
tablet  = ALProxy("ALTabletService",  PEPPER_IP, PEPPER_PORT)

anim_config = {"bodyLanguageMode": "contextual"}

# NAOqi ALTextToSpeech language names. These must exactly match what
# tts.getAvailableLanguages() reports on your robot (usually "English" and
# "Chinese" for Mandarin, but some images use "Mandarin" instead — check
# once with print(tts.getAvailableLanguages()) if setLanguage errors out).
DEFAULT_LANGUAGE = "English"
_current_tts_language = None  # tracked so we don't call setLanguage needlessly


def set_pepper_language(language_name):
    """Switch Pepper's TTS/AnimatedSpeech voice language if it isn't already set."""
    global _current_tts_language
    if isinstance(language_name, unicode):
        language_name = language_name.encode("utf-8")
    if language_name == _current_tts_language:
        return
    try:
        tts.setLanguage(language_name)
        _current_tts_language = language_name
        print("TTS language set to: " + language_name)
    except Exception as e:
        print("Could not set TTS language to '" + language_name + "': " + str(e))


# ============================================================
# TABLET STATUS
# ============================================================

def set_tablet_status(state):
    """
    Push a status update to the tablet UI.
    state: one of 'listening', 'thinking', 'speaking', 'acting'
    """
    try:
        js = "window.setStatus('{0}');".format(state)
        tablet.executeJS(js)
    except Exception as e:
        print("Tablet JS error: " + str(e))


def init_tablet():
    """Load the status page on Pepper's tablet."""
    try:
        tablet.showWebview("http://198.18.0.1/apps/pepperlistenerstatus-3021b6/pepper_status.html")
        time.sleep(1.0)   # give the page time to render
        set_tablet_status("waiting")
    except Exception as e:
        print("Tablet init error: " + str(e))


# ============================================================
# MIC MODULE
# ============================================================

class PepperMic(ALModule):
    """
    Subscribes to ALAudioDevice for gapless PCM streaming.
    State machine: WAITING -> RECORDING -> DONE

    Stop logic:
      - 0.8s of silence after at least MIN_DURATION seconds recorded
      - Hard ceiling at MAX_TOTAL_DURATION regardless
    """

    def __init__(self, name):
        ALModule.__init__(self, name)
        self.audio = ALProxy("ALAudioDevice", PEPPER_IP, PEPPER_PORT)

        self._frames        = []
        self._state         = "WAITING"
        self._silent_time   = 0.0
        self._recorded_time = 0.0
        self._last_rms      = 0
        self._lock          = threading.Lock()
        self._last_rms_log  = 0.0   # wall-clock time of last RMS print

    def listen(self):
        """Block until a complete utterance is captured. Returns WAV bytes."""
        with self._lock:
            self._frames        = []
            self._state         = "WAITING"
            self._silent_time   = 0.0
            self._recorded_time = 0.0
            self._last_rms      = 0
            self._last_rms_log  = 0.0

        leds.fadeRGB("FaceLeds", 0xFB00FF40, 0.3)

        self.audio.setClientPreferences(self.getName(), SAMPLE_RATE, 3, 0)
        self.audio.subscribe(self.getName())

        try:
            while True:
                with self._lock:
                    state = self._state
                if state == "DONE":
                    break
                time.sleep(0.05)
        finally:
            self.audio.unsubscribe(self.getName())

        with self._lock:
            raw = b"".join(self._frames)

        return self._to_wav(raw)

    def processRemote(self, channels, samples, timestamp, buffer):
        pcm = str(bytearray(buffer))
        if len(pcm) == 0:
            return

        rms = audioop.rms(pcm, 2)
        buf_duration = len(pcm) / 2.0 / SAMPLE_RATE

        with self._lock:
            self._last_rms = rms

            # ── RMS heartbeat log (once per second) ───────────────────────
            now = time.time()
            if now - self._last_rms_log >= 1.0:
                print("[RMS] state={0} rms={1} recorded={2:.2f}s silence={3:.2f}s".format(
                    self._state, rms,
                    self._recorded_time,
                    self._silent_time))
                self._last_rms_log = now

            if self._state == "WAITING":
                if rms > ACTIVATION_THRESHOLD:
                    print("Activated! RMS=" + str(rms))
                    leds.fadeRGB("FaceLeds", 0x0000FF, 0.2)
                    set_tablet_status("listening")
                    self._state         = "RECORDING"
                    self._frames.append(pcm)
                    self._recorded_time = buf_duration
                    self._silent_time   = 0.0

            elif self._state == "RECORDING":
                self._frames.append(pcm)
                self._recorded_time += buf_duration

                if rms < SILENCE_THRESHOLD:
                    self._silent_time += buf_duration
                else:
                    self._silent_time = 0.0

                if self._recorded_time >= MAX_TOTAL_DURATION:
                    print("Stopping: hard ceiling | recorded=" +
                          str(round(self._recorded_time, 2)) + "s")
                    leds.fadeRGB("FaceLeds", 0x00FF00, 0.3)
                    self._state = "DONE"

                elif (self._silent_time  >= SILENCE_AFTER and
                      self._recorded_time >= MIN_DURATION):
                    print("Stopping: silence | recorded=" +
                          str(round(self._recorded_time, 2)) + "s")
                    leds.fadeRGB("FaceLeds", 0x00FF00, 0.3)
                    self._state = "DONE"

    @staticmethod
    def _to_wav(pcm_bytes):
        import io
        buf = io.BytesIO()
        wf = wave.open(buf, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)
        wf.close()
        return buf.getvalue()


# ============================================================
# NETWORK
# ============================================================

def send_audio_get_response(wav_bytes):
    """
    Send WAV to PC, return (response_string, socket_or_None).

    For TEXT responses the server closes the socket — returns (text, None).
    For BEHAVIOR responses the socket stays open for the DONE signal
    — returns (behavior_msg, open_socket).
    """
    print("Sending audio to PC...")
    set_tablet_status("thinking")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((PC_IP, PC_PORT))
    sock.sendall(str(len(wav_bytes)).zfill(16).encode())
    sock.sendall(wav_bytes)

    response = ""
    while True:
        chunk = sock.recv(1024)
        if not chunk:
            break
        response += chunk.decode("utf-8")
        if response.startswith("TEXT:") or response.startswith("BEHAVIOR:"):
            break

    if response.startswith("BEHAVIOR:"):
        return response.strip(), sock   # keep socket open for DONE

    sock.close()
    return response.strip(), None


def wait_for_done(sock):
    """Block until the PC sends DONE on the open socket, then close it."""
    sock.settimeout(120)
    try:
        data = ""
        while "DONE" not in data:
            chunk = sock.recv(64)
            if not chunk:
                break
            data += chunk.decode("utf-8")
        print("Received DONE from PC.")
    except Exception as e:
        print("wait_for_done error: " + str(e))
    finally:
        try:
            sock.close()
        except Exception:
            pass


# ============================================================
# SPEECH
# ============================================================

def pepper_speak(text, language=DEFAULT_LANGUAGE):
    # Normalize to plain str up front — language may arrive as a unicode
    # object (split from the decoded socket payload), and mixing unicode
    # with utf-8-encoded str bytes later causes ascii decode errors, and
    # NAOqi's setLanguage() rejects unicode outright.
    if isinstance(language, unicode):
        language = language.encode("utf-8")

    set_pepper_language(language)
    if isinstance(text, unicode):
        text = text.encode("utf-8")
    print("Pepper says (" + language + "): " + text)
    set_tablet_status("speaking")
    try:
        anim.say(text, anim_config)   # blocking — returns when speech finishes
    except Exception as e:
        print("Animated speech failed: " + str(e))
        tts.say(text)
    try:
        posture = ALProxy("ALRobotPosture", PEPPER_IP, PEPPER_PORT)
        posture.goToPosture("Stand", 0.6)
    except Exception as e:
        print("Posture reset failed: " + str(e))


# ============================================================
# STARTUP HELPERS
# ============================================================

def setup_robot_state():
    """
    Wake Pepper (ALRobotPosture → Stand) and disable Autonomous Life
    so he won't wander or speak on his own during the session.
    """
    try:
        life = ALProxy("ALAutonomousLife", PEPPER_IP, PEPPER_PORT)
        if life.getState() != "disabled":
            life.setState("disabled")
            print("Autonomous life: disabled")
        else:
            print("Autonomous life: already disabled, skipping")
    except Exception as e:
        print("Could not disable autonomous life: " + str(e))

    try:
        motion = ALProxy("ALMotion", PEPPER_IP, PEPPER_PORT)
        motion.wakeUp()
        print("Motors: awake")
    except Exception as e:
        print("Could not wake up motors: " + str(e))

    try:
        posture = ALProxy("ALRobotPosture", PEPPER_IP, PEPPER_PORT)
        posture.goToPosture("Stand", 0.6)
        print("Posture: Stand")
    except Exception as e:
        print("Could not set posture: " + str(e))


# ============================================================
# MAIN
# ============================================================

def main():
    broker = ALBroker("myBroker", "0.0.0.0", 0, PEPPER_IP, PEPPER_PORT)

    # ── Robot state setup ──────────────────────────────────────────────────
    setup_robot_state()

    # ── Tablet UI ──────────────────────────────────────────────────────────
    init_tablet()

    global mic_module
    mic_module = PepperMic("mic_module")

    print("Pepper Listener ready.")
    pepper_speak("Hello! I am ready to chat. How can I help you?")

    try:
        while True:
            # Show waiting (pink) until voice activates, then mic sets listening
            set_tablet_status("waiting")
            wav_bytes = mic_module.listen()

            response, behavior_sock = send_audio_get_response(wav_bytes)

            if not response:
                pepper_speak("Sorry, I did not get a response. Please try again.")
                continue

            if response.startswith("TEXT:"):
                payload = response[len("TEXT:"):]
                if "|" in payload:
                    language, text = payload.split("|", 1)
                else:
                    # Backward-compatible fallback if the server didn't tag a language
                    language, text = DEFAULT_LANGUAGE, payload

                if "goodbye" in text.lower() or u"再见" in text:
                    pepper_speak("Goodbye! It was nice talking to you.", DEFAULT_LANGUAGE)
                    break

                pepper_speak(text, language)
                time.sleep(0.4)

            elif response.startswith("BEHAVIOR:") and behavior_sock is not None:
                payload = response[len("BEHAVIOR:"):]
                parts = payload.split("|", 2)
                if len(parts) == 3:
                    action_name, language, spoken = parts
                elif len(parts) == 2:
                    action_name, spoken = parts
                    language = DEFAULT_LANGUAGE
                else:
                    action_name, spoken, language = parts[0], "OK, here we go!", DEFAULT_LANGUAGE

                leds.fadeRGB("FaceLeds", 0xFF8C00, 0.3)
                set_tablet_status("acting")

                pepper_speak(spoken, language)

                # Block mic until PC sends DONE (behavior finished)
                wait_for_done(behavior_sock)

                leds.fadeRGB("FaceLeds", 0x00FF00, 0.3)
                time.sleep(0.4)

            else:
                pepper_speak(response)
                time.sleep(0.4)

    except KeyboardInterrupt:
        pass
    finally:
        broker.shutdown()


if __name__ == "__main__":
    main()