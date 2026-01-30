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

    property string currStdOut: "file:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of null\nfile:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of null\nfile:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of nullfile:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of null\n";
    property alias statusGlobalTranscript: transcriptRunningIndicator.indeterminate
    property alias statusRecordingTranscript: transcriptRunningIndicator2.indeterminate

    GroupBox {
        Layout.fillWidth: true

        title: "Transcript"

        GridLayout {
            anchors.fill: parent
            columns: 3
            rowSpacing: 15
            columnSpacing: 15

            Text {
                text: "Generate Transcript"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: transcriptRunningIndicator
                indeterminate: false
                value: 1.0
            }


            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running && preprocessingPipeline.global_transcript_ready
                onClicked: {
                    transcriptRunningIndicator.indeterminate = true;
                    transcriptTab.currStdOut = "";
                    preprocessingPipeline.run_transcript_global()
                }
            }

            Text {
                text: "Split Transcript"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: transcriptRunningIndicator2
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running && preprocessingPipeline.recording_transcript_ready
                onClicked: {
                    transcriptRunningIndicator2.indeterminate = true;
                    transcriptTab.currStdOut = "";
                    preprocessingPipeline.run_transcript_recording()
                }
            }

        }
    }
    Rectangle {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.maximumHeight: 300
        Layout.bottomMargin: 25
        Layout.topMargin: 5
        
        color: "#e8e8e8"
        radius: 5

        Connections {
            target: preprocessingPipeline
            function onStdOutLine(line) { 
                transcriptTab.currStdOut += "\n" + line;
            }
        }

        ScrollView {
            anchors.fill: parent
            anchors.margins: 10
            Text {
                width: parent.width
                id: stdoutText
                color: "#666"
                text: transcriptTab.currStdOut;
                wrapMode: Text.WordWrap
            }
        }
    }
}