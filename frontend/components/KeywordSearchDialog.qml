import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

Dialog {
    id: keywordDialog
    property var userKeywords: []

    title: "Keyword Search"
    standardButtons: Dialog.Ok | Dialog.Cancel

    signal keywordSearch(list<string> keywords)

    /*
    background: Rectangle {
        color: "#f0f0f0"
    }
    */

    ColumnLayout {
        anchors.fill: parent

        Label {
            text: "Keyword Terms:"
            font.pixelSize: 20
            Layout.fillWidth: true
            Layout.preferredHeight: 50
        }

        Label {
            font.pixelSize: 18
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: "No keyword terms defined"
            color: "#aaa"
            horizontalAlignment: Text.AlignHCenter
            visible: keywordDialog.userKeywords.length === 0
        }

        Flow {
            id: keywordsContainer

            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15

            function removeKeyword(keyword) {
                keywordDialog.userKeywords = keywordDialog.userKeywords.filter(k => k !== keyword);
            }

            Repeater {
                anchors.fill: parent
                anchors.margins: 30

                model: keywordDialog.userKeywords
                Rectangle {
                    required property string modelData

                    width: tagText.implicitWidth + 15
                    height: 25
                    radius: 5
                    color: "#eee"
                    border.color: "#aaa"

                    Row {
                        id: tagText
                        spacing: 5

                        anchors.centerIn: parent
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5

                        Text {
                            text: modelData
                            elide: Text.ElideMiddle
                            color: "#555"
                            font.pixelSize: 12
                        }
                        Label {
                            text: "✕"
                            color: "#555"
                            font.pixelSize: 14
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    keywordsContainer.removeKeyword(modelData);
                                }
                            }
                        }
                    }
                }
            }
        }

        TextField {
            id: keywordInput

            Layout.preferredHeight: 50
            Layout.fillWidth: true

            placeholderText: "Enter keyword term here ..."

            background: Rectangle {
                radius: 5
                border.color: keywordInput.activeFocus ? "#e80" : "#C9C9C9"
                border.width: 2
            }
            Label {
                id: image
                text: "🔎"
                font.pixelSize: 18
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 5
            }

            leftPadding: image.implicitWidth + 15
            verticalAlignment: TextField.AlignVCenter

            font.pixelSize: 16
            font.weight: Font.Normal
            font.family: "Arial"

            onAccepted: {
                keywordDialog.userKeywords = [...keywordDialog.userKeywords, keywordInput.text.toLowerCase()];
                keywordInput.text = "";
            }
        }

    }

    onOpened: {
        keywordDialog.userKeywords = [];
        keywordInput.clear();
        keywordInput.focus = true;
    }

    onAccepted: {
        keywordSearch(keywordDialog.userKeywords);
    }

    modal: true
}