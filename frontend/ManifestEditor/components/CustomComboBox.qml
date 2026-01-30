import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Shapes 1.2
import QtQuick.Controls.Basic
import QtQml

ComboBox {
    id: control
    background: Rectangle {
        implicitWidth: 120
        implicitHeight: 40
        border.color: control.pressed ? "#003366" : "#0066cc"
        border.width: 1.25
        radius: 3
    }
    indicator: Canvas {
        id: canvas
        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        width: 12
        height: 8
        contextType: "2d"

        Connections {
            target: control
            function onPressedChanged() { canvas.requestPaint(); }
        }

        onPaint: {
            context.reset();
            context.moveTo(0, 0);
            context.lineTo(width, 0);
            context.lineTo(width / 2, height);
            context.closePath();
            context.fillStyle = "#0066cc";
            context.fill();
        }
    }
}