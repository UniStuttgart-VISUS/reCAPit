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
    id: appwin
    visible: true
    width: 800
    height: 1000
    color: "white"
    title: ""

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
                text: manifest.was_modified ? qsTr("Manifest (modified)") : qsTr("Manifest") 
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

            AudioTab {
                id: audioTab
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            VideoTab {
                id: videoTab
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            GazeTab {
                id: gazeTab
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            NotesTab {
                id: notesTab
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            SegmentsTab {
                id: segmentsTab
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }
}
