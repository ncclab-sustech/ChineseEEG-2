import time
import argparse
import tkinter as tk
from tkinter import Radiobutton, font
from datetime import datetime
from psychopy import locale_setup, prefs, sound, gui, visual, core, data, event, logging, clock, colors, iohub, hardware
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
from psychopy.hardware import keyboard
import asyncio
import json
import re
import numpy as np
import os
import zmq
import threading
import concurrent.futures
import scipy.io.wavfile as wav
import sounddevice as sd

# Network communication
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

current_time = datetime.now()
path = f"{current_time.month}_{current_time.day}_{current_time.hour}_{current_time.minute}{current_time.second}.json"


def attention_check(win, correct_answer, content):
    win.mouseVisible = True

    def submit_info():
        global user_info
        user_info = truth_var.get()
        focus_level = focus_var.get()
        user_data = {
            "user_choice": user_info,
            "focus_level": focus_level,
            "correct_answer": correct_answer
        }
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_data.append(user_data)
        else:
            existing_data = [user_data]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        root.destroy()
        win.mouseVisible = False

    root = tk.Tk()
    truth_var = tk.IntVar()
    focus_var = tk.IntVar()
    custom_font = font.Font(family="Helvetica", size=12)
    root.title("Attention Check")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 900
    window_height = 500
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{int(x)}+{int(y)}")
    participant_label = tk.Label(root, text="请判断下面的陈述是否正确：", font=custom_font)
    participant_label.pack(side='top')
    statement = tk.Label(root, text=content, font=custom_font)
    statement.pack(side='top')
    true_button = Radiobutton(root, text="对", variable=truth_var, value=1, font=custom_font)
    true_button.place(x=window_width // 2 - 85, y=window_height - 400)
    false_button = Radiobutton(root, text="错", variable=truth_var, value=0, font=custom_font)
    false_button.place(x=window_width // 2 + 55, y=window_height - 400)

    participant_focus = tk.Label(root, text="请对您刚才的专注程度进行自评：", font=custom_font)
    participant_focus.place(x=window_width // 2 - 130, y=window_height - 300)
    low_button = Radiobutton(root, text="完全不专注", variable=focus_var, value=-2, font=custom_font)
    low_button.place(x=window_width // 2 - 395, y=window_height - 230)
    middle_low_button = Radiobutton(root, text="有些不专注", variable=focus_var, value=-1, font=custom_font)
    middle_low_button.place(x=window_width // 2 - 190, y=window_height - 230)
    middle_button = Radiobutton(root, text="一般", variable=focus_var, value=0, font=custom_font)
    middle_button.place(x=window_width // 2 - 30, y=window_height - 230)
    middle_high_button = Radiobutton(root, text="比较专注", variable=focus_var, value=1, font=custom_font)
    middle_high_button.place(x=window_width // 2 + 100, y=window_height - 230)
    high_button = Radiobutton(root, text="完全专注", variable=focus_var, value=2, font=custom_font)
    high_button.place(x=window_width // 2 + 280, y=window_height - 230)

    submit_button = tk.Button(root, text="提交", command=submit_info, font=custom_font)
    submit_button.place(x=window_width // 2 - 50, y=window_height - 80, width=100, height=50)
    root.attributes("-topmost", True)
    root.mainloop()


def create_input_window(chapter, now, win):
    with open("statements.json", 'r', encoding='utf-8') as json_file:
        questions = json.load(json_file)
    if now != 0:
        if chapter == 28:
            answer = questions['statements1']
            correct = questions['truth1']
            attention_check(win, correct[now-1], answer[now-1])
        elif chapter == 10:
            answer = questions['statements2']
            correct = questions['truth2']
            attention_check(win, correct[now-1], answer[now-1])


def send_event(event_type):
    # print(event_type)
    socket.send_string(event_type)


def load_audio(file_path):
    rate, data = wav.read(file_path)
    return rate, data


def play_audio(rate, data):
    sd.play(data, rate)
    sd.wait()


def trigger_events(event_type, global_start_time, event_times, rate):
    for event_time in event_times:
        audio_time = event_time / rate
        # print("audio_time", audio_time)
        while 1:
            if time.time() - global_start_time >= audio_time:
                send_event(event_type)
                print(f"Trigger {event_type} at {audio_time:.2f} seconds")
                break


def play_audio_with_triggers(audio_files, audio_path, eeg_sampling_rate, ROWS_times, ROWE_times, start_indices, win):
    global global_start_time, image
    image = visual.ImageStim(win=win, name='image', image='图片1.png', pos=(0, -0.05), size=(1.7, 1.2))
    # Calculate global start time
    end_index = [0 for i in range(len(audio_files))]
    rows_array = np.array(ROWS_times)
    rowe_array = np.array(ROWE_times)
    send_event("START_RECORDING")
    for i, audio_file in enumerate(audio_files):
        if i < 10:
            send_event(f"CH0{i}")
        else:
            send_event(f"CH{i}")
        rate, data = load_audio(os.path.join(audio_path, audio_file))
        total_samples = len(data)
        start_index = start_indices[i]
        print("st")
        print(start_index)
        indices = np.where(rows_array < start_indices[i + 1])
        print(indices)
        # if len(indices[0]) > 0:
        #     end_index[i] = indices[0][-1] + 1
        if i == len(audio_files) - 1:
            end_index[i] = len(ROWS_times)
            print(0)
        else:
            indices = np.where(rows_array < start_indices[i + 1])
            print(indices)
            if len(indices[0]) > 0:
                end_index[i] = indices[0][-1] + 1
            # else:
            #     end_index[i] = len(rows_array)
            print(end_index)

        ROWS_audio_times = []
        ROWE_audio_times = []
        if i == 0:
            for j in range(0, end_index[i]):

                ROWS_audio_times.append((rows_array[j] - start_index) / eeg_sampling_rate * rate)
                ROWE_audio_times.append((rowe_array[j] - start_index) / eeg_sampling_rate * rate)
            print(len(ROWS_audio_times))
            print(ROWS_audio_times)
            print(len(ROWE_audio_times))
            print(ROWE_audio_times)
        # Calculate audio times based on EEG start index
        else:
            for j in range(end_index[i - 1], end_index[i]):
                ROWS_audio_times.append((rows_array[j] - start_index) / eeg_sampling_rate * rate)
                ROWE_audio_times.append((rowe_array[j] - start_index) / eeg_sampling_rate * rate)
            # print(len(ROWS_audio_times))
            # print(ROWS_audio_times)
            # print(len(ROWE_audio_times))
            # print(ROWS_audio_times)
        # ROWS_audio_times = [(event_time - start_index) / eeg_sampling_rate * rate for event_time in ROWS_times]
        # ROWE_audio_times = [(event_time - start_index) / eeg_sampling_rate * rate for event_time in ROWE_times]
        # print("ROWS", ROWS_audio_times)

        image.setAutoDraw(True)
        win.flip()
        # Create separate tasks for ROWS and ROWE
        # ROWS_task = asyncio.create_task(trigger_events("ROWS", global_start_time, ROWS_audio_times, rate))
        p = threading.Thread(target=play_audio, args=(rate, data))

        p.start()
        print("start")
        global_start_time = time.time()
        t1 = threading.Thread(target=trigger_events, args=("ROWS", global_start_time, ROWS_audio_times, rate))
        # print("ROWE", ROWE_audio_times)
        # ROWE_task = asyncio.create_task(trigger_events("ROWE", global_start_time, ROWE_audio_times, rate))
        t2 = threading.Thread(target=trigger_events, args=("ROWE", global_start_time, ROWE_audio_times, rate))
        # Start audio playback
        # play_audio(rate, data)
        # threading.Thread(target=play_audio, args=(rate,data)).start()

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        p.join()
        print("end")
        rest_text = visual.TextStim(win, text='休息时间', pos=(0, 0), height=0.1, color='white')
        image.setAutoDraw(False)
        rest_text.setAutoDraw(True)  # Start displaying the rest text
        win.flip()
        core.wait(10)  # Wait for 10 seconds
        rest_text.setAutoDraw(False)  # Stop displaying the rest text
        create_input_window(len(audio_files), i, win)
    send_event("STOP_RECORDING")


def main_experiment():
    global args

    # Prepare for the psychopy experiment
    _thisDir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_thisDir)
    psychopyVersion = '2022.2.4'
    expName = 'PlayAudio'
    expInfo = {'participant': f"{np.random.randint(0, 999999):06.0f}", 'session': '001'}
    dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
    if dlg.OK == False:
        core.quit()
    expInfo['date'] = data.getDateStr()
    expInfo['expName'] = expName
    expInfo['psychopyVersion'] = psychopyVersion

    filename = _thisDir + os.sep + u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])

    thisExp = data.ExperimentHandler(name=expName, version='', extraInfo=expInfo, runtimeInfo=None, savePickle=True,
                                     saveWideText=True, dataFileName=filename)
    logFile = logging.LogFile(filename + '.log', level=logging.EXP)
    logging.console.setLevel(logging.WARNING)

    endExpNow = False
    frameTolerance = 0.001

    win = visual.Window(size=[800, 600], fullscr=args.fullscreen, screen=0, winType='pyglet', allowStencil=False,
                        monitor='testMonitor', color=[0, 0, 0], colorSpace='rgb', blendMode='avg', useFBO=True,
                        units='height')
    image = visual.ImageStim(win=win, name='image', image='图片1.png', pos=(0, 0), size=(1.5, 1.5))

    win.mouseVisible = False
    expInfo['frameRate'] = win.getActualFrameRate()
    frameDur = 1.0 / round(expInfo['frameRate']) if expInfo['frameRate'] != None else 1.0 / 60.0

    ioConfig = {}
    ioConfig['Keyboard'] = dict(use_keymap='psychopy')

    defaultKeyboard = keyboard.Keyboard(backend='iohub')

    textWelcome = visual.TextStim(win=win, name='textWelcome', text='您好！音频实验即将开始\n请按空格键开始',
                                  font='Open Sans',
                                  pos=(0, 0), height=0.05, wrapWidth=None, ori=0.0, color='white', colorSpace='rgb',
                                  opacity=None, languageStyle='LTR', depth=0.0)
    key_Welcome = keyboard.Keyboard()

    textGoodbye = visual.TextStim(win=win, name='textGoodbye', text='实验结束，感谢您的参与！\n  请按空格键退出实验',
                                  font='Open Sans',
                                  pos=(0, 0), height=0.05, wrapWidth=None, ori=0.0, color='white', colorSpace='rgb',
                                  opacity=None, languageStyle='LTR', depth=0.0)
    key_Goodbye = keyboard.Keyboard()

    routineTimer = core.Clock()

    # send_event("START_RECORDING")

    audio_path = args.audio_folder
    audio_files = [f for f in os.listdir(audio_path) if f.endswith('.wav')]

    # Regular expression to find the number in the filename
    match_pattern = re.compile(r"audio_(\d+).wav")

    # Sort the list of audio files using the extracted numbers
    # The lambda function extracts the number and converts it to an integer
    audio_files.sort(key=lambda x: int(match_pattern.match(x).group(1)))

    # Define the file path for loading the JSON data
    json_file_path = os.path.join(args.audio_folder, 'events_data.json')

    # Load the events data from the JSON file
    with open(json_file_path, 'r') as json_file:
        events_data = json.load(json_file)

    begn_nonzero_indices = events_data['begn_nonzero_indices']
    ROWS_times = events_data['ROWS_times']
    ROWE_times = events_data['ROWE_times']
    print(ROWS_times)
    print(ROWE_times)

    continueRoutine = True
    routineForceEnded = False
    key_Welcome.keys = []
    key_Welcome.rt = []
    _key_Welcome_allKeys = []
    WelcomePageComponents = [textWelcome, key_Welcome]
    for thisComponent in WelcomePageComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    while continueRoutine:
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1

        if textWelcome.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            textWelcome.frameNStart = frameN
            textWelcome.tStart = t
            textWelcome.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(textWelcome, 'tStartRefresh')
            thisExp.timestampOnFlip(win, 'textWelcome.started')
            textWelcome.setAutoDraw(True)

        waitOnFlip = False
        if key_Welcome.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            key_Welcome.frameNStart = frameN
            key_Welcome.tStart = t
            key_Welcome.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(key_Welcome, 'tStartRefresh')
            thisExp.timestampOnFlip(win, 'key_Welcome.started')
            key_Welcome.status = STARTED
            waitOnFlip = True
            win.callOnFlip(key_Welcome.clock.reset)
            win.callOnFlip(key_Welcome.clearEvents, eventType='keyboard')
        if key_Welcome.status == STARTED and not waitOnFlip:
            theseKeys = key_Welcome.getKeys(keyList=['space'], waitRelease=False)
            _key_Welcome_allKeys.extend(theseKeys)
            if len(_key_Welcome_allKeys):
                key_Welcome.keys = _key_Welcome_allKeys[-1].name
                key_Welcome.rt = _key_Welcome_allKeys[-1].rt
                continueRoutine = False

                win.flip()

        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()

        if not continueRoutine:
            routineForceEnded = True
            break
        continueRoutine = False
        for thisComponent in WelcomePageComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break

        if continueRoutine:
            win.flip()

    for thisComponent in WelcomePageComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    if key_Welcome.keys in ['', [], None]:
        key_Welcome.keys = None
    thisExp.addData('key_Welcome.keys', key_Welcome.keys)
    if key_Welcome.keys != None:
        thisExp.addData('key_Welcome.rt', key_Welcome.rt)
    thisExp.nextEntry()
    routineTimer.reset()

    play_audio_with_triggers(audio_files, audio_path, 250, ROWS_times, ROWE_times, begn_nonzero_indices, win)
    continueRoutine = True
    routineForceEnded = False
    key_Goodbye.keys = []
    key_Goodbye.rt = []
    _key_Goodbye_allKeys = []
    GoodbyePageComponents = [textGoodbye, key_Goodbye]
    for thisComponent in GoodbyePageComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # send_event("STOP_RECORDING")

    while continueRoutine:
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1

        if textGoodbye.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            textGoodbye.frameNStart = frameN
            textGoodbye.tStart = t
            textGoodbye.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(textGoodbye, 'tStartRefresh')
            thisExp.timestampOnFlip(win, 'textGoodbye.started')
            textGoodbye.setAutoDraw(True)

        waitOnFlip = False
        if key_Goodbye.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            key_Goodbye.frameNStart = frameN
            key_Goodbye.tStart = t
            key_Goodbye.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(key_Goodbye, 'tStartRefresh')
            thisExp.timestampOnFlip(win, 'key_Goodbye.started')
            key_Goodbye.status = STARTED
            waitOnFlip = True
            win.callOnFlip(key_Goodbye.clock.reset)
            win.callOnFlip(key_Goodbye.clearEvents, eventType='keyboard')
        if key_Goodbye.status == STARTED and not waitOnFlip:
            theseKeys = key_Goodbye.getKeys(keyList=['space'], waitRelease=False)
            _key_Goodbye_allKeys.extend(theseKeys)
            if len(_key_Goodbye_allKeys):
                key_Goodbye.keys = _key_Goodbye_allKeys[-1].name
                key_Goodbye.rt = _key_Goodbye_allKeys[-1].rt
                continueRoutine = False

        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()

        if not continueRoutine:
            routineForceEnded = True
            break
        continueRoutine = False
        for thisComponent in GoodbyePageComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break

        if continueRoutine:
            win.flip()

    for thisComponent in GoodbyePageComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    if key_Goodbye.keys in ['', [], None]:
        key_Goodbye.keys = None
    thisExp.addData('key_Goodbye.keys', key_Goodbye.keys)
    if key_Goodbye.keys != None:
        thisExp.addData('key_Goodbye.rt', key_Goodbye.rt)
    thisExp.nextEntry()
    routineTimer.reset()

    win.flip()

    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)
    logging.flush()

    thisExp.abort()
    # win.close()
    core.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parameters that can be changed in this experiment')
    parser.add_argument('--fullscreen', type=bool, default=False, help='Whether to set a full screen')
    parser.add_argument('--audio_folder', type=str, default="example/path",
                        help='path to your folder')
    args = parser.parse_args()
    main_experiment()
