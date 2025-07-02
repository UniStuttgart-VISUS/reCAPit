
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.15



Canvas {
    id: canvas

    required property var data
    required property string sourcePic
    property int picSize: 12

    Component.onCompleted: {
        loadImage(sourcePic)
    }

    onPaint: {
        var ctx = getContext("2d")
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        const radius = Math.min(canvas.width, canvas.height) / 2;
        const picRadius = picSize * 0.5
        var startAngle = 0

        for (var j = 0; j < data.length; j++) {
            var sliceAngle = 2 * Math.PI * data[j].value;
            ctx.fillStyle = data[j].color
            ctx.beginPath()
            ctx.moveTo(canvas.width / 2, canvas.height / 2)
            ctx.arc(canvas.width / 2, canvas.height / 2, Math.min(canvas.width, canvas.height) / 2, startAngle, startAngle + sliceAngle)
            ctx.closePath()
            ctx.fill()
            startAngle += sliceAngle
        }

        ctx.fillStyle = "#fff";
        ctx.beginPath()
        ctx.arc(canvas.width / 2, canvas.height / 2, radius - picRadius, 0, 2*Math.PI)
        ctx.closePath()
        ctx.fill()
        ctx.drawImage(sourcePic, picRadius, picRadius, 2*(radius-picRadius), 2*(radius-picRadius));
    }
}