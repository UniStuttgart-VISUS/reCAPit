import QtQuick 2.15
import QtQuick.Controls.Basic
import QtQuick.Layouts 2.15

Rectangle {
    property alias text: dataLabel.text

    width: 50
    height: dataLabel.height + 5

    radius: 3
    color: "#fff"

    Label { 
        id: dataLabel 
        anchors.centerIn: parent
    }
}