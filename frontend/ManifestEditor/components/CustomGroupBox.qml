import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Shapes 1.2
import QtQml
import QtQml.Models
import QtQuick.Controls.Basic

import "."

GroupBox {
    id: control
    default property alias content: layout.data
    property bool expanded: false

    implicitHeight: (expanded ? layout.implicitHeight : 0)  + label.implicitHeight + topPadding + bottomPadding

    states: [
        State {
            name: "expanded"; when: expanded
            PropertyChanges { target: layout; opacity: 1.0}
        },
        State {
            name: "collapsed"; when: !expanded
            PropertyChanges { target: layout; opacity: 0.0}
        }
    ]

    transitions: Transition {
        reversible: true
        SequentialAnimation {
            NumberAnimation { properties: "opacity"; easing.type: Easing.InOutQuad; duration: 150}
            PropertyAction { target: layout; property: "visible"; value: !expanded }
        }
    }


    label: RowLayout {
        Label {
            Layout.fillWidth: true
            text: control.title
            color: "#000"
            font.pixelSize: 18
        }
        Button {
            id: expandButton
            implicitWidth: 24
            implicitHeight: 24
            contentItem: Shape {
                id: arrowShape
                width: 12
                height: 12
                anchors.centerIn: parent
                
                ShapePath {
                    strokeWidth: 0
                    fillColor: expandButton.hovered ? "#888" : "#ccc"
                    PathSvg {
                        path: expanded 
                            ? "M 0 2 L 6 10 L 12 2 Z"   // Down arrow
                            : "M 2 0 L 10 6 L 2 12 Z"   // Right arrow
                    }
                }
            }
            background: Rectangle { color: "transparent" }
            onClicked: {
                expanded = !expanded;
            }
        }
    }
    ColumnLayout {
        id: layout
        width: parent.width
        spacing: 5
        //visible: expanded
    }
}