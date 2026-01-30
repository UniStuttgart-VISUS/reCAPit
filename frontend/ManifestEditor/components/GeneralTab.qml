import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Shapes 1.2
import QtQml
import QtQml.Models
import QtQuick.Controls.Basic
import QtQuick.Effects

import "."

ColumnLayout {
    spacing: 20

    FileDialog {
        id: dialogSpeech
        onAccepted: {
            manifest.audio = new URL(selectedFile).pathname.slice(1);
        }
        nameFilters: ["WAV files (*.wav)"]
    }

    FileDialog {
        id: dialogAoi
        onAccepted: {
            manifest.aoi = new URL(selectedFile).pathname.slice(1);
        }
        nameFilters: ["JSON files (*.json)"]
    }

    FolderDialog {
        id: dialogNotes
        onAccepted: {
            manifest.notes = new URL(selectedFolder).pathname.slice(1);
        }
    }

    FileDialog {
        id: dialogVideoWorkspace
        onAccepted: {
            manifest.video_workspace = new URL(selectedFile).pathname.slice(1);
        }
        nameFilters: ["MP4 files (*.mp4)"]
    }

    FileDialog {
        id: dialogVideoSide
        onAccepted: {
            manifest.video_side = new URL(selectedFile).pathname.slice(1);
        }
        nameFilters: ["MP4 files (*.mp4)"]
    }

    Dialog {
        id: addRoleDialog
        title: "Add New Role"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel

        ColumnLayout {
            spacing: 10
            
            Text {
                text: "Enter role name:"
            }
            
            TextField {
                id: roleNameInput
                Layout.preferredWidth: 250
                placeholderText: "e.g., Developer, Designer, etc."
                onAccepted: {
                    if (text.trim() !== "") {
                        addRoleDialog.accept()
                    }
                }
            }
        }

        onAccepted: {
            if (roleNameInput.text.trim() !== "") {
                var rowCount = manifest.participant_roles.rowCount()
                manifest.participant_roles.insertRow(rowCount)
                var index = manifest.participant_roles.index(rowCount, 0)
                manifest.participant_roles.setData(index, roleNameInput.text.trim(), Qt.EditRole)
                roleNameInput.text = ""
            }
        }
        
        onRejected: {
            roleNameInput.text = ""
        }
    }

    GridLayout {
        columns: 2
        Layout.fillWidth: true
        Layout.fillHeight: true
        rowSpacing: 20

        Text { 
            text: "Language"
            font.bold: true
        }

        CustomComboBox {
            id: langSelection
            model: manifest.supported_languages()
            currentIndex: manifest.supported_languages().indexOf(manifest.language)
            Binding {
                target: manifest
                property: "language"
                value: langSelection.currentValue
            }
        }

        Text { 
            text: "Roles"
            font.bold: true
        }
        
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            
            ListView {
                id: roleListView

                model: manifest.participant_roles
                Layout.fillWidth: true
                Layout.preferredHeight: 30

                orientation: ListView.Horizontal
                spacing: 10

                delegate: Rectangle {
                    required property int index
                    required property string display
                    
                    width: Math.max(70, roleContent.width + 10)
                    height: roleListView.height
                    radius: 15
                    color: "#ddd"

                    RowLayout {
                        id: roleContent
                        anchors.centerIn: parent
                        spacing: 5

                        Text {
                            id: roleText
                            text: display
                        }

                        Button {
                            text: "×"
                            flat: true
                            Layout.preferredWidth: 20
                            Layout.preferredHeight: 20
                            font.pixelSize: 14
                            font.bold: true
                            onClicked: {
                                manifest.participant_roles.removeRow(index)
                            }
                        }
                    }
                }
            }
            
            CustomButton {
                text: "+ Add Role"
                Layout.preferredHeight: 30
                onClicked: addRoleDialog.open()
            }
        }
    }

    GroupBox {
        id: groupDataSources

        Layout.fillWidth: true

        label: Text {
            text: "📂 Global Data"
            font.pixelSize: 18
            x: groupDataSources.leftPadding
            width: groupDataSources.availableWidth
        }

        ColumnLayout {
            anchors.fill: parent

            GroupBox {
                id: groupGeneral
                Layout.fillWidth: true
                Layout.fillHeight: true

                label: Text {
                    text: "💾 General"
                    font.pixelSize: 16
                    x: groupGeneral.leftPadding
                    width: groupGeneral.availableWidth
                }

                Column {
                    anchors.fill: parent

                    UserFileInput {
                        width: parent.width
                        dialog: dialogSpeech
                        name: "Speech (.wav)"
                        path: manifest.audio
                        valid: manifest.is_valid_file(manifest.audio)
                    }

                    UserFileInput {
                        width: parent.width
                        dialog: dialogAoi
                        name: "Areas of Interest (.json)"
                        path: manifest.aoi
                        valid: manifest.is_valid_file(manifest.aoi)
                    }

                    UserFileInput {
                        width: parent.width
                        dialog: dialogNotes
                        name: "Notes"
                        path: manifest.notes
                        valid: manifest.is_valid_notes_dir(manifest.notes)
                    }
                }
            }

            GroupBox {
                id: groupVideos
                Layout.fillWidth: true
                Layout.fillHeight: true

                label: Text {
                    text: "📹 Videos"
                    font.pixelSize: 16
                    x: groupVideos.leftPadding
                    width: groupVideos.availableWidth
                }

                Column {
                    anchors.fill: parent

                    UserFileInput {
                        width: parent.width
                        dialog: dialogVideoWorkspace
                        name: "Workspace Video (.mp4)"
                        path: manifest.video_workspace
                        valid: manifest.is_valid_file(manifest.video_workspace)
                    }

                    UserFileInput {
                        width: parent.width
                        dialog: dialogVideoSide
                        name: "Side Video (.mp4)"
                        path: manifest.video_side
                        valid: manifest.is_valid_file(manifest.video_side)
                    }
                }
            }
        }
    }

    GroupBox {
        id: groupRecordings
        Layout.fillWidth: true

        label: Text {
            text: "👤 Participant Data"
            font.pixelSize: 18
            x: groupRecordings.leftPadding
            width: groupRecordings.availableWidth
        }

        ColumnLayout {
            anchors.fill: parent

            ScrollView {
                Layout.fillWidth: true
                //Layout.preferredHeight: 300
                Layout.topMargin: 10
                Layout.bottomMargin: 10

                GridLayout {
                    id: recList
                    width: groupRecordings.availableWidth
                    clip: true
                    columns: 2
                    rowSpacing: 25
                    columnSpacing: 50

                    Repeater {
                        model: manifest.recordings
                        delegate: Rectangle {
                            id: groupRec

                            required property string recId
                            required property string role
                            required property string sourceGaze
                            required property int index
                            required property var model

                            Layout.fillWidth: true
                            Layout.preferredHeight: 150

                            Layout.horizontalStretchFactor: 1

                            radius: 5
                            color: "#ececec"

                            Dialog {
                                id: editRecIdDialog
                                title: "Edit Recording Id"
                                modal: true
                                anchors.centerIn: parent
                                standardButtons: Dialog.Ok | Dialog.Cancel

                                ColumnLayout {
                                    spacing: 10
                                    
                                    Text {
                                        text: "Enter recording id:"
                                    }
                                    TextField {
                                        id: recIdInput
                                        Layout.preferredWidth: 250
                                        placeholderText: "e.g., John, Peter, etc."
                                    }
                                }

                                onAccepted: {
                                    model.recId = recIdInput.text;
                                }
                            }
                            /*
                            RectangularShadow {
                                anchors.fill: parent
                                offset.x: 0
                                offset.y: 0
                                radius: parent.radius
                                blur: 20
                                spread: 5
                                color: Qt.darker(parent.color, 1.1)
                            }
                            */

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                anchors.topMargin: 10
                                anchors.bottomMargin: 25

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30

                                    Button {
                                        flat: true
                                        icon.source: "../icons/trash.png"
                                        icon.color: "transparent"
                                        Layout.preferredWidth: 30
                                        Layout.preferredHeight: 30
                                        onClicked: {
                                            manifest.recordings.removeRow(index)
                                        }
                                    }

                                    Button {
                                        flat: true
                                        icon.source: "../icons/pen.png"
                                        icon.color: "transparent"
                                        Layout.preferredWidth: 30
                                        Layout.preferredHeight: 30
                                        
                                        onClicked: {
                                            editRecIdDialog.open()
                                        }
                                    }
                                    Text {
                                        text: recId
                                        verticalAlignment: Text.AlignVCenter
                                        horizontalAlignment: Text.AlignHCenter
                                        font.pixelSize: 16
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                    }
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true

                                    id: recContainer
                                    columns: 4

                                    FileDialog {
                                        id: dialogFixations
                                        onAccepted: {
                                            const path = new URL(selectedFile).pathname.slice(1);
                                            model.sourceGaze = path;
                                        }
                                        nameFilters: ["CSV files (*.csv)"]
                                    }

                                    Text { 
                                        text: "Role"
                                        font.bold: true
                                    }
                                    CustomComboBox {
                                        id: role2recCombo
                                        model: manifest.participant_roles
                                        textRole: "display"
                                        Layout.preferredHeight: 30
                                        Layout.fillWidth: true
                                        Layout.columnSpan: 3
                                        Component.onCompleted: currentIndex = find(role)
                                        onActivated: {
                                            groupRec.model.role = currentText;
                                        }
                                    }

                                    UserFileInput {
                                        Layout.columnSpan: 4
                                        dialog: dialogFixations
                                        name: "Fixations"
                                        path: sourceGaze
                                        valid: manifest.is_valid_file(manifest.video_workspace)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            CustomButton {
                text: "New recording"
                onClicked: {
                    manifest.recordings.add_new('', manifest.participant_roles[0]);
                }
            }
        }
    }
}