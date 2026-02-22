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

import "components"

ApplicationWindow {
    id: appWindow
    visible: true
    width: 800
    height: 1000
    color: "white"
    title: ""

    // Terminal window for process output
    property var terminalWindow: null

    function openTerminalWindow() {
        if (terminalWindow === null || !terminalWindow.visible) {
            var component = Qt.createComponent("components/TerminalWindow.qml");
            if (component.status === Component.Ready) {
                terminalWindow = component.createObject(appWindow);
                terminalWindow.clear();
            }
        } else {
            terminalWindow.clear();
            terminalWindow.raise();
        }
    }

    Connections {
        target: preprocessingPipeline
        function onRunningStatusChanged() {
            if (preprocessingPipeline.pipeline_running) {
                appWindow.openTerminalWindow();
            }
        }
    }

    footer: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton {
                text: qsTr("👁 Show console")
                onClicked: {
                    appWindow.openTerminalWindow();
                }
            }
            Label {
                text: preprocessingPipeline.current_process_info.args
                elide: Label.ElideRight
                horizontalAlignment: Qt.AlignHCenter
                verticalAlignment: Qt.AlignVCenter
                Layout.fillWidth: true
            }
            ToolButton {
                text: qsTr("❌ Kill current process")
                enabled: preprocessingPipeline.pipeline_running
                onClicked: {
                    preprocessingPipeline.terminate_current_process();
                }
            }
        }

        background: Rectangle {
            implicitHeight: 30
            color: "#f8f8f8"
            Rectangle {
                width: parent.width
                height: 1
                anchors.top: parent.top
                color: "transparent"
                border.color: "indigo"
            }
        }
    }

    component CustomTabButton: TabButton {
        id: tabBtn

        contentItem: Column {
            spacing: 10

            Text {
                font.pixelSize: 16
                font.letterSpacing: 0.5

                color: tabBtn.checked ? "#000" : "#888"

                text: tabBtn.text
                width: implicitWidth
                height: implicitHeight
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }

            Rectangle {
                id: rect

                width: parent.width
                height: 3
                radius: 2
                //color: tabBtn.checked ? "red" : "transparent"

                states: State {
                    name: "active"; when: tabBtn.checked
                    PropertyChanges { target: rect; color: "red" }
                }
                transitions: Transition {
                    ColorAnimation {from: "red"; duration: 200}
                }
            }
        }

        background: Rectangle {
            color: "transparent"
        }
    }

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: bar
            Layout.fillWidth: true
            Layout.margins: 10
            background: Rectangle {
                color: "transparent"
            }

            CustomTabButton {
                text: qsTr("Manifest") 
                width: implicitWidth
            }
            CustomTabButton {
                text: qsTr("Audio")
                width: implicitWidth
            }
            CustomTabButton {
                text: qsTr("Video")
                width: implicitWidth
            }
            CustomTabButton {
                text: qsTr("Gaze")
                width: implicitWidth
            }
            CustomTabButton {
                text: qsTr("Notes")
                width: implicitWidth
            }
            CustomTabButton {
                text: qsTr("Segments")
                width: implicitWidth
            }

        }

        StackLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 25
            Layout.rightMargin: 25

            currentIndex: bar.currentIndex

            GeneralTab {
                id: generalTab
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            ScriptsTab {
                id: audioTab
                Layout.fillWidth: true
                Layout.fillHeight: true
                targetScriptDir: "transcript"
            }

            ScriptsTab {
                id: videoTab
                Layout.fillWidth: true
                Layout.fillHeight: true
                targetScriptDir: "video/workspace"
            }

            ScriptsTab {
                id: gazeTab
                Layout.fillWidth: true
                Layout.fillHeight: true
                targetScriptDir: "gaze"
            }

            ScriptsTab {
                id: notesTab
                Layout.fillWidth: true
                Layout.fillHeight: true
                targetScriptDir: "notes"
            }

            ScriptsTab {
                id: segmentationTab
                Layout.fillWidth: true
                Layout.fillHeight: true
                targetScriptDir: "segmentation"
            }
        }
    }
}
