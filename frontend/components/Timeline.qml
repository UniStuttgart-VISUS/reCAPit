import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.2

import "../js/utils.js" as Utils

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
                color: cmap[modelData.Category(index)]

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