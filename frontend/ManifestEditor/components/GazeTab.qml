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
    id: gazeTab
    property real windowSizeSec: 0.5
    property real minDetectedTags: 1
    property string aprilTagFamily: "tag36h11"
    property string currStdOut: ""

    property alias statusAttention: attentionRunner.isRunning
    property bool attentionExists: manifest.is_valid_file(manifest.attention)
    property bool aoiExists: manifest.is_valid_file(manifest.aoi)

    Connections {
        target: preprocessingPipeline
        function onGazeAttentionCompleted(returnCode) { 
            gazeTab.statusAttention = false;
        }
        function onStdOutLine(line) { 
            gazeTab.currStdOut += "\n" + line;
        }
    }

    GroupBox {
        Layout.fillWidth: true

        label: Label {
            width: parent.availableWidth
            text: "◳ Marker Mapping"
            color: "#000"
            font.pixelSize: 18
        }

        ColumnLayout {
            anchors.fill: parent

            Repeater {
                model: manifest.recordings
                delegate: ProcessRunner {
                    Connections {
                        target: preprocessingPipeline
                        function onGazeSurfaceMappingCompleted(returnCode) { 
                            surfaceMappingRunner.isRunning = false;
                        }
                    }

                    required property string recId
                    required property string role
                    required property string sourceGaze
                    required property real sourceGazeOffset
                    required property string sourceGazeHardware
                    required property string surfaceFixPath
                    required property string mappedFixPath
                    required property int index
                    required property var model

                    property bool gazeDataExists: manifest.is_valid_dir(sourceGaze, "*")

                    Layout.fillWidth: true
                    id: surfaceMappingRunner
                    title: "Recording %1".arg(recId)
                    description: "Marker-based mapping of participants' fixations on the workspace area."
                    requirements: ([{name: "Gaze Data", 'satisfies': gazeDataExists}])
                    enabled: !preprocessingPipeline.pipeline_running && gazeDataExists
                    onRunTriggered: {
                        surfaceMappingRunner.isRunning = true;
                        preprocessingPipeline.run_gaze_surf_mapping(recId, gazeTab.minDetectedTags, gazeTab.aprilTagFamily);
                    }
                    realParams: ([{name: "Minimum Detected Tags", from: 1, to: 64, stepSize: 1, unit: ""}])
                    selectionParams: ([{name: "AprilTag Family", options: ["tag36h11"]}])

                    pathInfo: ({path: surfaceFixPath, is_valid: manifest.is_valid_file(surfaceFixPath), is_dir: false})

                    onUserPathChanged: (newPath) => {}

                    onParamChanged: (name, value) => {
                        if (name === "Minimum Detected Tags") {
                            gazeTab.minDetectedTags = value;
                        }
                        else if (name === "AprilTag Family") {
                            gazeTab.aprilTagFamily = value;
                        }
                    }
                }
            }
        }
    }

    ProcessRunner {
        id: attentionRunner
        Layout.fillWidth: true
        title: "AOI-Mapping"
        description: "Map the surface fixations (on workspace) on the areas-of-interests"
        requirements: ([{name: "Areas-of-interests", 'satisfies': aoiExists}])
        enabled: !preprocessingPipeline.pipeline_running && aoiExists
        onRunTriggered: {
            statusAttention = true;
            preprocessingPipeline.run_attention(gazeTab.windowSizeSec)
        }
        realParams: ([{name: "Window Size", from: 0.1, to: 5, stepSize: 0.1, unit: "sec."}])

        pathInfo: ({path: manifest.attention, is_valid: attentionExists, is_dir: false})

        onUserPathChanged: (newPath) => {
            manifest.attention = newPath;
        }

        onParamChanged: (name, value) => {
            if (name === "Window Size") {
                gazeTab.windowSizeSec = value;
            }
        }
    }
}