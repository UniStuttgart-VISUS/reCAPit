import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.2

import "utils.js" as Utils

Item {
    id: timeline
    required property var modelData
    required property var xScale
    property var cmap

    Repeater {
        model: modelData.rowCount()
        delegate: Item {
            required property int index;
            Rectangle {
                id: textBlock
                property int w: xScale(modelData.PosEndSec(index)) - xScale(modelData.PosStartSec(index))
                x: xScale(modelData.PosStartSec(index))
                y: 0
                radius: 2
                width: w
                height: timeline.height
                color: cmap.get(modelData.Category(index))
                /*
                Rectangle {
                    anchors.centerIn: parent
                    width: timeline.height+5
                    height: timeline.height+5
                    radius: timeline.height
                    color: cmap.get(modelData.Role())
                    visible: modelData.IsInterrogative(index);
                }
                Text {
                    anchors.centerIn: parent
                    text: "?"                     
                    visible: modelData.IsInterrogative(index);
                    font.pointSize: 10
                    font.weight: 700
                    color: "white"
                    y: 0
                }
                */
                /*
                Text {
                    function get_utterance_id(src, idx) {
                        const code_first = src.toLowerCase().charCodeAt(0);
                        const offset1 = (code_first - 'a'.charCodeAt());
                        return "%1%2".arg(src.toUpperCase().slice(0, 2)).arg(idx);
                        //return String.fromCodePoint(9398 + offset1) + String.fromCodePoint(9312 + idx);
                    }
                    anchors.centerIn: parent
                    text: get_utterance_id(modelData.Identifier(), index);
                    visible: parent.width > 25
                    font.pointSize: 9
                    font.weight: 700
                    color: "white"
                    y: 0
                }
                */
                ToolTip {
                    id: toolTip
                    text: {
                        let formatted = modelData.EventData(index);
                        formatted = formatted.replace(/\.+/g, '.');
                        formatted = formatted.split('.').map((s) => s.trim()).join('\n');
                        return "**%1**: %2".arg(modelData.Identifier()).arg(formatted);
                    }
                    visible: false
                    delay: 250
                    contentItem: Text {
                        text: toolTip.text
                        font: toolTip.font
                        textFormat: Text.MarkdownText
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
    }
}