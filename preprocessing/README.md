# Multimodal Feature Extraction

## The Manifest File

reCAPit enables the analysis of various derived features (**artifacts**) extracted from multiple data sources, including video, speech, and eye tracking (**sources**).
All **sources** and **artifacts** are managed using a JSON file called `manifest.json`, which contains both manually defined entries and automatically generated entries.
The provided scripts automatically add `artifact` entries (**registering**) to the `manifest.json` file based on the **sources** you manually specified.

## Requirements

Scripts are organized in directories according to the sources they extract features from (transcript/video/gaze).
Please make sure [astral-sh/uv](https://github.com/astral-sh/uv) is installed on your system.
UV is a Python package and project manager that eases the deployment of applications written in Python.

To launch a script, navigate to the respective directory and `uv run register_[NAME].py` inside your terminal, and replace `NAME` with the respective script name.


> [!NOTE]
> Please note that certain scripts depend on PyTorch. For best performance, it is recommended to run them on systems with a GPU and CUDA capabilities. Please make sure to install a PyTorch version that is compatible with the CUDA version available on your system.

# Scripts

The scripts provided in this folder can be used to extract a variety of **artifacts** based on the specified sources.
Each script that can register artifacts follows this naming convention: `register_*.py`.

* Most importantly, **sources** need to be specified by the user.
* Some scripts may also depend on artifacts produced by other scripts.
* Only registered artifacts in the manifest can be used by reCAPit.
* If the script terminates without errors, it adds the respective artifact to the manifest file.
* Each script requires the manifest file as input, plus additional parameters pertaining to the specific feature extraction.

## 📄 Transcript

### `register_transcript.py`

Registers transcript data and processes it for individual recordings by mapping speaker information to recording IDs and roles.

* 📥 This script requires a transcript file (CSV format) and recordings defined in the manifest
* 📤 This script will register `artifacts/transcript` globally and `artifacts/transcript` for each individual recording.

Please note that the actual transcript generation must be performed with an external tool.
There are many open-source tools that can be used for speech-to-text transformation, such as:

- **noScribe - https://github.com/kaixxx/noScribe** 
- **whisper-standalone-win - https://github.com/Purfview/whisper-standalone-win**

The transcript must be provided as a CSV file with the following required columns:

| Column | Type | Description |
|--------|------|-------------|
| `speaker` | string | Speaker identifier that matches recording IDs in the manifest |
| `text` | string | Transcribed speech content |
| `start timestamp [sec]` | float | Start time of the speech segment in seconds |
| `end timestamp [sec]` | float | End time of the speech segment in seconds |


> [!IMPORTANT]
> The speaker IDs must exactly match the recording IDs defined in the manifest. Many tools struggle with precise speaker identification and will most likely produce suboptimal results with more than two speakers. Hence, often manual corrections of the speaker assignments are necessary.

> [!TIP]
> Many tools such as the ones mentioned above output subtitle files (.srt or .vtt), which you can transform to the required CSV format using the helper scripts `transcript/srt2csv.py` and `transcript/vtt2csv.py`.


## 🧩 Segmentation

### `register_segment_initial.py` 

Performs initial segmentation based on a previously registered multivariate time series, specified by `input_signal`.

* 📥 The `input_signal` must be a registered multivariate time series `artifacts/multi_time`
* 📤 This script will register `artifacts/segments/initial`.

> [!NOTE]
> Currently, `movement` and `attention` are available, which you can extract using the scripts `videos/workspace/register_movement.py` and `gaze/register_attention.py`, respectively.

### `register_segment_refine.py` 

Refines an initial segmentation using lexical features extracted from the transcript. This refinement effectively splits the initial segments by detecting transitions between subsequent discussions.

* 📥 This script requires a previously registered initial segmentation `artifacts/segments/initial` (see [register_segment_initial.py](#register_segment_initial.py)) and a registered transcript `artifacts/transcript`
* 📤 This script will register `artifacts/segments/refined`.

> [!NOTE]
> Refinement is not a necessary step, and it is legitimate to perform only the initial segmentation. However, if you notice particularly long segments after initial segmentation, you may be advised to perform refinement.

### `segment_attributes.py` 

Uses ChatGPT to automatically generate text summaries and titles for each segment of an existing segmentation result.
The outputs are populated into the existing segmentation results as new data columns.

* 📥 This script requires a previously registered segmentation, either `artifacts/segments/initial` or `artifacts/segments/refined`
* 📤 This script will not register anything

> [!NOTE]
> This is a special script that does not register any new artifact, but instead adds new data to an existing segmentation result.

## 🎥 Video

### `register_movement.py`

Extracts movement activity from workspace video using background subtraction and hand detection. This script analyzes video frames to detect hand movements within defined areas of interest.

* 📥 This script requires a registered workspace video `sources/videos/workspace` and areas of interest `sources/areas_of_interests`
* 📤 This script will register a multivariate time series `artifacts/multi_time/movement`.

> [!NOTE]
> The output of this script `movement` can be used as an input signal for [register_segment_initial.py](#register_segment_initial.py)

### `register_heatmaps_gaze.py`

Generates gaze-based heatmaps from eye tracking data by creating temporal aggregations of fixation data overlaid on the workspace video.

* 📥 This script requires a registered workspace video `sources/videos/workspace` and mapped fixations from recordings with `artifacts/mapped_fixations` (see [register_attention.py](#register_attention.py))
* 📤 This script will register `artifacts/video_overlay/attention`.

### `register_heatmaps_move.py`

Creates movement-based heatmaps by analyzing hand activity patterns within areas of interest over time windows.

* 📥 This script requires a registered workspace video `sources/videos/workspace` and areas of interest `sources/areas_of_interests`
* 📤 This script will register `artifacts/video_overlay/movement`.

## 👁️ Gaze

### `register_attention.py`

Processes eye tracking data to compute attention signals by mapping surface fixations to areas of interest and generating time series data.

* 📥 This script requires recordings with `sources/surface_fixations` and areas of interest `sources/areas_of_interests`
* 📤 This script will register a global artifact `artifacts/multi_time/attention` and recording specific artifacts `artifacts/mapped_fixations`.

> [!NOTE]
> The global artifact of this script `attention` can be used as an input signal for [register_segment_initial.py](#register_segment_initial.py)

## 🗒️ Digital Notes

### `register_notes.py`

Analyzes temporal changes in an instrumented Word document by processing document snapshots and computing text differences between versions.

* 📥 This script requires notes snapshots `sources/notes_snapshots` (directory containing .docm files with timestamp-based filenames)
* 📤 This script will register `artifacts/notes`.

> [!NOTE]
> The script uses diff-match-patch algorithms to identify insertions and deletions between document versions. It samples documents at configurable intervals (default: 150 seconds) and generates HTML visualizations of changes. Document filenames should be timestamps for proper temporal ordering.

## License and Third-Party Notices

This project includes third-party software:

### Cisco H.264 Binaries 

This product includes software developed by Cisco Systems, licensed under the BSD 2-Clause License:

Copyright (c) 2013, Cisco Systems
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this
  list of conditions and the following disclaimer in the documentation and/or
  other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
