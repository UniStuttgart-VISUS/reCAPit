import QtQuick 2.15
import QtQuick.Effects
import QtQuick.Controls 2.15
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "."
import "utils.js" as Utils

Rectangle {
    id: root

    required property var title
    required property var dia
    required property var tan
    required property var sac
    required property var sat
    required property var cmapAOI
    required property var cmapRole
    required property var meta
    required property int topicIndex
    required property bool hasCard
    required property int min_ts
    required property int max_ts

    property int cardIndex : -1
    property bool editing: false

    border.color: "#ffad33"
    border.width: editing ? 3 : 0

    height: 90 + 175 + Object.keys(dia).length * (appwin.timelineHeight + appwin.timelineVSpace)
    clip: false

    signal cardVisibilityChanged(int topicIndex, bool visible)
    signal noteRequested(real timestamp, int topicIndex)
    signal collapseRequested(int topicIndex)
    signal mergeWithLeft(int topicIndex)
    signal mergeWithRight(int topicIndex)

    function xScaleG(ts) {
        return (ts - min_ts) * root.width / (max_ts - min_ts);
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: (mouse) => {
            if (mouse.button === Qt.RightButton) {
                contextMenu.popup()
                root.editing = !root.editing;
            }
        }
    }

    Menu {
        id: contextMenu
        anchors.centerIn: parent

        onAboutToHide: {
            root.editing = false;
        }

        MenuItem { 
            text: "Merge with " + String.fromCodePoint(0x21E4) + " (left)" 
            onTriggered: mergeWithLeft(root.topicIndex)
        }
        MenuItem { 
            text: "Merge with " + String.fromCodePoint(0x21E5) + " (right)" 
            onTriggered: mergeWithRight(root.topicIndex)
        }
        MenuItem { 
            text: "Export" 
            onTriggered: {
                root.grabToImage(function(result) {
                    result.saveToFile("something.png")
                })
            }
        }
    }


    ColumnLayout {
        id: segRoot
        z: 5
        anchors.fill: parent
        spacing: 0

        AOIRiver {
            id: aoiRiver
            Layout.fillWidth: true
            height: 175

            cmap: root.cmapAOI
            tickIntervalMajor: xScaleG(60) - xScaleG(0)
            tickIntervalMinor: xScaleG(10) - xScaleG(0)
            stacksActivity: sac
            stacksAttention: sat
            xScale: xScaleG
        }

        TopicBar {
            id: topicBar
            Layout.fillWidth: true
            height: 30
            z: 20
            title: root.title
            checked: root.hasCard
            onCardVisibilityChanged: (visible) => {
                root.hasCard = visible;
                root.cardVisibilityChanged(root.topicIndex, visible);
            }
        }

        TimelineAxis {
            id: axis1
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            z: 10

            //color: root.timelineBackgroundColor
            fromTimestamp: min_ts
            toTimestamp: max_ts
            tickIntervalMajor: xScaleG(60) - xScaleG(0)
            tickIntervalMinor: xScaleG(10) - xScaleG(0)
            showLabels: true
        }


        // Timeline
        /*
        Rectangle {
            id: timelineContainer
            z: 2
            Layout.fillWidth: true
            height: dia.SpeechLineCount() * (appwin.timelineHeight + appwin.timelineVSpace)
            color: root.timelineBackgroundColor
        }
        */

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: Object.keys(dia).length * (appwin.timelineHeight + appwin.timelineVSpace)
            clip: true

            SwipeView {
                id: view
                currentIndex: 0
                orientation: Qt.Vertical

                anchors.fill: parent

                Repeater {
                    id: repDataTypes

                    model: Object.values(dia)[0].AvailableDataTypes()
                    property var recIds: Object.keys(dia)

                    delegate: ListView {
                        property var currDatatype: modelData

                        model: repDataTypes.recIds
                        spacing: appwin.timelineVSpace
                        interactive: false

                        delegate: Timeline {
                            required property int index

                            width: root.width
                            height: appwin.timelineHeight

                            cmap: root.meta.GetColormap(currDatatype)
                            modelData: dia[repDataTypes.recIds[index]].SubjectData(currDatatype)
                            xScale: xScaleG
                        }
                    }
                }

                /*
                ListView {
                    model: dia.SpeechLineCount()
                    spacing: appwin.timelineVSpace
                    interactive: false

                    delegate: Timeline {
                        required property int index

                        width: root.width
                        height: appwin.timelineHeight

                        cmap: root.cmapRole
                        modelData: dia.SpeechLine(index)
                        xScale: xScaleG
                    }
                }

                ListView {
                    model: dia.SpeechLineCount()
                    spacing: appwin.timelineVSpace
                    interactive: false

                    delegate: Timeline {
                        required property int index

                        width: root.width
                        height: appwin.timelineHeight

                        cmap: root.cmapAOI
                        modelData: dia.AoiLine(index)
                        xScale: xScaleG
                    }
                }
                */
            }

            PageIndicator {
                id: indicator

                count: view.count
                currentIndex: view.currentIndex

                anchors.bottom: view.bottom
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }

        TimelineAxisN {
            id: axis2
            z: 10
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            xScale: xScaleG
            modelData2: tan
            //color: root.timelineBackgroundColor

            fromTimestamp: Object.values(dia)[0].MinTimestamp()
            toTimestamp: Object.values(dia)[0].MaxTimestamp()
            tickIntervalMajor: xScaleG(60) - xScaleG(0)
            tickIntervalMinor: xScaleG(10) - xScaleG(0)
            showLabels: false

            Image {
                id: lineCursor
                source: "icons/add.png"
                z: 1000
                width: 35
                height: 35
                visible: false
                y: parent.height-20
            }
        }
    }
}