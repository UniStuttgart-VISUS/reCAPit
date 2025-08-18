import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

GroupBox {
    id: control

    required property string pastedTextColor
    required property string placeHolderText
    required property string textContent
    required property var labels

    //property ListModel labelsModel: ListModel {}
    //property alias textContentQuote: textAreaOut.text

    signal linkActivated(string link)

    function setOutText(text) 
    {
        textAreaOut.text = text;
    }

    function getOutText()
    {
        return textAreaOut.text;
    }

    label: Label {
        x: control.leftPadding
        width: control.availableWidth
        text: control.title
        font.pixelSize: 16
        font.bold: true
        elide: Text.ElideRight
    }

    background: Rectangle {
        y: control.topPadding - control.bottomPadding
        width: parent.width
        height: parent.height - control.topPadding + control.bottomPadding
        color: "transparent"
        border.color: "#e0e0e0"
        border.width: 1
        radius: 5
    }
    /*
    background: Rectangle {
        radius: 5
        border.color: "#e0e0e0"
        border.width: 2
    }
    */


    ColumnLayout {
        anchors.fill: parent
        //anchors.topMargin: 15

        Flow {
            id: flow
            Layout.fillWidth: true
            spacing: 15

            Repeater {
                id: myRepeater
                anchors.margins: 30
                anchors.fill: parent

                model: control.labels
                delegate: Rectangle {
                    id: rect
                    required property string modelData

                    width: Math.min(150, modelData.length * 10)
                    height: 25
                    radius: rect.width / 2
                    color: "#A8A8A8"

                    Text {
                        anchors.centerIn: parent
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5

                        text: modelData
                        elide: Text.ElideMiddle
                        color: "white"
                        font.pixelSize: 12
                        font.weight: Font.Bold
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true

                        onClicked: {
                            const cursor_pos = textAreaOut.cursorPosition;
                            const symbol_chr = String.fromCodePoint(0x27E8) + modelData + String.fromCodePoint(0x27E9);

                            //control.textContentQuote = control.textContentQuote.slice(0, cursor_pos) + symbol_chr + control.textContentQuote.slice(cursor_pos, -1);
                            textAreaOut.text = textAreaOut.text.slice(0, cursor_pos) + symbol_chr + textAreaOut.text.slice(cursor_pos, -1);
                            textAreaOut.cursorPosition = cursor_pos + symbol_chr.length;
                        }

                        onEntered: {
                            rect.color = "#6F70E1";
                        }

                        onExited: {
                            rect.color = "#A8A8A8";
                        }
                    }
                }
            }
        }

        TextArea  {
            id: textArea
            visible: control.textContent.length > 0

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignLeft
            Layout.verticalStretchFactor: 1

            text: control.textContent
            textFormat: Text.RichText
            wrapMode: Text.WordWrap

            onLinkActivated: (link) => {
                control.linkActivated(link);
            }

            background: Rectangle {
                radius: 5
            }

            font.pixelSize: 14
            readOnly: true
            selectByMouse: true
        }

        TextArea  {
            id: textAreaOut
            placeholderText: control.placeHolderText

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.verticalStretchFactor: 1
            Layout.alignment: Qt.AlignLeft
            Layout.minimumHeight: 100

            textFormat: Text.PlainText
            wrapMode: Text.WordWrap

            font.pixelSize: 14
            color: pastedTextColor
            readOnly: false

            background: Rectangle {
                radius: 5
            }
        }

        /*
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.verticalStretchFactor: 3
        }
        */
    }
}
