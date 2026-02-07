import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Shapes 1.2
import QtQml
import QtQml.Models
import QtQuick.Controls.Basic
import QtQuick.Effects

import "."

ColumnLayout {
    id: transcriptTab

    property alias statusGlobalTranscript: transcriptGlobalRunner.isRunning
    property alias statusRecordingTranscript: transcriptRecordingRunner.isRunning

    property int numberSpeakers: 0
    property string hfToken: ""
    property string device: "cpu"
    property bool speakerIdentificationEnabled: true

    property bool audioExists: manifest.is_valid_file(manifest.audio)
    property bool transcriptExists: manifest.is_valid_file(manifest.transcript)

    spacing: 15

    Connections {
        target: preprocessingPipeline
        function onTranscriptGlobalCompleted(returnCode) { 
            transcriptTab.statusGlobalTranscript = false;
        }
        function onTranscriptRecordingCompleted(returnCode) { 
            transcriptTab.statusRecordingTranscript = false;
        }
    }

    ProcessRunner {
        id: transcriptGlobalRunner
        Layout.fillWidth: true

        title: "Generate Transcript"
        description: "Generate a transcript using OpenAI's Whisper speech-to-text model."
        requirements: ([{name: "Audio", 'satisfies': audioExists}])
        enabled: !preprocessingPipeline.pipeline_running && audioExists
        pathInfo: ({path: manifest.transcript, is_valid: transcriptExists, is_dir: false, file_extensions: ["CSV files (*.csv)"]})

        realParams: ([{name: "Number of Speakers", from: 0, to: 10, stepSize: 1, unit: ""}])
        selectionParams: ([{name: "Speaker Identification", options: ["Yes", "No"]}, {name: "Device", options: ["CPU", "GPU"]}])
        textInputParams: ([{name: "Hugging Face Token", inputMask: ""}])

        onUserPathChanged: (newPath) => {
            manifest.transcript = newPath;
        }

        onRunTriggered: {
            statusGlobalTranscript = true;
            preprocessingPipeline.run_transcript_global(transcriptTab.numberSpeakers, transcriptTab.hfToken, 
                                                        transcriptTab.device, transcriptTab.speakerIdentificationEnabled);
        }

        onParamChanged: (name, value) => {
            if (name === "Number of Speakers") {
                transcriptTab.numberSpeakers = value;
            }
            else if (name === "Device") {
                transcriptTab.device = value;
            }
            else if (name === "Hugging Face Token") {
                transcriptTab.hfToken = value;
            }
            else if (name === "Speaker Identification") {
                print(value === "Yes")
                transcriptTab.speakerIdentificationEnabled = value === "Yes";
            }
        }
    }

    ProcessRunner {
        id: transcriptRecordingRunner
        Layout.fillWidth: true
        title: "Split Transcript"
        description: "Split the previously generated transcript using speaker id"
        requirements: ([{name: "Transcript", 'satisfies': transcriptExists}])
        enabled: !preprocessingPipeline.pipeline_running && transcriptExists
        onRunTriggered: {
            statusRecordingTranscript = true;
            transcriptTab.currStdOut = "";
            preprocessingPipeline.run_transcript_recording()
        }
    }
}