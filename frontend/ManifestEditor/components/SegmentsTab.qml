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

    property alias segmentInitialIndicator: segmentInitialRunningIndicator
    property alias segmentRefineIndicator: segmentRefineRunningIndicator
    property string currStdOut: ""

    GroupBox {
        Layout.fillWidth: true

        title: "Segmentation"

        GridLayout {
            anchors.fill: parent
            columns: 3
            rowSpacing: 15
            columnSpacing: 15

            Text {
                text: "Initial Segmentation"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: segmentInitialRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    segmentInitialRunningIndicator.indeterminate = true;
                    segmentsTab.currStdOut = "";
                    preprocessingPipeline.run_segment_initial()
                }
            }

            Text {
                text: "Refine Segmentation"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: segmentRefineRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    segmentRefineRunningIndicator.indeterminate = true;
                    segmentsTab.currStdOut = "";
                    preprocessingPipeline.run_segment_refine()
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
                segmentsTab.currStdOut += "\n" + line;
            }
        }

        ScrollView {
            anchors.fill: parent
            anchors.margins: 10
            Text {
                width: parent.width
                color: "#666"
                text: segmentsTab.currStdOut;
                wrapMode: Text.WordWrap
            }
        }
    }
}