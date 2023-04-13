# ailia APPS Safety Detection
# (C) 2023 AXELL CORPORATION

import sys
import time
from signal import SIGINT

import numpy as np
import cv2
import json
from matplotlib import cm
from PIL import Image, ImageTk

import ailia

# import original modules
sys.path.append('./util')
from utils import get_base_parser, update_parser
# logger
from logging import getLogger  # noqa: E402

import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
import os

logger = getLogger(__name__)

# ======================
# Arguemnt Parser Config
# ======================

parser = get_base_parser(
    'ailia APPS safety detection', None, None)

args = update_parser(parser)


# ======================
# Video
# ======================

input_index = 0
listsInput = None
ListboxInput = None
input_list = []

def get_input_list():
    if args.debug:
        return ["Camera:0"]

    index = 0
    inputs = []
    while True:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            inputs.append("Camera:"+str(index))
        else:
            break
        index=index+1
        cap.release()

    if len(inputs) == 0:
        inputs.append("demo.mp4")

    return inputs

def input_changed(event):
    global input_index, input_list, textInputVideoDetail
    selection = event.widget.curselection()
    if selection:
        input_index = selection[0]
    else:
        input_index = 0   
    if "Camera:" in input_list[input_index]:
        textInputVideoDetail.set(input_list[input_index])
    else:
        textInputVideoDetail.set(os.path.basename(input_list[input_index]))
        
    #print("input",input_index)

def input_video_dialog():
    global textInputVideoDetail, listsInput, ListboxInput, input_index, input_list
    fTyp = [("All Files", "*.*"), ("Video files","*.mp4")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    file_name = tk.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
    if len(file_name) != 0:
        textInputVideoDetail.set(os.path.basename(file_name))
        input_list.append(file_name)
        listsInput.set(input_list)
        ListboxInput.select_clear(input_index)
        input_index = len(input_list)-1
        ListboxInput.select_set(input_index)

def apply_path_to_ui():
    global textOutputVideoDetail
    textOutputVideoDetail.set(os.path.basename(args.savepath))
    global textOutputCsvDetail
    textOutputCsvDetail.set(os.path.basename(args.csvpath))
    global textOutputImageDetail
    textOutputImageDetail.set(os.path.basename(args.imgpath))

def output_video_dialog():
    global textOutputVideoDetail
    fTyp = [("Output Video File", "*")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    file_name = tk.filedialog.asksaveasfilename(filetypes=fTyp, initialdir=iDir)
    if len(file_name) != 0:
        args.savepath = file_name
        apply_path_to_ui()

def output_csv_dialog():
    global textOutputCsvDetail
    fTyp = [("Output Csv File", "*")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    file_name = tk.filedialog.asksaveasfilename(filetypes=fTyp, initialdir=iDir)
    if len(file_name) != 0:
        args.csvpath = file_name
        apply_path_to_ui()

def output_img_dialog():
    fTyp = [("Output Image Folder", "*")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    file_name = tk.filedialog.askdirectory(initialdir=iDir)
    if len(file_name) != 0:
        args.imgpath = file_name
        apply_path_to_ui()

# ======================
# Environment
# ======================

env_index = args.env_id

def get_env_list():
    env_list = []
    for env in ailia.get_environment_list():
        env_list.append(env.name)
    return env_list  

def environment_changed(event):
    global env_index
    selection = event.widget.curselection()
    if selection:
        env_index = selection[0]
    else:
        env_index = 0
    #print("env",env_index)

# ======================
# Model
# ======================

model_index = 0

def get_model_list():
    model_list = ["yolox_poseresnet"]
    return model_list  

def model_changed(event):
    global model_index
    selection = event.widget.curselection()
    if selection:
        model_index = selection[0]
    else:
        model_index = 0
    #print("model",model_index)

# ======================
# Area setting
# ======================

def get_video_path():
    global input_list, input_index
    if "Camera:" in input_list[input_index]:
        return input_index
    else:
        return input_list[input_index]

# ======================
# Menu functions
# ======================

def get_settings():
    settings = {}

    global model_index
    settings["model_type"] = get_model_list()[model_index]

    global detectionThresholdTextEntry
    settings["detection_threshold"] = detectionThresholdTextEntry.get()

    global poseThresholdTextEntry
    settings["pose_threshold"] = poseThresholdTextEntry.get()

    global checkBoxCategoryFallenBln
    if checkBoxCategoryFallenBln.get():
        settings["category_fallen"] = True
    else:
        settings["category_fallen"] = False
    
    global checkBoxCategorySittingBln
    if checkBoxCategorySittingBln.get():
        settings["category_sitting"] = True
    else:
        settings["category_sitting"] 

    settings["savepath"] = args.savepath
    settings["csvpath"] = args.csvpath
    settings["imgpath"] = args.imgpath

    return settings

def set_settings(settings):
    global model_index, ListboxModel
    model_list = get_model_list()
    for i in range(len(model_list)):
        if settings["model_type"] == model_list[i]:
            model_index = i
    ListboxModel.select_set(model_index)

    global detectionThresholdTextEntry
    detectionThresholdTextEntry.delete(0, tk.END)
    detectionThresholdTextEntry.insert(0, str(settings["detection_threshold"]))

    global poseThresholdTextEntry
    poseThresholdTextEntry.delete(0, tk.END)
    poseThresholdTextEntry.insert(0, str(settings["pose_threshold"]))

    global checkBoxCategoryFallenBln
    checkBoxCategoryFallenBln.set(settings["category_fallen"])

    global checkBoxCategorySittingBln
    checkBoxCategorySittingBln.set(settings["category_sitting"])

    if "savepath" in settings:
        args.savepath = settings["savepath"]
    if "csvpath" in settings:
        args.csvpath = settings["csvpath"]
    if "imgpath" in settings:
        args.imgpath = settings["imgpath"]
    
    apply_path_to_ui()

def menu_file_open_click():
    fTyp = [("Config files","*.json")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    file_name = tk.filedialog.askopenfilename(filetypes=fTyp, initialdir=iDir)
    if len(file_name) != 0:
        with open(file_name, 'r') as json_file:
            settings = json.load(json_file)
            set_settings(settings)

def menu_file_saveas_click():
    fTyp = [("Config files", "*.json")]
    iDir = os.path.abspath(os.path.dirname(__file__))
    file_name = tk.filedialog.asksaveasfilename(filetypes=fTyp, initialdir=iDir)
    if len(file_name) != 0:
        with open(file_name, 'w') as json_file:
            settings = get_settings()
            json.dump(settings, json_file)

def menu(root):
    menubar = tk.Menu(root)

    menu_file = tk.Menu(menubar, tearoff = False)
    menu_file.add_command(label = "Load settings",  command = menu_file_open_click,  accelerator="Ctrl+O")
    menu_file.add_command(label = "Save settings", command = menu_file_saveas_click, accelerator="Ctrl+S")
    #menu_file.add_separator() # 仕切り線
    #menu_file.add_command(label = "Quit",            command = root.destroy)

    menubar.add_cascade(label="File", menu=menu_file)

    root.config(menu=menubar)

# ======================
# GUI functions
# ======================

root = None
resolutionTextEntry = None
areaThresholdTextEntry = None
labelAcceptTextEntry = None
labelDenyTextEntry = None
checkBoxMultipleAssignBln = None
ListboxModel = None

def ui():
    # rootメインウィンドウの設定
    global root
    root = tk.Tk()
    root.title("ailia APPS Safety Detection")
    root.geometry("720x360")

    # メニュー作成
    menu(root)

    # 環境情報取得
    global input_list
    input_list = get_input_list()
    model_list = get_model_list()
    env_list = get_env_list()

    # メインフレームの作成と設置
    frame = ttk.Frame(root)
    frame.pack(padx=10,pady=10)

    textInputVideo = tk.StringVar(frame)
    textInputVideo.set("Input video")
    buttonInputVideo = tk.Button(frame, textvariable=textInputVideo, command=input_video_dialog, width=14)
    buttonInputVideo.grid(row=0, column=0, sticky=tk.NW)

    global textInputVideoDetail
    textInputVideoDetail = tk.StringVar(frame)
    textInputVideoDetail.set(input_list[input_index])
    labelInputVideoDetail = tk.Label(frame, textvariable=textInputVideoDetail)
    labelInputVideoDetail.grid(row=0, column=1, sticky=tk.NW)

    textOutputVideo = tk.StringVar(frame)
    textOutputVideo.set("Output video")
    buttonOutputVideo = tk.Button(frame, textvariable=textOutputVideo, command=output_video_dialog, width=14)
    buttonOutputVideo.grid(row=1, column=0, sticky=tk.NW)

    global textOutputVideoDetail
    textOutputVideoDetail = tk.StringVar(frame)
    textOutputVideoDetail.set(args.savepath)
    labelOutputVideoDetail= tk.Label(frame, textvariable=textOutputVideoDetail)
    labelOutputVideoDetail.grid(row=1, column=1, sticky=tk.NW)

    textOutputCsv = tk.StringVar(frame)
    textOutputCsv.set("Output csv")
    buttonOutputCsv = tk.Button(frame, textvariable=textOutputCsv, command=output_csv_dialog, width=14)
    buttonOutputCsv.grid(row=2, column=0, sticky=tk.NW)

    global textOutputCsvDetail
    textOutputCsvDetail = tk.StringVar(frame)
    textOutputCsvDetail.set(args.csvpath)
    labelOutputCsvDetail= tk.Label(frame, textvariable=textOutputCsvDetail)
    labelOutputCsvDetail.grid(row=2, column=1, sticky=tk.NW)

    textOutputImage = tk.StringVar(frame)
    textOutputImage.set("Output image")
    buttonOutputImage = tk.Button(frame, textvariable=textOutputImage, command=output_img_dialog, width=14)
    buttonOutputImage.grid(row=3, column=0, sticky=tk.NW)

    global textOutputImageDetail
    textOutputImageDetail = tk.StringVar(frame)
    textOutputImageDetail.set(args.imgpath)
    labelOutputImageDetail= tk.Label(frame, textvariable=textOutputImageDetail)
    labelOutputImageDetail.grid(row=3, column=1, sticky=tk.NW)

    textTrainVideo = tk.StringVar(frame)
    textTrainVideo.set("Run")
    buttonTrainVideo = tk.Button(frame, textvariable=textTrainVideo, command=run, width=14)
    buttonTrainVideo.grid(row=4, column=0, sticky=tk.NW)

    textTrainVideo = tk.StringVar(frame)
    textTrainVideo.set("Stop")
    buttonTrainVideo = tk.Button(frame, textvariable=textTrainVideo, command=stop, width=14)
    buttonTrainVideo.grid(row=5, column=0, sticky=tk.NW)

    global listsInput, ListboxInput

    textInputVideoHeader = tk.StringVar(frame)
    textInputVideoHeader.set("Inputs")
    labelInputVideoHeader = tk.Label(frame, textvariable=textInputVideoHeader)
    labelInputVideoHeader.grid(row=0, column=2, sticky=tk.NW)

    listsInput = tk.StringVar(value=input_list)
    ListboxInput = tk.Listbox(frame, listvariable=listsInput, width=26, height=4, selectmode="single", exportselection=False)
    ListboxInput.bind("<<ListboxSelect>>", input_changed)
    ListboxInput.select_set(input_index)
    ListboxInput.grid(row=1, column=2, sticky=tk.NW, rowspan=3, columnspan=2)

    lists = tk.StringVar(value=model_list)
    listEnvironment =tk.StringVar(value=env_list)

    global ListboxModel
    ListboxModel = tk.Listbox(frame, listvariable=lists, width=26, height=4, selectmode="single", exportselection=False)
    ListboxEnvironment = tk.Listbox(frame, listvariable=listEnvironment, width=26, height=4, selectmode="single", exportselection=False)

    ListboxModel.bind("<<ListboxSelect>>", model_changed)
    ListboxEnvironment.bind("<<ListboxSelect>>", environment_changed)

    ListboxModel.select_set(model_index)
    ListboxEnvironment.select_set(env_index)

    textModel = tk.StringVar(frame)
    textModel.set("Models")
    labelModel = tk.Label(frame, textvariable=textModel)
    labelModel.grid(row=4, column=2, sticky=tk.NW, rowspan=1)
    ListboxModel.grid(row=5, column=2, sticky=tk.NW, rowspan=2)

    textEnvironment = tk.StringVar(frame)
    textEnvironment.set("Environment")
    labelEnvironment = tk.Label(frame, textvariable=textEnvironment)
    labelEnvironment.grid(row=8, column=2, sticky=tk.NW, rowspan=1)
    ListboxEnvironment.grid(row=9, column=2, sticky=tk.NW, rowspan=4)

    textOptions = tk.StringVar(frame)
    textOptions.set("Options")
    labelOptions = tk.Label(frame, textvariable=textOptions)
    labelOptions.grid(row=0, column=3, sticky=tk.NW)

    textDetectionThreshold = tk.StringVar(frame)
    textDetectionThreshold.set("Detection Threshold")
    labeDetectionThreshold = tk.Label(frame, textvariable=textDetectionThreshold)
    labeDetectionThreshold.grid(row=1, column=3, sticky=tk.NW)

    global detectionThresholdTextEntry
    detectionThresholdTextEntry = tkinter.Entry(frame, width=20)
    detectionThresholdTextEntry.insert(tkinter.END,"0.4")
    detectionThresholdTextEntry.grid(row=2, column=3, sticky=tk.NW, rowspan=1)

    textPoseThreshold= tk.StringVar(frame)
    textPoseThreshold.set("Pose Threshold")
    labelPoseThreshold = tk.Label(frame, textvariable=textPoseThreshold)
    labelPoseThreshold.grid(row=3, column=3, sticky=tk.NW)

    global poseThresholdTextEntry
    poseThresholdTextEntry = tkinter.Entry(frame, width=20)
    poseThresholdTextEntry.insert(tkinter.END,"0.4")
    poseThresholdTextEntry.grid(row=4, column=3, sticky=tk.NW, rowspan=1)

    textLabels = tk.StringVar(frame)
    textLabels.set("Detection Category")
    labelLabels = tk.Label(frame, textvariable=textLabels)
    labelLabels.grid(row=5, column=3, sticky=tk.NW)

    global checkBoxCategoryFallenBln
    checkBoxCategoryFallenBln = tkinter.BooleanVar()
    checkBoxCategoryFallenBln.set(True)
    checkBoxCategoryFallenAssign = tkinter.Checkbutton(frame, variable=checkBoxCategoryFallenBln, text='Fallen')
    checkBoxCategoryFallenAssign.grid(row=6, column=3, sticky=tk.NW, rowspan=1)

    global checkBoxCategorySittingBln
    checkBoxCategorySittingBln = tkinter.BooleanVar()
    checkBoxCategorySittingBln.set(True)
    checkBoxCategorySittingAssign = tkinter.Checkbutton(frame, variable=checkBoxCategorySittingBln, text='Sitting')
    checkBoxCategorySittingAssign.grid(row=7, column=3, sticky=tk.NW, rowspan=1)

    root.mainloop()

# ======================
# MAIN functions
# ======================

def main():
    args.savepath = ""
    args.csvpath = ""
    args.imgpath = ""
    ui()

import subprocess

proc = None

def run():
    global proc

    if not (proc==None):
        proc.kill()
        proc=None

    cmd = sys.executable

    args_dict = {}#vars(args)
    args_dict["video"] = get_video_path()
        
    settings = get_settings()
    if settings["savepath"]:
        args_dict["savepath"] = settings["savepath"]
    if settings["csvpath"]:
        args_dict["csvpath"] = settings["csvpath"]
    if settings["imgpath"]:
        args_dict["imgpath"] = settings["imgpath"]

    global model_index
    args_dict["model_type"] = get_model_list()[model_index].split("-")[0]

    global env_index
    args_dict["env_id"] = env_index

    global detectionThresholdTextEntry
    if detectionThresholdTextEntry:
        args_dict["detection_threshold"] = float(detectionThresholdTextEntry.get())

    global poseThresholdTextEntry
    if poseThresholdTextEntry:
        args_dict["pose_threshold"] = float(poseThresholdTextEntry.get())

    global checkBoxCategoryFallenBln
    if checkBoxCategoryFallenBln.get():
        args_dict["category_fallen"] = True

    global checkBoxCategorySittingBln
    if checkBoxCategorySittingBln.get():
        args_dict["category_sitting"] = True

    options = []
    for key in args_dict:
        if key=="ftype":
            continue
        if args_dict[key] is not None:
            if args_dict[key] is True:
                options.append("--"+key)
            elif args_dict[key] is False:
                continue
            else:
                options.append("--"+key)
                options.append(str(args_dict[key]))

    cmd = [cmd, "pose_resnet.py"] + options
    print(" ".join(cmd))

    dir = "./pose_estimation/pose_resnet/"

    proc = subprocess.Popen(cmd, cwd=dir)
    try:
        outs, errs = proc.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        pass


def stop():
    global proc
    if not (proc==None):
        proc.send_signal(SIGINT)
        proc=None

if __name__ == '__main__':
    main()
