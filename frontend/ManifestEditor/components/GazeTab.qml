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
    property bool attentionExists: manifest.is_valid_file(manifest.attention)
    property bool aoiExists: manifest.is_valid_file(manifest.aoi)
    property bool videoWorkspaceExists: manifest.is_valid_file(manifest.video_workspace)

    CustomGroupBox {
        Layout.fillWidth: true
        title: "◳ Marker Mapping"

        Repeater {
            model: manifest.recordings
            delegate: ProcessRunner {
                Connections {
                    target: preprocessingPipeline
                    function onGazeSurfaceMappingCompleted(returnCode) { 
                        surfaceMappingRunner.isRunning = false;
                    }
                }

                id: surfaceMappingRunner

                required property string recId
                required property string sourceGaze
                required property string surfaceFixPath

                property real minDetectedTags: 1
                property string aprilTagFamily: "tag36h11"

                property bool gazeDataExists: manifest.is_valid_dir(sourceGaze, "*")

                Layout.fillWidth: true

                title: "Recording %1".arg(recId)
                description: "Marker-based mapping of participants' fixations on the workspace area."
                requirements: ([{name: "Gaze Data", 'exists': gazeDataExists}, {name: "Workspace Video", exists: gazeTab.videoWorkspaceExists}])
                enabled: !preprocessingPipeline.pipeline_running && gazeDataExists
                onRunTriggered: {
                    surfaceMappingRunner.isRunning = true;
                    preprocessingPipeline.run_gaze_surf_mapping(recId, minDetectedTags, aprilTagFamily);
                }
                realParams: ([{name: "Minimum Detected Tags", from: 1, to: 64, stepSize: 1, unit: ""}])
                selectionParams: ([{name: "AprilTag Family", options: ["tag36h11"]}])

                pathInfo: ({path: surfaceFixPath, is_valid: manifest.is_valid_file(surfaceFixPath), is_dir: false})

                onUserPathChanged: (newPath) => {}

                onParamChanged: (name, value) => {
                    if (name === "Minimum Detected Tags") {
                        minDetectedTags = value;
                    }
                    else if (name === "AprilTag Family") {
                        aprilTagFamily = value;
                    }
                }
            }
        }
    }

    CustomGroupBox {
        Layout.fillWidth: true
        title: "◳ AOI Mapping"

        Repeater {
            model: manifest.recordings
            delegate: ProcessRunner {
                id: aoiMappingRunner

                Connections {
                    target: preprocessingPipeline
                    function onGazeAOIMappingCompleted(returnCode) { 
                        aoiMappingRunner.isRunning = false;
                    }
                }

                required property string recId
                required property string mappedFixPath
                required property string surfaceFixPath

                property bool surfaceFixExists: manifest.is_valid_file(surfaceFixPath)
                property bool mappedFixExists: manifest.is_valid_file(mappedFixPath)

                Layout.fillWidth: true

                title: "Recording %1".arg(recId)
                description: "Map the surface fixations (in workspace video) to the areas-of-interests"
                requirements: ([{name: "Areas-of-interests", exists: aoiExists}, {name: "Surface Fixations", exists: surfaceFixExists}])
                enabled: !preprocessingPipeline.pipeline_running && aoiExists && surfaceFixExists
                onRunTriggered: {
                    aoiMappingRunner.isRunning = true;
                    preprocessingPipeline.run_gaze_aoi_mapping(recId)
                }

                pathInfo: ({path: mappedFixPath, is_valid: mappedFixExists, is_dir: false})
                onUserPathChanged: (newPath) => {}
            }
        }
    }
    ProcessRunner {
        id: attentionRunner
        property real windowSizeSec: 0.5

        Connections {
            target: preprocessingPipeline
            function onGazeAttentionCompleted(returnCode) { 
                attentionRunner.isRunning = false;
            }
        }
        Layout.fillWidth: true

        title: "Temporal AOI Distribution (Time Series)"
        description: "Map the surface fixations (on workspace) on the areas-of-interests"
        requirements: ([{name: "Areas-of-interests", exists: aoiExists}, {name: "Surface Fixations", exists: false}])
        enabled: !preprocessingPipeline.pipeline_running && aoiExists
        onRunTriggered: {
            attentionRunner.isRunning = true;
            preprocessingPipeline.run_attention(windowSizeSec);
        }

        realParams: ([{name: "Window Size", from: 0.1, to: 5, stepSize: 0.1, unit: "sec."}])
        onParamChanged: (name, value) => {
            if (name === "Window Size") {
                windowSizeSec = value;
            }
        }
    }
}