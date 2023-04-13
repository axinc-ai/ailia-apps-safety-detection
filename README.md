# ailia APPS Safety Detection

Detects people who are lying down or sitting down.

# Functions

- Detect lying down and sitting down

# Requirements

- Windows, macOS, Linux
- Python 3.7 and later
- ailia SDK 1.2.13 and later

# Basic Usage

1. Put this command to open GUI.

```
python3 ailia-apps-safety-detection.py
```

![Open GUI](./tutorial/open.png)

2. Push "Input video" button to select input video

3. Push "Run" button to execute the app

![Run app](./tutorial/run.png)

# Architecture

```mermaid
classDiagram
`ailia APPS Safety Detection` <|-- `Fall Detection` : Person Status
`Fall Detection` <|-- `ailia.pose_estimator` : Person Keypoints
`ailia.pose_estimator` <|-- `ailia.detector` : Person Detection (Bounding box)
`ailia APPS Safety Detection` : Input Video, Output Video, Output csv
`Fall Detection` : Traditional Algorithm
`ailia.detector` <|-- `ailia.core` : Inference Engine
`ailia.core` <|-- `onnx` : Model
`ailia.pose_estimator` <|-- `ailia.core` : Inference Engine
`ailia.pose_estimator` : PoseEstimation
`ailia.detector` : ailiaDetectorCompute
`ailia.core` : ailiaCreate, ailiaPredict, ailiaDestroy
`ailia.core` <|-- Backend : Acceleration
`onnx` : yolox_s, poseresnet
`Backend` : CPU, GPU
```

# Test video

TBD

