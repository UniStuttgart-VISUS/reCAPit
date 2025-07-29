import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.2

import "utils.js" as Utils

Item {
    id: timeline
    required property var modelData;
    required property var xScale;


    Repeater {
        model: modelData.rowCount()
        delegate: Image {
            required property int index;
            property int w: timeline.height

            x: xScale(modelData.PosStartSec(index)) + .5 * (xScale(modelData.PosEndSec(index)) - xScale(modelData.PosStartSec(index)))
            y: 0
            width: w
            height: timeline.height

            source: {
                if (modelData.HasInsertions(index) && modelData.HasDeletions(index))
                    return "../icons/insert_delete.png"
                if (modelData.HasInsertions(index))
                    return "../icons/insert.png"
                if (modelData.HasDeletions(index))
                    return "../icons/delete.png"
                return "../icons/note.png"
            }
            visible: modelData.HasInsertions(index) || modelData.HasDeletions(index)
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
                text: modelData.HTML(index)
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