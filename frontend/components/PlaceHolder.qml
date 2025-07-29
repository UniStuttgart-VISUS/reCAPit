
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "../js/utils.js" as Utils
import "."

Rectangle {
    width: 30
    height: 400
    color: "#eee"

    Label {
        anchors.centerIn: parent
        font.pixelSize: 30
        font.weight: Font.Bold
        text: "..."
        color: "#888"
    }
}