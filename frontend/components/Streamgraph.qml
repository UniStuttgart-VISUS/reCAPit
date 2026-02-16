import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml
import QtCharts 2.6

import "../js/utils.js" as Utils

Item {
    id: shapeContainer

    required property var mtsModel
    property var cmap
    property bool flipped: false

    // Flip the chart horizontally when "flipped" is set 
    transform: Scale{xScale: 1; yScale: flipped ? -1 : 1; origin.x: shapeContainer.width / 2; origin.y: shapeContainer.height / 2}

    Repeater {
        model: mtsModel.StackCount()
        delegate: AreaPath {
            required property int index;

            pathStr: mtsModel.StackAsSvgPath(index, shapeContainer.width, shapeContainer.height) 
            areaColor: cmap[mtsModel.Label(index)]
        }
    }
}