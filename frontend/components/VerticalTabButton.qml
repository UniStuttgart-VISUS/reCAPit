import QtQuick 2.15
import QtQuick.Controls.Basic
import QtQuick.Layouts 2.15

TabButton {
    id: control
    width: 150
    height: 40

    contentItem: Text {
        text: control.text
        font.pixelSize: control.font.pixelSize
        font.bold: control.checked
        color: "#222"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 100
        implicitHeight: 40
        color: control.checked ? "#B0C4DE" : "#f8f8f8"
        radius: 0
    }
}