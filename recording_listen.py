#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Sitong Chen, Dongyang Li

This file handles receiving triggers, collecting video/audio, and connecting to the EGI station.
"""
import zmq
import threading
import wave
import os
import cv2
import pyaudio
from egi_pynetstation.NetStation import NetStation
from datetime import datetime
import time

# Global variables
allowRecording = False
CHUNK_SIZE = 360  # 1040
CHANNELS = 2
FORMAT = pyaudio.paInt16
RATE = 12000  # 48000
video_count = 0
audio_count = 0
eci_client = None

def send_event_async(event_type):

    def target():
        try:
            eci_client.send_event(event_type=event_type)
        except Exception as e:
            print(f"Error sending event {event_type}: {e}")

    thread = threading.Thread(target=target)
    thread.start()




def zmq_listener():
    global allowRecording
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    
    while True:
        message = socket.recv_string()
        if message == "START_RECORDING":
            allowRecording = True
        elif message == "STOP_RECORDING":
            allowRecording = False
        else:
            send_event_async(message)




def main():
    global eci_client
    IP_ns = '10.10.10.42'  # IP Address of Net Station
    IP_amp = '10.10.10.51'  # IP Address of Amplifier
    port_ns = 55513  # Port configured for ECI in Net Station

    eci_client = NetStation(IP_ns, port_ns)
    eci_client.connect(ntp_ip=IP_amp)
    eci_client.begin_rec()  # begin to record
    

    listener_thread = threading.Thread(target=zmq_listener)
    listener_thread.start()
    listener_thread.join()

if __name__ == '__main__':
    main()
