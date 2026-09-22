# Pepper AI Integration

## Introduction

This program is used to integrate Pepper's conversational function to a text-based LLM using groq API. It consists of the two codes `pc_server2.py` and `pepper_listener7.py`. The code `pc_server2.py` is to be run on a computer using Python 3.10 to act as a host that connects Pepper to groq. The code `pepper_listener7.py` is to be run on Pepper and will control the speaking and listening mechanism. Both pepper and the hosting computer needs to be connected on the same network. Make sure the CONFIG on `pc_server2.py` and `pepper_listener7.py` which includes the IP and and API key is configured properly.

Future Development will work on excluding the need for a separate hosting machine.
