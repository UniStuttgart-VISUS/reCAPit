import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "utils.js" as Utils
import "."

/*
Component {
    id: myRow
    Row {
        anchors.fill: parent
        spacing: 0
    }
}

Component {
    id: myImage
    required property var source: ""

    Image {
        id: img
        height: 150
        source: myImage.source
        fillMode: Image.PreserveAspectFit
    }
}

*/

Item {
    id: aoiRiver
    required property var stacksTop
    required property var stacksBottom
    required property var xScale
    required property real tickIntervalMajor
    required property real tickIntervalMinor
    required property var cmapTop
    required property var cmapBottom

    Column {
        anchors.fill: parent

        Streamgraph {
            id: streamAttention
            cmap: aoiRiver.cmapTop
            mtsModel: stacksTop
            width: parent.width
            height: (parent.height - 0) / 2
            flipped: false
            z: 10
        }

        /*
        TextField {
            placeholderText: ""
            width: parent.width
            height: 25
            horizontalAlignment: TextInput.AlignHCenter
            autoScroll: false
            wrapMode: TextInput.NoWrap

            font.pixelSize: 12

            color: "#888"
            z: 15

            background: Rectangle {
                width: parent.width
                height: parent.height
                color: "transparent"
                border.color: "transparent"
            }
        }
        Item {
            width: parent.width
            height: 50

            Rectangle {
                y: 25
                height: 2
                width: parent.width
                color: "#f0f0f0"
                z: 5
            }

            Repeater {
                model: indicatorPos.length
                delegate: Rectangle {
                    required property int index

                    width: 25
                    height: 25
                    z: 15

                    x: indicatorPos[index] * aoiRiver.width
                    y: 12

                    radius: 15
                    color: "#e0e0e0"

                    Text {
                        anchors.centerIn: parent
                        text: indicatorLabel[index]
                        color: "white"
                        font.weight: Font.Bold
                    }
                }
            }
        }
        */


        Streamgraph {
            id: streamActivity
            cmap: aoiRiver.cmapBottom
            mtsModel: stacksBottom
            //anchors.top: streamAttention.bottom
            width: parent.width
            height: (parent.height - 0) / 2
            flipped: true
            z: 10
        }
    }
}