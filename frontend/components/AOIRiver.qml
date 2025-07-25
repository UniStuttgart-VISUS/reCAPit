import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "../js/utils.js" as Utils
import "."

Item {
    id: aoiRiver
    required property var stacksTop
    required property var stacksBottom
    required property var xScale
    required property real tickIntervalMajor
    required property real tickIntervalMinor
    required property var cmapTop
    required property var cmapBottom
    required property var tickInfos

    function merged_tick_positions(tick_infos, min_gap) {
        if (tick_infos.length === 0)
            return [];

        tick_infos.forEach((x) => {
            x.pos_px = xScale(x.pos_ms*1e-3);
        });

        const sorted = tick_infos.sort((a, b) => a.pos_px - b.pos_px);
        var merged = sorted.slice(0, 1);

        for (var idx = 1; idx < sorted.length; idx++) {
            var curr = sorted[idx];
            var last = merged[merged.length - 1];

            if (curr.pos_px - last.pos_px < min_gap) {
                last.label += sorted[idx].label 
            }
            else {
                merged.push(curr);
            }
        }
        return merged;
    }

    Item {
        width: parent.width
        height: parent.height

        Repeater {
            model: aoiRiver.merged_tick_positions(tickInfos, 25)
            delegate: Item {
                required property var modelData

                x: modelData.pos_px 
                y: 0

                width: textRectBox.implicitWidth
                height: parent.height

                Rectangle {
                    x: parent.width / 2
                    width: 2
                    height: parent.height
                    color: "#f0f0f0"
                    z: 5
                }

                Rectangle {
                    id: textRectBox
                    width: txtLabel.implicitWidth + 5
                    height: 20
                    z: 15

                    anchors.centerIn: parent
                    color: "#e0e0e0"

                    Text {
                        id: txtLabel
                        anchors.centerIn: parent
                        color: "white"
                        text: modelData.label
                        font.weight: Font.Bold
                    }
                }
            }
        }
    }

    Column {
        anchors.fill: parent

        Streamgraph {
            id: streamAttention
            cmap: aoiRiver.cmapTop
            mtsModel: stacksTop
            width: parent.width
            height: (parent.height - 0) / 2
            flipped: false
            z: 10
        }

        Streamgraph {
            id: streamActivity
            cmap: aoiRiver.cmapBottom
            mtsModel: stacksBottom
            //anchors.top: streamAttention.bottom
            width: parent.width
            height: (parent.height - 0) / 2
            flipped: true
            z: 10
        }
    }
}