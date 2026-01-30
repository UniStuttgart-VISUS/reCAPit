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
    id: notesTab

    property alias notesIndicator: notesRunningIndicator
    property string currStdOut: ""

    GroupBox {
        Layout.fillWidth: true

        title: "Notes Processing"

        GridLayout {
            anchors.fill: parent
            columns: 3
            rowSpacing: 15
            columnSpacing: 15

            Text {
                text: "Register Notes"
                font.bold: true
            }

            ProgressBar {
                Layout.fillWidth: true
                id: notesRunningIndicator
                indeterminate: false
                value: 1.0
            }

            Button {
                Layout.preferredHeight: 25
                text: "Run"
                enabled: !preprocessingPipeline.pipeline_running
                onClicked: {
                    notesRunningIndicator.indeterminate = true;
                    notesTab.currStdOut = "";
                    preprocessingPipeline.run_notes()
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
                notesTab.currStdOut += "\n" + line;
            }
        }

        ScrollView {
            anchors.fill: parent
            anchors.margins: 10
            Text {
                width: parent.width
                color: "#666"
                text: notesTab.currStdOut;
                wrapMode: Text.WordWrap
            }
        }
    }
}