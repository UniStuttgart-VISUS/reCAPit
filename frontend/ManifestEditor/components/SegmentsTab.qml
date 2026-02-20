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
    id: segmentsTab

    property real downsamplingFactor: 1
    property real minSegmentDuration: 0.5
    property int penalization: 1

    property real similarityThreshold: 0.1
    property real minSegmentDuration2: 0.5
    property real gapThreshold: 0.5
    property string openaiModel: "gpt-5-mini"
    property string targetSignal: ""

    property alias statusInitial: initialSegmentation.isRunning
    property alias statusRefined: refinedSegmentation.isRunning
    property alias statusAttributes: segmentAttributes.isRunning

    property bool initialExists: manifest.is_valid_file(manifest.segments_initial)
    property bool refinedExists: manifest.is_valid_file(manifest.segments_refined)

    Connections {
        target: preprocessingPipeline
        function onSegmentInitialCompleted(returnCode) { 
            segmentsTab.statusInitial = false;
        }
        function onSegmentRefineCompleted(returnCode) { 
            segmentsTab.statusRefined = false;
        }
        function onSegmentAttributesCompleted(returnCode) { 
            segmentsTab.statusAttributes = false;
        }
    }

    ProcessRunner {
        id: initialSegmentation
        Layout.fillWidth: true
        title: "Initial Segmentation"
        description: "Generate a transcript using OpenAI's Whisper speech-to-text model."
        requirements: ([{name: "Any time series", 'exists': manifest.multi_time_signals.length > 0}])
        enabled: !preprocessingPipeline.pipeline_running && manifest.multi_time_signals.length > 0
        onRunTriggered: {
            statusInitial = true;
            preprocessingPipeline.run_segment_initial(segmentsTab.targetSignal, 
                                                      segmentsTab.penalization,
                                                      segmentsTab.downsamplingFactor,
                                                      segmentsTab.minSegmentDuration)
        }
        realParams: ([
            {name: "Signal Downsampling Factor", from: 1, to: 16, stepSize: 1, unit: ""},
            {name: "Minimum Segment Duration", from: 1, to: 120, stepSize: 1, unit: "sec."},
            {name: "Penalization", from: 0, to: 50, stepSize: 1, unit: ""},
        ])
        selectionParams: ([{name: "Available time series", options: manifest.multi_time_signals}])

        pathInfo: ({path: manifest.segments_initial, is_valid: initialExists, is_dir: false, file_extensions: ["CSV files (*.csv)"]})

        onUserPathChanged: (newPath) => {
            manifest.segments_initial = newPath;
        }

        onParamChanged: (name, value) => {
            if (name === "Signal Downsampling Factor") {
                segmentsTab.downsamplingFactor = value;
            }
            if (name === "Penalization") {
                segmentsTab.penalization = value;
            }
            else if (name === "Minimum Segment Duration") {
                segmentsTab.minSegmentDuration = value;
            }
            else if (name === "Available time series") {
                segmentsTab.targetSignal = value;
            }
        }
    }

    ProcessRunner {
        id: refinedSegmentation
        Layout.fillWidth: true
        title: "Refined Segmentation"
        description: "Refine previously generated segmentation using speech similarity"
        requirements: ([{name: "initial segments", 'exists': initialExists}])
        enabled: !preprocessingPipeline.pipeline_running && initialExists
        onRunTriggered: {
            statusRefined = true;
            preprocessingPipeline.run_segment_refine(segmentsTab.similarityThreshold, 
                                                     segmentsTab.gapThreshold,
                                                     segmentsTab.minSegmentDuration2)
        }
        realParams: ([
            {name: "Similarity Threshold", from: 0, to: 1, stepSize: 0.1, unit: ""},
            {name: "Gap Threshold", from: 0, to: 1, stepSize: 0.1, unit: ""},
            {name: "Minimum Segment Duration", from: 1, to: 120, stepSize: 1, unit: "sec."},
        ])

        pathInfo: ({path: manifest.segments_refined, is_valid: refinedExists, is_dir: false, file_extensions: ["CSV files (*.csv)"]})

        onUserPathChanged: (newPath) => {
            manifest.segments_refined = newPath;
        }

        onParamChanged: (name, value) => {
            if (name === "Similarity Threshold") {
                segmentsTab.similarityThreshold = value;
            }
            else if (name === "Gap Threshold") {
                segmentsTab.gapThreshold = value;
            }
            else if (name === "Minimum Segment Duration") {
                segmentsTab.minSegmentDuration2 = value;
            }
        }
    }

    ProcessRunner {
        id: segmentAttributes
        Layout.fillWidth: true
        title: "Segmentation Attributes"
        description: "Creates LLM-based summaries and titles for each topic segment"
        requirements: ([{name: "refined segments", 'exists': refinedExists}])
        enabled: !preprocessingPipeline.pipeline_running && (initialExists || refinedExists)
        onRunTriggered: {
            statusAttributes = true;
            preprocessingPipeline.run_segment_attributes("initial", segmentsTab.openaiModel, "")
        }

        selectionParams: ([{name: "OpenAI model", options: ["gpt-5-mini", "gpt-5", "gpt-5.2", "gpt-5-nano"]}])

        pathInfo: ({path: manifest.segments_refined, is_valid: refinedExists, is_dir: false, file_extensions: ["CSV files (*.csv)"]})

        onParamChanged: (name, value) => {
            if (name === "OpenAI model") {
                segmentsTab.openaiModel = value;
            }
        }
    }
}