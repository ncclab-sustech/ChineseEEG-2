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
import argparse

# Global variables
allowRecording = False
CHUNK_SIZE = 360  # 1040
CHANNELS = 2
FORMAT = pyaudio.paInt16
RATE = 12000  # 48000
video_count = 0
audio_count = 0
eci_client = None
current_time = datetime.now()


def send_event_async(event_type):
    def target():
        try:
            eci_client.send_event(event_type=event_type)
        except Exception as e:
            print(f"Error sending event {event_type}: {e}")

    thread = threading.Thread(target=target)
    thread.start()

def record_audio(filename):
    global args
    # args.time =datetime.now().strftime("Y%_m%_d%_H%_M%_S%")
    with open ('audio/audio.txt', 'a+') as f:
        p = pyaudio.PyAudio()
        print('start recording audio')
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK_SIZE
                        )
        send_event_async("BEGN")
        t = str(datetime.now())
        print("audio stream start",  t)
        f.write(f'{t}\n')
        folder_path = os.path.join('audio_',args.time)
        os.makedirs(folder_path, exist_ok=True)
        save_filename = os.path.join(folder_path, filename)
        wf = wave.open(save_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        try:
            while allowRecording:
                audio_data = stream.read(CHUNK_SIZE)
                wf.writeframes(audio_data)
        except Exception as e:
            print(f"Error recording audio: {e}")
        finally:
            wf.close()
            stream.stop_stream()
            stream.close()
            p.terminate()
        t = str(datetime.now())
        print("audio stream end", t)
        f.write(f'audio stream end {t}\n')    
        f.close()
    
def record_webcam(filename):
    global args
    # args.time = datetime.now().strftime("Y%_m%_d%_H%_M%_S%")
    with open ('video/video.txt', 'a+') as f:
        cap = cv2.VideoCapture(0, cv2.CAP_ANY)
        fourcc = cv2.VideoWriter.fourcc('X', 'V', 'I', 'D')
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        print('video stream start')
        fps = 30
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*'XVID'))
        folder_path = os.path.join('video_',args.time)
        os.makedirs(folder_path, exist_ok=True)
        save_filename = os.path.join(folder_path, filename)
        aviFile = cv2.VideoWriter(save_filename, fourcc, fps, (width, height))
        t = str(datetime.now())
        print("video stream start", t)
        f.write(f'{t}\n')
        while allowRecording == True:
            try:
                ret, frame = cap.read()
                if ret:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    date_t = str(datetime.now())[:19].replace(":", "-")
                    # 视频里面显示时间或者文字
                    frame = cv2.putText(frame, date_t, (10, 30), font, 0.5,
                                        (255, 255, 255), 1, cv2.LINE_AA)
                    aviFile.write(frame)
                else:
                    print("can not read data from camera")
                    break
            except Exception as e:
                print(f"fault while reading video{e}")
        t = str(datetime.now())
        print("end recording video", t)
        f.write(f'video stream end {t}\n')    
        f.close()
        aviFile.release()
        cap.release()

def start_recording():
    global video_count, audio_count
    args.time = (f"{(current_time).month}_{(current_time).day}_{(current_time).hour}_{(current_time).minute}{(current_time).second}")
    audio_filename = f"audio_{audio_count}.wav"
    video_filename = f"video_{video_count}.avi"
    threading.Thread(target=record_audio, args=(audio_filename,)).start()
    threading.Thread(target=record_webcam, args=(video_filename,)).start()
    print(f"Recording started: {audio_filename}, {video_filename}")
    video_count += 1
    audio_count += 1

def zmq_listener():
    global allowRecording
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5556")
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    
    while True:        
        
        message = socket.recv_string()
        print(f'Received {message}')
        
        # time.sleep(1)
        if message == "START_RECORDING":
            allowRecording = True
            start_recording()
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
    time.sleep(0.5)
    

    listener_thread = threading.Thread(target=zmq_listener)
    listener_thread.start()
    listener_thread.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parameters that can be changed in this experiment')
    parser.add_argument('--time', type=str, default='000', help='folder time')
    args = parser.parse_args()
    main()
