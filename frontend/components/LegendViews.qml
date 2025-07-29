import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQuick.Effects
import QtQml

Rectangle {
    id: rootLegend

    required property string textColor
    required property string streamTopId
    required property string streamBottomId
    required property var identifiers

    required property int h1
    required property int h2
    required property int h3
    required property int h4

    Column {
        anchors.fill: parent

        Rectangle {
            width: parent.width
            height: rootLegend.h1
            color: rootLegend.color

            Row {
                anchors.fill: parent

                Item {
                    width: parent.width / 2
                    height: parent.height

                    Text {
                        anchors.centerIn: parent
                        id: text1
                        text: String.fromCodePoint(0x1F4CA) + " Activity"
                        color: rootLegend.textColor
                        font.bold: true
                        font.capitalization: Font.AllUppercase
                        transform: Rotation { origin.x: text1.width / 2; origin.y: text1.height / 2; angle: -90}
                    }
                }

                Column {
                    width: parent.width / 2
                    height: parent.height

                    Item {
                        width: parent.width
                        height: parent.height / 2

                        Text {
                            anchors.centerIn: parent
                            id: text11
                            text: rootLegend.streamTopId
                            color: rootLegend.textColor
                            font.bold: false
                            font.capitalization: Font.AllUppercase
                            transform: Rotation { origin.x: text11.width / 2; origin.y: text11.height / 2; angle: -90}
                        }
                    }
                    Item {
                        width: parent.width
                        height: parent.height / 2

                        Text {
                            anchors.centerIn: parent
                            id: text12
                            text: rootLegend.streamBottomId
                            color: rootLegend.textColor
                            font.bold: false
                            font.capitalization: Font.AllUppercase
                            transform: Rotation { origin.x: text12.width / 2; origin.y: text12.height / 2; angle: -90}
                        }
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: rootLegend.h2
            color: rootLegend.color
        }

        Rectangle {
            width: parent.width
            height: rootLegend.h3
            color: rootLegend.color

            Row {
                anchors.fill: parent

                Item {
                    width: parent.width / 2
                    height: parent.height
                    Text {
                        anchors.centerIn: parent

                        id: text2
                        text: String.fromCodePoint(0x1F4AC) + " Participants"
                        color: rootLegend.textColor
                        font.bold: true
                        font.capitalization: Font.AllUppercase
                        transform: Rotation { origin.x: text2.width / 2; origin.y: text2.height / 2; angle: -90}
                    }
                }
                Column {
                    width: parent.width / 2
                    height: parent.height - 2*30
                    topPadding: 30
                    bottomPadding: 30

                    Repeater {
                        width: parent.width
                        height: parent.height

                        model: rootLegend.identifiers

                        delegate: Item {
                            required property string modelData

                            width: parent.width
                            height: parent.height / identifiers.length

                            Text {
                                anchors.centerIn: parent

                                id: text21
                                text: modelData.slice(0, 2)
                                color: rootLegend.textColor
                                font.bold: false
                                font.capitalization: Font.AllUppercase
                                transform: Rotation { origin.x: text21.width / 2; origin.y: text21.height / 2; angle: -90}
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            width: parent.width
            height: rootLegend.h4
            color: rootLegend.color

            Text {
                anchors.centerIn: parent

                id: text3
                text: String.fromCodePoint(0x1F4DC) + " Topic Cards"
                color: rootLegend.textColor
                font.bold: true
                font.capitalization: Font.AllUppercase
                transform: Rotation { origin.x: text3.width / 2; origin.y: text3.height / 2; angle: -90}
            }
        }
    }
}