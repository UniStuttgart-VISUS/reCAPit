import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

TabButton {
    id: control

    /*
    contentItem: Text {
        text: control.text
        //font: control.font
        font.weight: Font.Bold
        color: control.enabled ? "white" : "#888"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    */
    //width: 2*implicitWidth
    contentItem: Column {
        spacing: 8
        Text {
            id: contentText
            width: control.width
            text: control.text
            font.weight: Font.Bold
            color: (control.checked || control.down) ? "white" : "#888"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        Rectangle {
            visible: control.checked
            anchors.horizontalCenter: contentText.horizontalCenter
            width: parent.width * 0.5 //contentText.implicitWidth
            height: 3
            color: "#9BEC00"
            radius: 5
        }
    }
    background: Rectangle {
        color: "#222"
        border.width: 0
        visible: false
    }
}