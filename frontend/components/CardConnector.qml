import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

Shape {
    id: connShape

    property bool highlighted : false

    width: toRightX - toLeftX
    height: fromY - toY

    x: toLeftX
    y: toY

    required property real toLeftX
    required property real toRightX
    required property real toY
    required property real fromX
    required property real fromY

    ShapePath {
        startX: 0; startY: 0
        strokeWidth: -1
        //fillColor: "#f8f8f8"
        fillColor: connShape.highlighted ? "#E6E4E9" : "#f4f4f4"

        PathCubic {
            x: fromX - toLeftX; y: fromY - toY
            control1X: 0
            control1Y: 0.75 * (fromY - toY)
            control2X: fromX - toLeftX
            control2Y: 0.25 * (fromY - toY)
        }

        PathCubic {
            x: toRightX - toLeftX; y: 0
            control1X: fromX - toLeftX
            control1Y: 0.25 * (fromY - toY) 
            control2X: toRightX - toLeftX
            control2Y: 0.75 * (fromY - toY)
        }
        PathLine { x: 0; y: 0 }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true

        onEntered: {
            connShape.highlighted = true;
        }

        onExited: {
            connShape.highlighted = false;
        }

    }
}