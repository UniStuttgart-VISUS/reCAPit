import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "utils.js" as Utils
import "."

// Timeline axis

Item {
    id: ta

    required property bool showLabels

    required property real fromTimestamp
    required property real toTimestamp

    required property real tickIntervalMajor
    required property real tickIntervalMinor

    Shape {
        anchors.fill: parent

        ShapePath {
            strokeWidth: 1
            strokeColor: "#000"
            strokeStyle: ShapePath.SolidLine
            startX: 0; startY: 0
            PathLine { x: ta.width; y: 0}
        }


        // Major Ticks
        Repeater {
            model: Math.floor(ta.width / tickIntervalMajor)
            delegate: Shape {
                required property int modelData
                ShapePath {
                    strokeWidth: 1
                    strokeColor: "#000"
                    strokeStyle: ShapePath.SolidLine
                    startX: modelData*tickIntervalMajor; startY: 0
                    PathLine { x: modelData*tickIntervalMajor; y: 20}
                }
            }
        }
        Repeater {
            model: Math.floor(ta.width / tickIntervalMinor)
            delegate: Shape {
                required property int modelData
                ShapePath {
                    strokeWidth: 1
                    strokeColor: "#000"
                    strokeStyle: ShapePath.SolidLine
                    startX: modelData*tickIntervalMinor; startY: 0
                    PathLine { x: modelData*tickIntervalMinor; y: (modelData % 2 == 0 ? 15 : 10)}
                }
            }
        }

        // Major Tick Labels
        Repeater {
            model: Math.floor(ta.width / tickIntervalMajor)
            delegate: Text {
                visible: ta.showLabels
                required property int modelData
                x: modelData * tickIntervalMajor + 10
                y: 15
                text: Utils.timeFormat(ta.fromTimestamp + (ta.toTimestamp - ta.fromTimestamp) * tickIntervalMajor * modelData / ta.width)
                font.family: "Arial"
                font.pointSize: 10
                color: "black"
            }
        }
    }
}