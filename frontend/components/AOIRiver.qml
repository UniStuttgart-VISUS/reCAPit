import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "../js/utils.js" as Utils
import "."

Item {
    id: aoiRiver

    required property list<var> stacks
    required property var xScale
    required property real tickIntervalMajor
    required property real tickIntervalMinor
    required property var cmap
    required property var tickInfos

    function merged_tick_positions(tick_infos, min_gap) {
        if (tick_infos.length === 0)
            return [];

        tick_infos.forEach((x) => {
            x.pos_px = xScale(x.posSec);
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
    Column {
        anchors.fill: parent

        Repeater {
            model: aoiRiver.stacks

            delegate: Streamgraph {
                required property var modelData
                required property int index

                cmap: aoiRiver.cmap
                mtsModel: modelData
                width: aoiRiver.width
                height: (aoiRiver.height) / aoiRiver.stacks.length
                flipped: index === 1
                z: 10
            }
        }
    }

    Repeater {
        model: tickInfos
        delegate: Item {
            required property var modelData

            x: xScale(modelData.posSec);
            y: 0
            z: 20  // Higher z-order to be on top

            width: textRectBox.implicitWidth
            height: parent.height

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter

                width: 2
                height: parent.height
                color: "#f0f0f0"
                z: 5
            }

            Rectangle {
                id: textRectBox
                width: txtLabel.implicitWidth + 10
                height: txtLabel.implicitWidth + 10
                radius: txtLabel.implicitWidth + 10
                z: 15

                anchors.centerIn: parent
                color: "black"

                Text {
                    id: txtLabel
                    anchors.centerIn: parent
                    color: "white"
                    text: modelData.label
                    font.weight: Font.Bold
                    font.pixelSize: 10
                }
            }
        }
    }
}
