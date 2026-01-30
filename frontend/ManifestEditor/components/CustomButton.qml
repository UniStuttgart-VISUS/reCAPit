import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Shapes 1.2
import QtQuick.Controls.Basic
import QtQml

Button {
    id: control

    contentItem: Text {
        text: control.text
        font: control.font
        opacity: enabled ? 1.0 : 0.3
        color: hovered ? "white" : "black"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        color: hovered ? "#0066cc" : "white"
        border.color: "#0066cc"
        border.width: 1.5
        radius: 25
    }
}