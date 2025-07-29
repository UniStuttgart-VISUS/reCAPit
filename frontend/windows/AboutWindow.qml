import QtQuick 2.15
import QtQuick.Controls.Basic
import QtQuick.Layouts 1.15

Window {
    id: aboutWindow
    title: "About reCAPit"
    width: 450
    height: 350
    modality: Qt.ApplicationModal
    flags: Qt.Dialog
    
    color: "#f4f4f4"
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 20
        
        // Logo
        Image {
            id: logoImage
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 350
            source: "../../logo.png"
            fillMode: Image.PreserveAspectFit
            smooth: true
        }
        
        /*
        // Application Name
        Label {
            Layout.alignment: Qt.AlignHCenter
            text: "reCAPit"
            font.pixelSize: 28
            font.weight: Font.Bold
            color: "#333"
            horizontalAlignment: Text.AlignHCenter
        }
        
        // Subtitle
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: parent.width - 40
            text: "Reflecting on Collaborative Design Processes"
            font.pixelSize: 16
            color: "#666"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
        */
        
        // Separator
        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 200
            Layout.preferredHeight: 1
            color: "#ddd"
        }
        
        // License Information
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: parent.width - 40
            text: "Licensed under the GNU General Public License v3.0\n\nThis program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation."
            font.pixelSize: 12
            color: "#666"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            lineHeight: 1.2
        }
        
        // Spacer
        Item {
            Layout.fillHeight: true
        }
        
        // Close Button
        Button {
            Layout.alignment: Qt.AlignHCenter
            text: "Close"
            width: 80
            height: 35
            
            background: Rectangle {
                color: parent.pressed ? "#0056b3" : (parent.hovered ? "#007bff" : "#6c757d")
                radius: 4
            }
            
            contentItem: Text {
                text: parent.text
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 14
            }
            
            onClicked: {
                aboutWindow.close()
            }
        }
    }
}
