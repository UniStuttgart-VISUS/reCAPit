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

    background: Rectangle {
        color: "#f0f0f0"
    }

    ColumnLayout {
        anchors.fill: parent

        TextField {
            id: keywordInput

            Layout.preferredHeight: 50
            Layout.fillWidth: true

            placeholderText: "Enter keyword term here ..."

            background: Rectangle {
                radius: 20
                border.color: "#C9C9C9"
                border.width: 1
            }

            verticalAlignment: TextField.AlignVCenter

            font.pixelSize: 16
            font.weight: Font.Normal
            font.family: "Arial"
            leftPadding: 10

            onAccepted: {
                keywordDialog.userKeywords = [...keywordDialog.userKeywords, keywordInput.text.toLowerCase()];
                keywordInput.text = "";
            }
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

                    width: Math.min(150, modelData.length * 10)
                    height: 20
                    radius: 10
                    color: "#005fee"

                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            keywordsContainer.removeKeyword(modelData);
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5

                        text: modelData
                        elide: Text.ElideMiddle
                        color: "white"
                        font.pixelSize: 10
                    }
                }
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

    onRejected: console.log("Note adding was canceled by user")
    modal: true
}