import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Shapes 1.2
import QtQuick.Controls.Basic
import QtQml

RowLayout {
    property var dialog
    property alias name: nameText.text
    property alias path: pathText.text
    property alias valid: indicator.success

    spacing: 10

    Rectangle {
        id: indicator
        property bool success: false

        width: 10
        height: 10
        radius: 10
        color: success ? "#0f0" : "#f00"
    }

    Text { 
        id: nameText
        font.bold: true
    }

    Text {
        id: pathText
        Layout.fillWidth: true
        text: manifest.aoi
        horizontalAlignment: Text.AlignHCenter
        clip: true
    }
    Button {
        text: "..."
        onClicked: dialog.open()
        Layout.preferredWidth: 30
        Layout.preferredHeight: 30

        background: Rectangle {
            color: "white"
            radius: 2
        }
    }
}
