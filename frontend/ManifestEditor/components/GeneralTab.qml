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

    component DecimalSpinBox: SpinBox {
        property int decimals: 1
        readonly property int decimalFactor: Math.pow(10, decimals)
        readonly property real realValue: value / decimalFactor

        editable: true
        stepSize: 1

        function decimalToInt(decimal) { return Math.round(decimal * decimalFactor) }

        textFromValue: function(value, locale) {
            return Number(value / decimalFactor).toLocaleString(locale, 'f', decimals)
        }

        valueFromText: function(text, locale) {
            return Math.round(Number.fromLocaleString(locale, text) * decimalFactor)
        }
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
                    Repeater {
                        anchors.fill: parent
                        model: Object.keys(manifest.sources)

                        delegate: UserFileInput {
                            required property var modelData

                            width: parent.width
                            name: manifest.sources[modelData].meta.display_name
                            path: manifest.sources[modelData].path
                            isDir: manifest.sources[modelData].meta.is_dir
                            fileExtensions: manifest.sources[modelData].meta.file_extensions
                            valid: isDir ? manifest.is_valid_dir(manifest.sources[modelData].path, "*") : manifest.is_valid_file(manifest.sources[modelData].path)

                            onUserPathChanged: (newPath) => {
                                manifest.set_source_path(modelData, newPath);
                            }
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

                            required property var sources
                            required property var artifacts

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

                                        Repeater {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true

                                            model: Object.keys(groupRec.sources)

                                            delegate: ColumnLayout {
                                                required property string modelData

                                                UserFileInput {
                                                    Layout.fillWidth: true
                                                    name: groupRec.sources[modelData].meta.display_name
                                                    path: groupRec.sources[modelData].path
                                                    valid: manifest.is_valid_dir(groupRec.sources[modelData].path, "*")
                                                    isDir: groupRec.sources[modelData].meta.is_dir

                                                    onUserPathChanged: (newPath) => {
                                                        manifest.recordings.setSourcePath(groupRec.index, modelData, newPath)
                                                    }
                                                }
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 10
                                                    Text {
                                                        text: "Offset (sec.)"
                                                        font.bold: true
                                                    }
                                                    DecimalSpinBox {
                                                        id: offsetSpin
                                                        Layout.fillWidth: true
                                                        from: 0
                                                        value: decimalToInt(groupRec.sources[modelData].offset_sec)
                                                        to: decimalToInt(999)

                                                        onValueModified: {
                                                            manifest.recordings.setSourceOffset(groupRec.index, modelData, realValue);
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