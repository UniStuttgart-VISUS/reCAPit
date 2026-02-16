import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml
import QtQuick.Controls.Basic

import "../js/utils.js" as Utils

ListView {
    id: repB
    spacing: 0

    property real boxW: 60 
    property real boxH: 25 
    required property bool highlightsActive

    signal navigateTo(int index)

    clip: true
    
    delegate: Rectangle {
        id: rect

        required property int index
        required property bool marked
        required property string displayState
        required property real startSec
        required property real endSec

        width: repB.boxW
        height: repB.boxH

        readonly property string stateColor: (displayState === "highlighted" && highlightsActive) ? Utils.interpolateColor(0.5, "PuBuGn") : "#f8f8f8"

        color: stateColor
        border.color: '#d9d9d9'

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true

            onClicked: {
                repB.navigateTo(rect.index);
            }
            onEntered: {
                rect.border.color = Utils.interpolateColor(0.75, "PuBuGn");
                rect.border.width = 3;
            }
            onExited: {
                rect.border.color = "#d9d9d9";
                rect.border.width = 1;
            }
        }

        Label {
            anchors.fill: parent
            font.pixelSize: 10

            text: (rect.marked ? "⭐" : " ") + Utils.timeFormat(startSec)

            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}