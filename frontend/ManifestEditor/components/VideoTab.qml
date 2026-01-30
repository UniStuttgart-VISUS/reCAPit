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
    id: videoTab

    property alias movementIndicator: movementRunningIndicator
    property alias heatmapGazeIndicator: heatmapGazeRunningIndicator
    property alias heatmapMoveIndicator: heatmapMoveRunningIndicator
    property alias gazeAttentionIndicator: gazeAttentionRunningIndicator
    property string currStdOut: ""

    GroupBox {
        Layout.fillWidth: true

        title: "Video Processing"

        GridLayout {
            anchors.fill: parent
            columns: 3
            rowSpacing: 15
            columnSpacing: 15

            Text {
                text: "Register Movement"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: movementRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    movementRunningIndicator.indeterminate = true;
                    videoTab.currStdOut = "";
                    preprocessingPipeline.run_video_movement()
                }
            }

            Text {
                text: "Gaze Attention"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: gazeAttentionRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    gazeAttentionRunningIndicator.indeterminate = true;
                    videoTab.currStdOut = "";
                    preprocessingPipeline.run_gaze_attention()
                }
            }

            Text {
                text: "Heatmap Gaze"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: heatmapGazeRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    heatmapGazeRunningIndicator.indeterminate = true;
                    videoTab.currStdOut = "";
                    preprocessingPipeline.run_video_heatmap_gaze()
                }
            }

            Text {
                text: "Heatmap Movement"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: heatmapMoveRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    heatmapMoveRunningIndicator.indeterminate = true;
                    videoTab.currStdOut = "";
                    preprocessingPipeline.run_video_heatmap_move()
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
                videoTab.currStdOut += "\n" + line;
            }
        }

        ScrollView {
            anchors.fill: parent
            anchors.margins: 10
            Text {
                width: parent.width
                color: "#666"
                text: videoTab.currStdOut;
                wrapMode: Text.WordWrap
            }
        }
    }
}