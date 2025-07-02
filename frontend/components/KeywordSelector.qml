import QtQuick 2.15
import QtQuick.Effects
import QtQuick.Controls 2.15
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

ListView {
    id: listView
    clip: true

    header: RowLayout {
        spacing: 10
        Text { text: "Included"; Layout.fillWidth: true }
        Text { text: "Keyword"; Layout.fillWidth: true }
        Text { text: "# of occurrences"; Layout.fillWidth: true }
    }

    delegate: Item {
        width: listView.width
        height: 50
        property bool alternateRow: index % 2 === 0

        Rectangle {
            width: parent.width
            height: parent.height
            //color: alternateRow ? "#FFF" : "#CCC"

            RowLayout {
                anchors.fill: parent
                CheckBox {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.fillWidth: true

                    checked: model.checked
                    onClicked: model.checked = checked
                }
                Text {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.fillWidth: true

                    text: model.keyword
                    wrapMode: Text.WrapAnywhere
                    horizontalAlignment: Text.AlignLeft
                }
                Text {
                    Layout.alignment: Qt.AlignVCenter
                    Layout.fillWidth: true

                    text: model.occurrences
                    wrapMode: Text.WrapAnywhere
                    horizontalAlignment: Text.AlignLeft
                }
            }
        }
    }
}