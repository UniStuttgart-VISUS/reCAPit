import QtQuick 2.15
import QtQuick.Effects
import QtQuick.Controls 2.15
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "."
import "../js/utils.js" as Utils

Item {
    id: buttonContainer
    required property var onClicked
    required property string text
    required property string source
    required property string color

    MultiEffect {
        source: buildButton
        anchors.fill: buildButton
        shadowEnabled: true
        shadowColor: "black"
        shadowOpacity: 0.5
        shadowScale: 1.0
        autoPaddingEnabled: true
    }

    RoundButton {
        id: buildButton

        anchors.margins: 10
        anchors.fill: parent

        text: buttonContainer.text

        contentItem: Text {
            text: parent.text
            font.pixelSize: 20
            font.weight: Font.Bold
            color: "white"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        background: Rectangle {
            radius: parent.radius
            border.width: -1
            border.color: "black"
            color: buttonContainer.color

            Image {
                anchors.centerIn: parent
                source: buttonContainer.source
                width: parent.radius * 0.9
                height: parent.radius * 0.9
            }
        }
        onClicked: {
            buttonContainer.onClicked();
        }
    }
}