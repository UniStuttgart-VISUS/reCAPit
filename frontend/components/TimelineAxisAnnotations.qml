import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "../js/utils.js" as Utils
import "."

// Timeline axis
Item {
    id: ta

    required property bool showLabels

    required property real fromTimestamp
    required property real toTimestamp

    required property real tickIntervalMajor
    required property real tickIntervalMinor

    required property var modelData2;
    required property var xScale;

    Shape {
        anchors.fill: parent
        ShapePath {
            strokeWidth: 1
            strokeColor: "#000"
            strokeStyle: ShapePath.SolidLine
            startX: 0; startY: height
            PathLine { x: ta.width; y: height}
        }


        // Major Ticks
        Repeater {
            model: Math.floor(ta.width / tickIntervalMajor)
            delegate: Shape {
                required property int modelData
                ShapePath {
                    strokeWidth: 1
                    strokeColor: "#000"
                    strokeStyle: ShapePath.SolidLine
                    startX: modelData*tickIntervalMajor; startY: ta.height
                    PathLine { x: modelData*tickIntervalMajor; y: ta.height-20}
                }
            }
        }
        Repeater {
            model: Math.floor(ta.width / tickIntervalMinor)
            delegate: Shape {
                required property int modelData
                ShapePath {
                    strokeWidth: 1
                    strokeColor: "#000"
                    strokeStyle: ShapePath.SolidLine
                    startX: modelData*tickIntervalMinor; startY: ta.height
                    PathLine { x: modelData*tickIntervalMinor; y: (modelData % 2 == 0 ? ta.height-15 : ta.height-10)}
                }
            }
        }

        // Major Tick Labels
        Repeater {
            model: Math.floor(ta.width / tickIntervalMajor)
            delegate: Text {
                visible: ta.showLabels
                required property int modelData
                x: modelData * tickIntervalMajor + 10
                y: ta.height-15
                text: Utils.timeFormat(ta.fromTimestamp + (ta.toTimestamp - ta.fromTimestamp) * tickIntervalMajor * modelData / ta.width)
                font.family: "Arial"
                font.pointSize: 10
                color: "black"
            }
        }

        Repeater {
            anchors.centerIn: parent

            model: modelData2.rowCount()
            delegate: Image {
                z: 200
                required property int index;

                width: Math.floor(ta.height * 1.25)
                height: Math.floor(ta.height * 1.25)

                x: xScale(modelData2.PosStartSec(index)) + .5 * (xScale(modelData2.PosEndSec(index)) - xScale(modelData2.PosStartSec(index)))
                y: 0

                source: {
                    if (!modelData2.IsOfflineNote(index)) {
                        if (modelData2.HasInsertions(index) && modelData2.HasDeletions(index))
                            return "../icons/insert_delete.png"
                        if (modelData2.HasInsertions(index))
                            return "../icons/insert.png"
                        if (modelData2.HasDeletions(index))
                            return "../icons/delete.png"
                    }
                    else {
                        if (modelData2.Label(index) === 'none')
                            return "../icons/note.png"

                        if (modelData2.Label(index) === 'important')
                            return "../icons/star.png"
                    }

                    return "../icons/note.png"
                }
                visible: modelData2.HasInsertions(index) || modelData2.HasDeletions(index)
                /*
                radius: 20
                border.width: 1
                border.color: {
                    return '#aaa';
                } 
                color: {
                    if (modelData.HasInsertions(index) && modelData.HasDeletions(index))
                        return '#7303fc';
                    if (modelData.HasInsertions(index))
                        return '#fce303';
                    if (modelData.HasDeletions(index))
                        return '#fc0345';
                    return '#000';
                } 
                Text {
                    anchors.centerIn: parent
                    text: {
                        if (modelData.HasInsertions(index) && modelData.HasDeletions(index))
                            return String.fromCodePoint(0xB1)
                        if (modelData.HasInsertions(index))
                            return String.fromCodePoint(0x2B)
                        if (modelData.HasDeletions(index))
                            return String.fromCodePoint(0x2D)
                        return '';
                    }
                    visible: modelData.HasInsertions(index) || modelData.HasDeletions(index)
                    font.pointSize: 14
                    color: {
                        if (modelData.HasInsertions(index) && modelData.HasDeletions(index))
                            return '#fff';
                        if (modelData.HasInsertions(index))
                            return '#000';
                        if (modelData.HasDeletions(index))
                            return '#000';
                        return '#000';
                    } 
                    y: 0
                }
                */
                ToolTip {
                    id: toolTip
                    text: modelData2.HTML(index)
                    /*
                    text: {
                        if (modelData.HasInsertions(index) && modelData.HasDeletions(index))
                            return modelData.Insertions(index) + " - " + modelData.Deletions(index)
                        if (modelData.HasInsertions(index))
                            return modelData.Insertions(index)
                        if (modelData.HasDeletions(index))
                            return modelData.Deletions(index)
                        return '';
                    }
                    */
                    visible: false
                    delay: 250
                    contentItem: Text {
                        text: toolTip.text
                        font: toolTip.font
                        textFormat: Text.RichText
                        color: "#000"
                    }

                    background: Rectangle {
                        border.color: "#888"
                    }
                }
                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onEntered: {
                        toolTip.visible = true;
                    }
                    onExited: {
                        toolTip.visible = false;
                    }
                }
            }
        }

        /*
        MouseArea {
            id: mouseAreaLine
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                toolTipLine.visible = true;
            }
            onExited: {
                toolTipLine.visible = false;
            }
        }

        ToolTip {
            id: toolTipLine
            text: "OK"
            visible: false
            delay: 150
            contentItem: Text {
                text: toolTipLine.text
                font: toolTipLine.font
                color: "#000"
            }
            background: Rectangle {
                border.color: "#888"
            }
        }
        */
    }
}