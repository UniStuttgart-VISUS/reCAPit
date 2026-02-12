import QtQuick 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml
import QtQuick.Controls.Basic

import "../js/colorschemes.js" as Utils

ListView {
    id: repB
    spacing: 0

    property real boxW: 35 
    property real boxH: 20 

    signal navigateTo(int index)

    clip: true
    
    delegate: Rectangle {
        id: rect

        required property int index
        required property bool marked

        width: repB.boxW
        height: repB.boxH
        //color: (index < repB.segmentIndicesScores.length) ? Utils.interpolateColor(repB.segmentIndicesScores[index], "PuBuGn") : "#f8f8f8"
        border.color: '#d9d9d9'

        MouseArea {
            anchors.fill: parent
            onClicked: {
                //scroll.ScrollBar.horizontal.position = tsRoot.children[index].x / tsRoot.width;
                repB.navigateTo(rect.index);
            }
        }

        Label {
            anchors.fill: parent
            font.pixelSize: 16

            text: rect.marked ? "⭐" : ""
            opacity: 0.5

            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }
}