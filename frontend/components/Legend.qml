import QtQuick 2.15
import QtQuick.Effects
import QtQuick.Controls 2.15
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

RowLayout {
    id: legend

    required property var labels
    required property var cmap
    property alias title: legendTitle.text

    signal labelClicked(string label)

    Text {
        anchors.margins: 5

        Layout.preferredWidth: 50
        Layout.fillHeight: true

        verticalAlignment: Text.AlignVCenter
        id: legendTitle
        font.pixelSize: 16
        font.weight: Font.Bold
        color: "black"
    }

    Rectangle {
        Layout.preferredWidth: mar.implicitWidth + 50
        Layout.fillHeight: true

        color: "#eee"
        radius: 10

        RowLayout {
            id: mar
            anchors.fill: parent
            anchors.leftMargin: 25
            anchors.rightMargin: 25

            Repeater {
                id: rep
                model: legend.labels

                Row {
                    id: currLabel
                    property bool isActive: true

                    spacing: 10
                    Rectangle {
                        width: parent.height
                        height: parent.height
                        radius: parent.height
                        color: legend.cmap.get(modelData)
                        opacity: currLabel.isActive ? 1 : 0.5

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                currLabel.isActive = !currLabel.isActive
                                labelClicked(modelData)
                            }
                        }
                    }

                    Label {
                        id: label
                        text: modelData
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 12
                        font.capitalization: Font.AllLowercase
                        elide: Text.ElideMiddle
                        
                    }
                }
            }
        }
    }
}