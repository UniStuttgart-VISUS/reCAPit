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
            text: "Duration"
            font.bold: true
        }

        SpinBox {
            id: durationSpin

            value: manifest.duration_sec
            from: 0
            to: 9999
            editable: true

            textFromValue: function(value) {
                return "%1 sec.".arg(value);
            }
            valueFromText: function(text) {
                return Number(text.slice(0, -5))
            }

            Binding {
                target: manifest
                property: "duration_sec"
                value: durationSpin.value
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
                        name: "Speech (.wav)"
                        path: manifest.audio
                        isDir: false
                        fileExtensions: ["WAV files (*.wav)"]
                        valid: manifest.is_valid_file(manifest.audio)

                        onUserPathChanged: (newPath) => {
                            manifest.audio = newPath;
                        }
                    }

                    UserFileInput {
                        width: parent.width
                        name: "Areas of Interest (.json)"
                        path: manifest.aoi
                        valid: manifest.is_valid_file(manifest.aoi)
                        isDir: false
                        fileExtensions: ["JSON files (*.json)"]
                        onUserPathChanged: (newPath) => {
                            manifest.aoi = newPath;
                        }
                    }

                    UserFileInput {
                        width: parent.width
                        name: "Notes"
                        path: manifest.notes
                        valid: manifest.is_valid_dir(manifest.notes, '.docm')
                        isDir: true
                        onUserPathChanged: (newPath) => {
                            manifest.notes = newPath;
                        }
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
                        name: "Workspace Video (.mp4)"
                        path: manifest.video_workspace
                        valid: manifest.is_valid_file(manifest.video_workspace)
                        isDir: false
                        fileExtensions: ["MP4 files (*.mp4)"]
                        onUserPathChanged: (newPath) => {
                            manifest.video_workspace = newPath;
                        }
                    }

                    UserFileInput {
                        width: parent.width
                        name: "Side Video (.mp4)"
                        path: manifest.video_side
                        valid: manifest.is_valid_file(manifest.video_side)
                        isDir: false
                        fileExtensions: ["MP4 files (*.mp4)"]
                        onUserPathChanged: (newPath) => {
                            manifest.video_side = newPath;
                        }
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
                            required property real sourceGazeOffset
                            required property string sourceGazeHardware
                            required property int index
                            required property var model

                            Layout.fillWidth: true
                            Layout.preferredHeight: recContainer.implicitHeight + 25

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
                                id: recContainer

                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                anchors.topMargin: 10
                                anchors.bottomMargin: 45

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

                                FileDialog {
                                    id: dialogFixations
                                    onAccepted: {
                                        const path = new URL(selectedFile).pathname.slice(1);
                                        model.sourceGaze = path;
                                    }
                                    nameFilters: ["CSV files (*.csv)"]
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 30

                                    Text { 
                                        text: "Role"
                                        font.bold: true
                                    }
                                    CustomComboBox {
                                        Layout.preferredHeight: 30
                                        Layout.fillWidth: true

                                        id: role2recCombo
                                        model: manifest.participant_roles
                                        textRole: "display"
                                        Component.onCompleted: currentIndex = find(role)
                                        onActivated: {
                                            groupRec.model.role = currentText;
                                        }
                                    }
                                }

                                GroupBox {
                                    Layout.fillWidth: true
                                    title: "Sources"
                                    ColumnLayout {
                                        anchors.fill: parent
                                        spacing: 10

                                        UserFileInput {
                                            Layout.fillWidth: true
                                            name: "Gaze"
                                            path: sourceGaze
                                            valid: manifest.is_valid_dir(sourceGaze, "*")
                                            isDir: true
                                            onUserPathChanged: (newPath) => {
                                                groupRec.model.sourceGaze = newPath;
                                            }
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 10

                                            Text {
                                                text: "Device)"
                                                font.bold: true
                                            }
                                            CustomComboBox {
                                                Layout.fillWidth: true
                                                id: hardwareSelection
                                                model: manifest.supported_eye_tracking_devices()
                                                currentIndex: manifest.supported_eye_tracking_devices().indexOf(groupRec.sourceGazeHardware)
                                                onActivated: (index) => {
                                                    groupRec.model.sourceGazeHardware = model[index];
                                                }
                                            }
                                        }
                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 10
                                            Text {
                                                text: "Offset (sec.)"
                                                font.bold: true
                                            }
                                            SpinBox {
                                                id: offsetSpin
                                                Layout.fillWidth: true
                                                editable: true

                                                property int decimals: 1
                                                readonly property int decimalFactor: Math.pow(10, decimals)
                                                property real realValue: value / decimalFactor

                                                stepSize: 1

                                                function decimalToInt(decimal) {
                                                    return decimal * decimalFactor
                                                }

                                                from: 0
                                                value: decimalToInt(sourceGazeOffset)
                                                to: decimalToInt(999)

                                                textFromValue: function(value, locale) {
                                                    return Number(value / decimalFactor).toLocaleString(locale, 'f', offsetSpin.decimals)
                                                }

                                                valueFromText: function(text, locale) {
                                                    return Math.round(Number.fromLocaleString(locale, text) * decimalFactor)
                                                }

                                                onValueModified: {
                                                    groupRec.model.sourceGazeOffset = realValue;
                                                }
                                            }
                                        }
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