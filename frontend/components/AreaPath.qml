import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml


Shape {
    id: areaElement

    property string pathStr
    property string areaColor

    anchors.fill: parent

    asynchronous: true
    smooth: true

    ShapePath {
        fillColor: areaColor
        strokeColor: Qt.lighter(areaColor, 1.125)
        strokeWidth: 1

        /*
        fillGradient: LinearGradient {
            x1: parent.width / 2
            y1: 0

            x2: parent.width / 2
            y2: parent.height

            GradientStop { position: 0.0; color: Qt.darker(areaColor, 1.25) }
            GradientStop { position: 0.75; color: areaColor }
        }
        */
        startX: 0
        startY: 0

        PathSvg { 
            path: areaElement.pathStr;
        }
    }
}