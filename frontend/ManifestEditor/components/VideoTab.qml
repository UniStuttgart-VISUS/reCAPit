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

    property alias statusHeatmapMove: videoMovementRunner.isRunning
    property alias statusHeatmapGaze: heatmapGazeRunner.isRunning
    property alias statusMovement: videoMovementRunner.isRunning

    property real downsamplingFactor: 1.0
    property bool detectShadows: false

    property real stepSizeGaze: 1.0
    property int kernelSizeGaze: 3

    property real stepSizeMove: 1.0
    property int kernelSizeMove: 3

    property bool attentionExists: manifest.is_valid_file(manifest.attention)
    property bool workspaceVideoExists: manifest.is_valid_file(manifest.video_workspace)
    property bool aoiExists: manifest.is_valid_file(manifest.aoi)

    Connections {
        target: preprocessingPipeline
        function onVideoHeatmapGazeCompleted(returnCode) { 
            videoTab.statusHeatmapGaze = false;
        }
        function onVideoHeatmapMoveCompleted(returnCode) { 
            videoTab.statusHeatmapMove = false;
        }
    }


    ProcessRunner {
        id: videoMovementRunner
        Layout.fillWidth: true
        title: "Workspace Hand Activity"
        description: "Generate a transcript using OpenAI's Whisper speech-to-text model."
        requirements: ([
            {name: "Workspace Video", 'satisfies': workspaceVideoExists},
            {name: "Areas of interests", 'satisfies': aoiExists}
        ])
        enabled: !preprocessingPipeline.pipeline_running && workspaceVideoExists && aoiExists
        onRunTriggered: {
            statusMovement = true;
            preprocessingPipeline.run_video_movement(videoTab.downsamplingFactor, videoTab.downsamplingFactor)
        }
        realParams: ([{name: "Downsampling Factor", from: 1, to: 16, stepSize: 1, unit: ""}])
        selectionParams: ([{name: "Detect Shadows", options: ["Yes", "No"]}])

        pathInfo: ({path: manifest.movement, is_valid: manifest.is_valid_file(manifest.movement), is_dir: false})

        onUserPathChanged: (newPath) => {
            manifest.movement = newPath;
        }

        onParamChanged: (name, value) => {
            if (name === "Downsampling Factor") {
                videoTab.downsamplingFactor = Math.min(1. / value, 1);
                print(videoTab.downsamplingFactor);
            }
            else if (name === "Detect Shadows") {
                videoTab.detectShadows = value === "Yes";
                print(videoTab.detectShadows);
            }
        }
    }

    ProcessRunner {
        id: heatmapGazeRunner
        Layout.fillWidth: true
        title: "Gaze Heatmaps Overlays"
        description: "Generate gaze heatmaps used as an overlay on the workspace video."
        requirements: ([
            {name: "Workspace Video", 'satisfies': workspaceVideoExists},
            {name: "Areas of interests", 'satisfies': aoiExists}
        ])
        enabled: !preprocessingPipeline.pipeline_running && workspaceVideoExists && aoiExists

        onRunTriggered: {
            statusHeatmapGaze = true;
            preprocessingPipeline.run_video_heatmap_gaze(videoTab.stepSizeGaze, videoTab.kernelSizeGaze);
        }

        realParams: ([
            {name: "Step Size", from: 1, to: 180, stepSize: 1, unit: "sec."},
            {name: "Kernel Size", from: 51, to: 201, stepSize: 2, unit: ""},
        ])

        onUserPathChanged: (newPath) => {
            manifest.heatmaps_attention = newPath;
        }

        pathInfo: ({path: manifest.heatmaps_attention, is_valid: manifest.is_valid_dir(manifest.heatmaps_attention, '.npy'), is_dir: true})

        onParamChanged: (name, value) => {
            if (name === "Step Size") {
                videoTab.stepSizeGaze = value;
            }
            else if (name === "Kernel Size") {
                videoTab.kernelSizeGaze = Math.floor(value);
            }
        }
    }

    ProcessRunner {
        id: heatmapMoveRunner
        Layout.fillWidth: true
        title: "Movement Heatmaps Overlays"
        description: "Generate movement heatmaps used as an overlay on the workspace video."
        enabled: !preprocessingPipeline.pipeline_running && workspaceVideoExists && aoiExists
        requirements: ([
            {name: "Workspace Video", 'satisfies': workspaceVideoExists},
            {name: "Areas of interests", 'satisfies': aoiExists}
        ])
        onRunTriggered: {
            statusHeatmapMove = true;
            preprocessingPipeline.run_video_heatmap_move(videoTab.stepSizeMove, videoTab.kernelSizeMove);
        }
        realParams: ([
            {name: "Step Size", from: 1, to: 180, stepSize: 1, unit: "sec."},
            {name: "Kernel Size", from: 51, to: 201, stepSize: 2, unit: ""},
        ])
        pathInfo: ({path: manifest.heatmaps_movement, is_valid: manifest.is_valid_dir(manifest.heatmaps_movement, '.npy'), is_dir: true})

        onUserPathChanged: (newPath) => {
            manifest.heatmaps_movement = newPath;
        }

        onParamChanged: (name, value) => {
            if (name === "Step Size") {
                videoTab.stepSizeMove = value;
            }
            else if (name === "Kernel Size") {
                videoTab.kernelSizeMove = Math.floor(value);
            }
        }
    }

    /*
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
    */
}