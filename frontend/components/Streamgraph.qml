import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml
import QtCharts 2.6

import "utils.js" as Utils

Item {
    id: shapeContainer

    required property var mtsModel
    property var cmap
    property bool flipped: false

    transform: Scale{xScale: 1; yScale: flipped ? -1 : 1; origin.x: shapeContainer.width / 2; origin.y: shapeContainer.height / 2}

    Component.onCompleted: {
        for (var idx = 0; idx < mtsModel.StackCount(); idx++) {
            var component = Qt.createComponent("AreaPath.qml");
            if (component.status == Component.Ready) {
                component.createObject(shapeContainer, {pathStr: mtsModel.StackAsSvgPath(idx, shapeContainer.width, shapeContainer.height), areaColor: cmap[mtsModel.Label(idx)]});
            }
        }
    }
}