import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Dialogs
import QtQuick.Shapes 1.2
import QtQml

import QtQuick.Controls.Basic

Window {
    id: window
    visible: true
    width: 600
    height: 800
    color: "white"

    Dialog {
        id: addProjectDialog
        title: "Add New Project"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            spacing: 10
            
            Text {
                text: "Enter project name:"
            }
            
            TextField {
                id: roleNameInput
                Layout.preferredWidth: 250
                placeholderText: ""
                onAccepted: {
                }
            }
        }

        onAccepted: {
            var success = projectManager.add_project(roleNameInput.text);
            if (!success) {

            }
        }
        
        onRejected: {
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10
        
        // Logo
        Image {
            id: logoImage
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 350
            source: "../../logo.png"
            fillMode: Image.PreserveAspectFit
            smooth: true
        }

        GroupBox {
            Layout.fillWidth: true
            Layout.fillHeight: true

            title: "Project List"

            background: Rectangle {
                y: parent.topPadding - parent.bottomPadding
                width: parent.width
                height: parent.height - parent.topPadding + parent.bottomPadding
                color: "#efefef"
                border.color: "#fff"
                radius: 2
            }
            label: Label {
                x: parent.leftPadding
                width: parent.availableWidth
                text: parent.title
                font.pixelSize: 20
                color: "#888"
            }


        ListView {
            id: projectList

            width: parent.width
            height: parent.height - 50
            anchors.margins: 10

            model: projectManager
            spacing: 10
            clip: true

            header: Rectangle {
                width: parent.width
                height: 75
                color: "#efefef"

                RowLayout {
                    spacing: 10
                    anchors.fill: parent
                    anchors.margins: 10
                    Text {
                        text: "Name"
                        font.pixelSize: 16
                        color: '#888'
                        horizontalAlignment: Text. AlignHCenter
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Export Directory"
                        font.pixelSize: 16
                        color: '#888'
                        horizontalAlignment: Text. AlignHCenter
                    }
                    Text {
                        text: "Last Opened"
                        font.pixelSize: 16
                        color: '#888'
                        horizontalAlignment: Text. AlignHCenter
                    }
                    Text {
                        Layout.preferredWidth: 200
                        text: "Actions"
                        font.pixelSize: 16
                        color: '#888'
                        horizontalAlignment: Text. AlignHCenter
                    }
                }
            }

            delegate: Rectangle {
                id: proBtn

                required property string name
                required property string dir
                required property string date_created
                required property string last_opened
                required property int index

                width: parent.width
                height: 50


                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                }

                border.color: mouseArea.containsMouse ? '#fff' : '#555'
                border.width: 1
                radius: 2
                opacity: enabled ? 1 : 0.3
                color: mouseArea.containsMouse ? '#007bff' : "#eee"

                RowLayout {
                    spacing: 10

                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10

                    Text {
                        text: name
                        font.pixelSize: 16
                        color: mouseArea.containsMouse ? '#fff' : '#000'
                        horizontalAlignment: Text.AlignLeft
                    }
                    Text {
                        id: dirText
                        Layout.fillWidth: true
                        text: dir
                        font.pixelSize: 12

                        clip: true
                        color: mouseArea.containsMouse ? '#fff' : '#000'
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Text {
                        text: last_opened
                        font.pixelSize: 12
                        color: mouseArea.containsMouse ? '#fff' : '#000'
                        horizontalAlignment: Text. AlignRight
                    }

                    Row {
                        spacing: 10
                        Layout.preferredWidth: 200
                        Button {
                            icon.source: "../icons/app.png"
                            icon.color: "transparent"
                            width: 50
                            flat: true
                            onClicked: {
                                projectManager.open_project(index, "viewer");
                                window.close();
                            }
                        }
                        Button {
                            icon.source: "../icons/gear.png"
                            width: 50
                            flat: true
                            onClicked: {
                                projectManager.open_project(index, "manifest");
                                window.close();

                            }
                        }
                    }
                }
            }
        }

        Button {
            id: newProBtn
            text: "New Project"
            anchors.top: projectList.bottom
            height: 30
            anchors.horizontalCenter: parent.horizontalCenter

            background: Rectangle {
                implicitWidth: 100
                implicitHeight: 40
                opacity: newProBtn.down ? 0.3 : 1.0
                border.width: 1
                radius: 2
            }

            onClicked: {
                addProjectDialog.open();
            }
        }
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
        // License Information
        Label {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: parent.width

            text: "Licensed under the GNU General Public License v3.0\nThis program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation."
            font.pixelSize: 10
            color: "#666"
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            lineHeight: 1.2
        }
    }
}

