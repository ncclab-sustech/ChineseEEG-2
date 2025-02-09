#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Sitong Chen, Dongyang Li

This is the UI part for displaying the pre-processed novel on the screen and sending triggers.
"""
import math
import time
import argparse
from psychopy import locale_setup, prefs, sound, gui, visual, core, data, event, logging, clock, colors, iohub, hardware
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
from psychopy.hardware import keyboard
from multiprocessing import Queue
import asyncio
import json
import numpy as np
import os

# Network communication
import zmq

# Global variables
prefs.hardware['audioLib'] = 'ptb'
prefs.hardware['audioLatencyMode'] = '3'

queue = Queue()
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

# def send_event(event_type):
#     context = zmq.Context()
#     socket = context.socket(zmq.PUB)
#     socket.bind("tcp://*:5556")
#     socket.send_string(event_type)

def send_event(event_type):
    socket.send_string(event_type)


def calculate_length_without_punctuation_and_indexes(sentence):
    """Calculate the length of a sentence excluding punctuation and the coordinates of all non-punctuation positions"""
    punctuations = ['\n', '。', '，', '！', '？', '：', '；', '“', '”', '、', '《', '》', '.', '（', '）', '…', '·']
    sentence_list = list(sentence)
    length_without_punctuation = 0
    indexes = []
    for index, char in enumerate(sentence_list):
        if char not in punctuations:
            length_without_punctuation += 1
            indexes.append(index)

    return length_without_punctuation, indexes

def play_preface(thisExp, expInfo, win, routineTimer, eci_client=None):
    """
    This method is used for simulating the experiment and will take place after the calibration
    process. It will serve as a preliminary step before the actual novel reading begins.

    Typically, the trial reading material consists of the preface or introductory part of the novel.

    Before invoking this method, you should check if the experimental program requires the use of
    the EGI device. By default, the `eci_client` parameter is set to None. If an EGI device is
    connected, you need to pass the EGI object to the `egi_client` parameter.

    You can use this method as follows:

    if args.add_mark == True:
        play_preface(thisExp, expInfo, win, routineTimer, eci_client=eci_client)
    else:
        play_preface(thisExp, expInfo, win, routineTimer, eci_client=None)
    """
    global args
    # set up handler to look after randomisation of conditions etc
    keyPreface = keyboard.Keyboard()
    trialsPlay_preface = data.TrialHandler(nReps=1.0, method='sequential',
                                           extraInfo=expInfo, originPath=-1,
                                           trialList=data.importConditions(args.preface_path),
                                           seed=None, name='trialsPlayPreface')
    thisExp.addLoop(trialsPlay_preface)  # add the loop to the experiment
    thisTrialsPlay = trialsPlay_preface.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisTrialsPlay.rgb)
    if thisTrialsPlay != None:
        for paramName in thisTrialsPlay:
            exec('{} = thisTrialsPlay[paramName]'.format(paramName))

    text_preface_start = visual.TextStim(win=win, name='textPrefaceStart',
                                         text='您好！请按空格键进入模拟试读环节',
                                         font='Open Sans',
                                         pos=(0, 0), height=0.05, wrapWidth=None, ori=0.0,
                                         color='white', colorSpace='rgb', opacity=None,
                                         languageStyle='LTR',
                                         depth=0.0);
    continuePrefaceStart = True
    while continuePrefaceStart:
        theseKeys = keyPreface.getKeys(keyList=['space'], waitRelease=False)
        if len(theseKeys):
            continuePrefaceStart = False
        text_preface_start.draw()
        win.flip()

    # if args.add_mark == True:
        # eci_client.send_event(event_type='PRES')
    send_event("PRES")
    count = 1

    for thisTrialsPlay in trialsPlay_preface:
        currentLoop = trialsPlay_preface
        # abbreviate parameter names if possible (e.g. rgb = thisTrialsPlay.rgb)
        if thisTrialsPlay != None:
            for paramName in thisTrialsPlay:
                exec('{} = thisTrialsPlay[paramName]'.format(paramName))

        # --- Prepare to start Routine "trial" ---

        # update component parameters for each repeat
        # Prepare the texts to be shown in this trial and assign the highlighted character
        texts = []

        if thisTrialsPlay.row_num == 2 and thisTrialsPlay.main_row == 0:
            rows = thisTrialsPlay.Chinese_text.split('\n')
            rows = list(filter(lambda x: x != '\n' and x != '', rows))
            main_row = rows[0]
            other_row = rows[1]
            main_row_words = list(main_row)
            other_row_words = list(other_row)
            pos_x_main_row = -len(main_row_words)*0.06/2
            pos_y_main_row = 0
            pos_x_other_row = -len(other_row_words)*0.06/2
            pos_y_other_row = -0.1

            for i in range(len(main_row_words)):
                wordPlay = visual.TextStim(win, text=main_row_words[i], color=args.highlight_color,
                                           pos=(pos_x_main_row, pos_y_main_row), font='Times New Roman',
                                           opacity=1,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_main_row += 0.06
            for i in range(len(other_row_words)):
                wordPlay = visual.TextStim(win, text=other_row_words[i], color='white',
                                           pos=(pos_x_other_row, pos_y_other_row), font='Times New Roman',
                                           opacity=0.5,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_other_row += 0.06

        elif thisTrialsPlay.row_num == 2 and thisTrialsPlay.main_row == 1:
            rows = thisTrialsPlay.Chinese_text.split('\n')
            rows = list(filter(lambda x: x != '\n' and x != '', rows))
            main_row = rows[1]
            other_row = rows[0]
            main_row_words = list(main_row)
            other_row_words = list(other_row)
            pos_x_main_row = -len(main_row_words)*0.06/2
            pos_y_main_row = 0
            pos_x_other_row = -len(other_row_words)*0.06/2
            pos_y_other_row = 0.1

            for i in range(len(main_row_words)):
                wordPlay = visual.TextStim(win, text=main_row_words[i], color=args.highlight_color,
                                           pos=(pos_x_main_row, pos_y_main_row), font='Times New Roman',
                                           opacity=1,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_main_row += 0.06
            for i in range(len(other_row_words)):
                wordPlay = visual.TextStim(win, text=other_row_words[i], color='white',
                                           pos=(pos_x_other_row, pos_y_other_row), font='Times New Roman',
                                           opacity=0.5,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_other_row += 0.06

        elif thisTrialsPlay.row_num == 3:
            rows = thisTrialsPlay.Chinese_text.split('\n')
            rows = list(filter(lambda x: x != '\n' and x != '', rows))
            main_row = rows[1]
            top_row = rows[0]
            bottom_row = rows[2]
            main_row_words = list(main_row)
            top_row_words = list(top_row)
            bottom_row_words = list(bottom_row)
            pos_x_main_row = -len(main_row_words)*0.06/2
            pos_y_main_row = 0
            pos_x_top_row = -len(top_row_words)*0.06/2
            pos_y_top_row = 0.1
            pos_x_bottom_row = -len(bottom_row_words)*0.06/2
            pos_y_bottom_row = -0.1

            for i in range(len(main_row_words)):
                wordPlay = visual.TextStim(win, text=main_row_words[i], color=args.highlight_color,
                                           pos=(pos_x_main_row, pos_y_main_row), font='Times New Roman',
                                           opacity=1,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_main_row += 0.06
            for i in range(len(top_row_words)):
                wordPlay = visual.TextStim(win, text=top_row_words[i], color='white',
                                           pos=(pos_x_top_row, pos_y_top_row),
                                           font='Times New Roman', opacity=0.5, height=0.05)
                texts.append(wordPlay)
                pos_x_top_row += 0.06
            for i in range(len(bottom_row_words)):
                wordPlay = visual.TextStim(win, text=bottom_row_words[i], color='white',
                                           pos=(pos_x_bottom_row, pos_y_bottom_row), font='Times New Roman',
                                           opacity=0.5,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_bottom_row += 0.06

        for i in range(len(texts)):
            texts[i].setAutoDraw(True)
        
        # mark the eeg with 'ROWS' when a row begins to be highlighted
        # if args.add_mark == True:
        if count == 1:
            # eci_client.send_event(event_type='STRT')
            send_event("STRT")
            
        # --- Run Routine "trial" ---
        routineTimer.reset()
        while routineTimer.getTime() < args.shift_time:

            # check for quit (typically the Esc key)
            if keyPreface.getKeys(keyList=["escape"]):
                win.close()
                core.quit()

            win.flip()

        # mark the eeg with 'ROWE' when a row finishes all the highlights
        # if args.add_mark == True:
        main_row_words_len_without_punc, _ = calculate_length_without_punctuation_and_indexes(
            main_row_words)
        if count == main_row_words_len_without_punc:
            # eci_client.send_event(event_type='ROWE')
            send_event("ROWE")
            count = 1
        else:
            count += 1

        # for i in range(len(texts)):
        #     texts[i].setAutoDraw(False)
        for text in texts:
            text.setAutoDraw(False)
        texts.clear()            
        # texts.clear()
    # completed 1.0 repeats of 'trialsPlay'
    # if args.add_mark == True:
    # eci_client.send_event(event_type='PREE')
    send_event("PREE")
    routineTimer.reset()


def main_experiment():
    
    """
    Main program of the experiment.
    """
    global args
    global queue


    count =1 
    # --- Prepare for the psychopy experiment ---
    # Ensure that relative paths start from the same directory as this script
    _thisDir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(_thisDir)
    # Store info about the experiment session
    psychopyVersion = '2022.2.4'
    expName = 'PlayNovel'  # from the Builder filename that created this script
    expInfo = {
        'participant': f"{np.random.randint(0, 999999):06.0f}",
        'session': '001',
    }
    # --- Show participant info dialog --
    dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
    if dlg.OK == False:
        core.quit()  # user pressed cancel
    expInfo['date'] = data.getDateStr()  # add a simple timestamp
    expInfo['expName'] = expName
    expInfo['psychopyVersion'] = psychopyVersion

    # Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    filename = _thisDir + os.sep + u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])

    # An ExperimentHandler isn't essential but helps with data saving
    thisExp = data.ExperimentHandler(name=expName, version='',
                                     extraInfo=expInfo, runtimeInfo=None,
                                     savePickle=True, saveWideText=True,
                                     dataFileName=filename)

    # save a log file for detail verbose info
    logFile = logging.LogFile(filename + '.log', level=logging.EXP)
    logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    frameTolerance = 0.001  # how close to onset before 'same' frame

    # --- Setup the Window ---
    win = visual.Window(
        size=[800, 600], fullscr=args.fullscreen, screen=0,
        winType='pyglet', allowStencil=False,
        monitor='testMonitor', color=[0, 0, 0], colorSpace='rgb',
        blendMode='avg', useFBO=True,
        units='height')
    win.mouseVisible = False
    # store frame rate of monitor if we can measure it
    expInfo['frameRate'] = win.getActualFrameRate()
    if expInfo['frameRate'] != None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0  # could not measure, so guess

    # --- Setup input devices ---
    ioConfig = {}
    ioConfig['Keyboard'] = dict(use_keymap='psychopy')


    # create a default keyboard (e.g. to check for escape)
    defaultKeyboard = keyboard.Keyboard(backend='iohub')

    # --- Initialize components for Routine "WelcomePage" ---
    textWelcome = visual.TextStim(win=win, name='textWelcome',
                                  text='您好！小说《小王子》即将开始\n请按空格键开始观看',
                                  font='Open Sans',
                                  pos=(0, 0), height=0.05, wrapWidth=None, ori=0.0,
                                  color='white', colorSpace='rgb', opacity=None,
                                  languageStyle='LTR',
                                  depth=0.0);
    key_Welcome = keyboard.Keyboard()

    # --- Initialize components for Routine "trial" ---
    # textDot is used to control the duration of every highlighted
    textDot = visual.TextStim(win=win, name='textDot',
                              text='.',
                              font='Open Sans',
                              pos=(1, 0), height=0.05, wrapWidth=None, ori=0.0,
                              color='white', colorSpace='rgb', opacity=None,
                              languageStyle='LTR',
                              depth=-1.0);

    # --- Initialize components for Routine "GoodbyePage" ---
    textGoodbye = visual.TextStim(win=win, name='textGoodbye',
                                  text='实验结束，感谢您的参与！\n  请按空格键退出实验',
                                  font='Open Sans',
                                  pos=(0, 0), height=0.05, wrapWidth=None, ori=0.0,
                                  color='white', colorSpace='rgb', opacity=None,
                                  languageStyle='LTR',
                                  depth=0.0);
    key_Goodbye = keyboard.Keyboard()

    # Create some handy timers
    globalClock = core.Clock()  # to track the time since experiment started
    routineTimer = core.Clock()  # to track time remaining of each (possibly non-slip) routine
    # play_preface(thisExp, expInfo, win, routineTimer, eci_client=None)
    # if args.isFirstSession:
    send_event("START_RECORDING")
    print("OK")
    
    play_preface(thisExp, expInfo, win, routineTimer)
    send_event("STOP_RECORDING")
    # --- Prepare to start Routine "WelcomePage" ---
    continueRoutine = True
    routineForceEnded = False
    # update component parameters for each repeat
    key_Welcome.keys = []
    key_Welcome.rt = []
    _key_Welcome_allKeys = []
    # keep track of which components have finished
    WelcomePageComponents = [textWelcome, key_Welcome]
    for thisComponent in WelcomePageComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "WelcomePage" ---
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *textWelcome* updates
        if textWelcome.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            # keep track of start time/frame for later
            textWelcome.frameNStart = frameN  # exact frame index
            textWelcome.tStart = t  # local t and not account for scr refresh
            textWelcome.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(textWelcome, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'textWelcome.started')
            textWelcome.setAutoDraw(True)

        # *key_Welcome* updates
        waitOnFlip = False
        if key_Welcome.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            # keep track of start time/frame for later
            key_Welcome.frameNStart = frameN  # exact frame index
            key_Welcome.tStart = t  # local t and not account for scr refresh
            key_Welcome.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(key_Welcome, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'key_Welcome.started')
            key_Welcome.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(key_Welcome.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(key_Welcome.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if key_Welcome.status == STARTED and not waitOnFlip:
            theseKeys = key_Welcome.getKeys(keyList=['space'], waitRelease=False)
            _key_Welcome_allKeys.extend(theseKeys)
            if len(_key_Welcome_allKeys):
                key_Welcome.keys = _key_Welcome_allKeys[-1].name  # just the last key pressed
                key_Welcome.rt = _key_Welcome_allKeys[-1].rt
                # a response ends the routine
                continueRoutine = False

        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()

        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in WelcomePageComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "WelcomePage" ---
    for thisComponent in WelcomePageComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # check responses
    if key_Welcome.keys in ['', [], None]:  # No response was made
        key_Welcome.keys = None
    thisExp.addData('key_Welcome.keys', key_Welcome.keys)
    if key_Welcome.keys != None:  # we had a response
        thisExp.addData('key_Welcome.rt', key_Welcome.rt)
    thisExp.nextEntry()
    # the Routine "WelcomePage" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    # set up trial list
    base_path = "data/segmented_novel/segmented_Chinense_novel_"
    file_list = [f"{base_path}run_{i}_display.xlsx" for i in range(1, 8)]
    trials_list = [data.importConditions(file) for file in file_list]
    combined_trials = []
    for trials in trials_list:
        combined_trials.extend(trials)
    # set up handler to look after randomisation of conditions etc
    trialsPlay = data.TrialHandler(nReps=1.0, method='sequential',
                                   extraInfo=expInfo, originPath=-1,
                                   trialList=combined_trials,
                                   seed=None, name='trialsPlay')
    thisExp.addLoop(trialsPlay)  # add the loop to the experiment
    thisTrialsPlay = trialsPlay.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisTrialsPlay.rgb)
    if thisTrialsPlay != None:
        for paramName in thisTrialsPlay:
            exec('{} = thisTrialsPlay[paramName]'.format(paramName))

    count_chapter = 0
    count_chapter0 = 0

    send_event("START_RECORDING")
    for thisTrialsPlay in trialsPlay:
        currentLoop = trialsPlay
        # abbreviate parameter names if possible (e.g. rgb = thisTrialsPlay.rgb)
        if thisTrialsPlay != None:
            for paramName in thisTrialsPlay:
                exec('{} = thisTrialsPlay[paramName]'.format(paramName))

        # --- Prepare to start Routine "trial" ---
        continueRoutine = True
        routineForceEnded = False
        restRoutine = False
        isChapterStart = False
        # update component parameters for each repeat
        # Prepare the texts to be shown in this trial and assign the highlighted character
        texts = []
        if thisTrialsPlay.Chinese_text in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
                                           22, 23, 24, 25,
                                           26,
                                           27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]:
            # print(str(round(thisTrialsPlay.Chinese_text)))
            # judge whether to rest before display another chapter
            thisTrialsPlay.Chinese_text = round(thisTrialsPlay.Chinese_text)
            isChapterStart = True
            count_chapter += 1
            count_chapter0 += 1

            if count_chapter == args.rest_period + 1:
                restRoutine = True
                count_chapter = 1

            wordPlay = visual.TextStim(win, text=str(round(thisTrialsPlay.Chinese_text)),
                                       color=args.highlight_color, pos=(0, 0),
                                       font='Times New Roman',
                                       opacity=1, height=0.05)
            texts.append(wordPlay)
            main_row_words = texts

        elif thisTrialsPlay.row_num == 2 and thisTrialsPlay.main_row == 0:
            rows = thisTrialsPlay.Chinese_text.split('\n')
            rows = list(filter(lambda x: x != '\n' and x != '', rows))
            main_row = rows[0]
            other_row = rows[1]
            main_row_words = list(main_row)
            other_row_words = list(other_row)
            pos_x_main_row = -len(main_row_words) * 0.06 / 2
            pos_y_main_row = 0
            pos_x_other_row = -len(other_row_words) * 0.06 / 2
            pos_y_other_row = -0.1

            for i in range(len(main_row_words)):
                wordPlay = visual.TextStim(win, text=main_row_words[i], color=args.highlight_color,
                                           pos=(pos_x_main_row, pos_y_main_row), font='Times New Roman',
                                           opacity=1,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_main_row += 0.06
            for i in range(len(other_row_words)):
                wordPlay = visual.TextStim(win, text=other_row_words[i], color='white',
                                           pos=(pos_x_other_row, pos_y_other_row), font='Times New Roman',
                                           opacity=0.5,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_other_row += 0.06

        elif thisTrialsPlay.row_num == 2 and thisTrialsPlay.main_row == 1:
            rows = thisTrialsPlay.Chinese_text.split('\n')
            rows = list(filter(lambda x: x != '\n' and x != '', rows))
            main_row = rows[1]
            other_row = rows[0]
            main_row_words = list(main_row)
            other_row_words = list(other_row)
            pos_x_main_row = -len(main_row_words) * 0.06 / 2
            pos_y_main_row = 0
            pos_x_other_row = -len(other_row_words) * 0.06 / 2
            pos_y_other_row = 0.1

            for i in range(len(main_row_words)):
                wordPlay = visual.TextStim(win, text=main_row_words[i], color=args.highlight_color,
                                           pos=(pos_x_main_row, pos_y_main_row), font='Times New Roman',
                                           opacity=1,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_main_row += 0.06
            for i in range(len(other_row_words)):
                wordPlay = visual.TextStim(win, text=other_row_words[i], color='white',
                                           pos=(pos_x_other_row, pos_y_other_row), font='Times New Roman',
                                           opacity=0.5,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_other_row += 0.06

        elif thisTrialsPlay.row_num == 3:
            rows = thisTrialsPlay.Chinese_text.split('\n')
            rows = list(filter(lambda x: x != '\n' and x != '', rows))
            main_row = rows[1]
            top_row = rows[0]
            bottom_row = rows[2]
            main_row_words = list(main_row)
            top_row_words = list(top_row)
            bottom_row_words = list(bottom_row)
            pos_x_main_row = -len(main_row_words) * 0.06 / 2
            pos_y_main_row = 0
            pos_x_top_row = -len(top_row_words) * 0.06 / 2
            pos_y_top_row = 0.1
            pos_x_bottom_row = -len(bottom_row_words) * 0.06 / 2
            pos_y_bottom_row = -0.1

            for i in range(len(main_row_words)):
                wordPlay = visual.TextStim(win, text=main_row_words[i], color=args.highlight_color,
                                           pos=(pos_x_main_row, pos_y_main_row), font='Times New Roman',
                                           opacity=1,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_main_row += 0.06
            for i in range(len(top_row_words)):
                wordPlay = visual.TextStim(win, text=top_row_words[i], color='white',
                                           pos=(pos_x_top_row, pos_y_top_row),
                                           font='Times New Roman', opacity=0.5, height=0.05)
                texts.append(wordPlay)
                pos_x_top_row += 0.06
            for i in range(len(bottom_row_words)):
                wordPlay = visual.TextStim(win, text=bottom_row_words[i], color='white',
                                           pos=(pos_x_bottom_row, pos_y_bottom_row), font='Times New Roman',
                                           opacity=0.5,
                                           height=0.05)
                texts.append(wordPlay)
                pos_x_bottom_row += 0.06

        # rest if restRoutine is True
        if restRoutine == True:
            send_event("STOP_RECORDING")

            textRest = visual.TextStim(win=win, name='textRest',
                                       text='您好！现在进入强制休息时间\n倒计时结束前不可以进入后续章节',
                                       font='Open Sans',
                                       pos=(0, 0), height=0.05, wrapWidth=None, ori=0.0,
                                       color='white', colorSpace='rgb', opacity=None,
                                       languageStyle='LTR',
                                       depth=0.0);
            textCount = visual.TextStim(win=win, name='textCount',
                                        text='20',
                                        font='Open Sans',
                                        pos=(0, -0.2), height=0.05, wrapWidth=None, ori=0.0,
                                        color='white', colorSpace='rgb', opacity=None,
                                        languageStyle='LTR',
                                        depth=0.0);

            routineTimer.reset()
            for i in range(args.force_rest_time):
                textCount.text = str(args.force_rest_time - i)
                while routineTimer.getTime() <= 1:
                    textRest.draw()
                    textCount.draw()
                    win.flip()
                routineTimer.reset()

            textRest.text = '您好！强制休息时间已结束\n请按空格键开始观看后续章节'
            continueRest = True
            restKeyboard = keyboard.Keyboard()
            while continueRest:
                keys = restKeyboard.getKeys(keyList=['space'], waitRelease=False)
                if len(keys):
                    continueRest = False
                    send_event("START_RECORDING")
                textRest.draw()
                win.flip()

            # reset the time to the beginning of the rest
            routineTimer.reset()

        if isChapterStart == True:
            send_event(f"CH{str(thisTrialsPlay.Chinese_text).zfill(2)}")
            for i in range(len(texts)):
                texts[i].setAutoDraw(True)
            routineTimer.reset()
            while routineTimer.getTime() < 5:
                win.flip()
            routineTimer.reset()

        for i in range(len(texts)):
            texts[i].setAutoDraw(True)

        # keep track of which components have finished
        trialComponents = [textDot]
        for thisComponent in trialComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1


        if count == 1:
            send_event(event_type='ROWS')


        # --- Run Routine "trial" ---
        while continueRoutine and routineTimer.getTime() < args.shift_time:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            # Run 'Each Frame' code from code

            # *textDot* updates
            if textDot.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
                # keep track of start time/frame for later
                textDot.frameNStart = frameN  # exact frame index
                textDot.tStart = t  # local t and not account for scr refresh
                textDot.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(textDot, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'textDot.started')
                textDot.setAutoDraw(True)
            if textDot.status == STARTED:
                # is it time to stop? (based on global clock, using actual start)
                if tThisFlipGlobal > textDot.tStartRefresh + args.shift_time - frameTolerance:
                    # keep track of stop time/frame for later
                    textDot.tStop = t  # not accounting for scr refresh
                    textDot.frameNStop = frameN  # exact frame index
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'textDot.stopped')
                    textDot.setAutoDraw(False)

            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()

            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in trialComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished

            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()

        # --- Ending Routine "trial" ---
        for thisComponent in trialComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)


        main_row_words_len_without_punc, _ = calculate_length_without_punctuation_and_indexes(main_row_words)
        if count == main_row_words_len_without_punc:
            # eci_client.send_event(event_type='SENTENCE_END')

            send_event(event_type='ROWE')

            count = 1
        else:
            count += 1


        for i in range(len(texts)):
            texts[i].setAutoDraw(False)

        # using non-slip timing so subtract the expected duration of this Routine (unless ended on request)
        if routineForceEnded:
            routineTimer.reset()
        else:
            routineTimer.addTime(-args.shift_time)
    # completed 1.0 repeats of 'trialsPlay'

    # --- Prepare to start Routine "GoodbyePage" ---
    continueRoutine = True
    routineForceEnded = False
    # update component parameters for each repeat
    key_Goodbye.keys = []
    key_Goodbye.rt = []
    _key_Goodbye_allKeys = []
    # keep track of which components have finished
    GoodbyePageComponents = [textGoodbye, key_Goodbye]
    for thisComponent in GoodbyePageComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    send_event("STOP_RECORDING")

    # --- Run Routine "GoodbyePage" ---
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *textGoodbye* updates
        if textGoodbye.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            # keep track of start time/frame for later
            textGoodbye.frameNStart = frameN  # exact frame index
            textGoodbye.tStart = t  # local t and not account for scr refresh
            textGoodbye.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(textGoodbye, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'textGoodbye.started')
            textGoodbye.setAutoDraw(True)

        # *key_Goodbye* updates
        waitOnFlip = False
        if key_Goodbye.status == NOT_STARTED and tThisFlip >= 0.0 - frameTolerance:
            # keep track of start time/frame for later
            key_Goodbye.frameNStart = frameN  # exact frame index
            key_Goodbye.tStart = t  # local t and not account for scr refresh
            key_Goodbye.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(key_Goodbye, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'key_Goodbye.started')
            key_Goodbye.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(key_Goodbye.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(key_Goodbye.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if key_Goodbye.status == STARTED and not waitOnFlip:
            theseKeys = key_Goodbye.getKeys(keyList=['space'], waitRelease=False)
            _key_Goodbye_allKeys.extend(theseKeys)
            if len(_key_Goodbye_allKeys):
                key_Goodbye.keys = _key_Goodbye_allKeys[-1].name  # just the last key pressed
                key_Goodbye.rt = _key_Goodbye_allKeys[-1].rt
                # a response ends the routine
                continueRoutine = False

        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()

        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in GoodbyePageComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "GoodbyePage" ---
    for thisComponent in GoodbyePageComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # check responses
    if key_Goodbye.keys in ['', [], None]:  # No response was made
        key_Goodbye.keys = None
    thisExp.addData('key_Goodbye.keys', key_Goodbye.keys)
    if key_Goodbye.keys != None:  # we had a response
        thisExp.addData('key_Goodbye.rt', key_Goodbye.rt)
    thisExp.nextEntry()
    # the Routine "GoodbyePage" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

    # --- End experiment ---
    # Flip one final time so any remaining win.callOnFlip()
    # and win.timeOnFlip() tasks get executed before quitting
    win.flip()

    # these shouldn't be strictly necessary (should auto-save)
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)
    logging.flush()

    thisExp.abort()  # or data files will save again on exit
    win.close()
    core.quit()

if __name__ == '__main__':
    # --- Change parameters here ---
    parser = argparse.ArgumentParser(description='Parameters that can be changed in this experiment')
    parser.add_argument('--highlight_color', type=str, default='red', help='Highlight color of the captions')
    parser.add_argument('--shift_time', type=float, default=0.25, help='The shifting time of the highlighted character')
    parser.add_argument('--novel_path', type=str,
                        default=r"example/name.xlsx",
                        help='The path of the  .xlsx format novel you want to play')
    parser.add_argument('--preface_path', type=str,
                        default=r"example/preface_name.xlsx",
                        help='The path of the  .xlsx format preface you want to play')
    parser.add_argument('--fullscreen', type=bool, default=False,
                        help='Whether to set a full screen')
    parser.add_argument('--rest_period', type=int, default=1,
                        help='The chapter interval of rest')
    parser.add_argument('--force_rest_time', type=int, default=20,
                        help='The forced rest time')
    parser.add_argument('--isFirstSession', action='store_true',
                        help='Whether this is the first session of the experiment, this will determine whether to '
                             'display the preface before the formal experiment'
                        )

    args = parser.parse_args()
    send_event("PRES")
    main_experiment()
