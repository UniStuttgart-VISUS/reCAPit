
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.2
import "../js/utils.js" as Utils

Item {
    id: segments

    required property var title
    property var onCardVisibilityChanged
    property bool checked: true

    readonly property string baseColor: "#4f4f4f"

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton

        onClicked: (mouse) => {
            if (mouse.button === Qt.LeftButton) {
                segments.checked = !segments.checked;
                segments.onCardVisibilityChanged(segments.checked)
            }
        }
    }
    Rectangle {
        id: brect
        width: parent.width
        height: parent.height
        /*
        color: {
            if (segments.editing)
                return "#8a8576"
            return segments.checked ? "#373735" : "#676764"
        }
        */
        opacity: segments.checked ? 1.0 : 0.5

        gradient: Gradient {
            orientation: Gradient.Horizontal

            GradientStop { position: 0.0; color: Qt.lighter(segments.baseColor, 1.5) }
            GradientStop { position: 0.5; color: segments.baseColor }
            GradientStop { position: 1.0; color: Qt.lighter(segments.baseColor, 1.5) }
        }
    }
    Rectangle {
        id: brect2
        anchors.top: brect.bottom
        width: parent.width
        height: 3
        color: "#FFE000"
        visible: title !== ""
    }
    Text {
        width: parent.width
        height: parent.height

        wrapMode: Text.NoWrap
        elide: Text.ElideMiddle

        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter

        font.pointSize: 9
        font.weight: 700

        text: title
        color: "#eee"
    }
}