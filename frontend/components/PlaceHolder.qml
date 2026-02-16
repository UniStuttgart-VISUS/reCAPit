
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "../js/utils.js" as Utils
import "."

Rectangle {
    id: root
    color: "#eee"

    Column {
        spacing: 15

        width: parent.width
        anchors.centerIn: parent

        Repeater {
            id: rects
            model: 3

            delegate: Rectangle {

                width: parent.width * 0.3
                height: parent.width * 0.3
                radius: parent.width * 0.3
                color: "#aaa"

                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }
}