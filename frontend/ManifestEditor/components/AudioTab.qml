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

    property real speechPauseSec: 0.5
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

        realParams: ([{name: "Speech Pause", from: 0, to: 5, stepSize: 0.1, unit: "sec."}])
        selectionParams: ([{name: "Speaker Identification", options: ["Yes", "No"]}])

        onUserPathChanged: (newPath) => {
            manifest.transcript = newPath;
        }

        onRunTriggered: {
            statusGlobalTranscript = true;
            preprocessingPipeline.run_transcript_global(transcriptTab.speechPauseSec)
        }

        onParamChanged: (name, value) => {
            if (name === "Speech Pause") {
                transcriptTab.speechPauseSec = value;
                print(transcriptTab.speechPauseSec);
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