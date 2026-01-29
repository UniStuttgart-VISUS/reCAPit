import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts
import QtQuick.Dialogs
import QtQuick.Shapes 1.2
import QtQml
import QtQml.Models
import QtQuick.Controls.Basic

ApplicationWindow {
    id: appwin
    visible: true
    width: 800
    height: 1000
    color: "white"
    title: ""

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

    component CircularIndicator: Rectangle {
        required property bool success
        width: 10
        height: 10
        radius: 10
        color: success ? "#0f0" : "#f00"
    }

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: bar
            Layout.fillWidth: true

            TabButton {
                text: manifest.was_modified ? qsTr("Manifest (modified)") : qsTr("Manifest") 
                width: implicitWidth
            }
            TabButton {
                text: qsTr("Audio")
                width: implicitWidth
            }
            TabButton {
                text: qsTr("Video")
                width: implicitWidth
            }
            TabButton {
                text: qsTr("Notes")
                width: implicitWidth
            }
            TabButton {
                text: qsTr("Segments")
                width: implicitWidth
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 25
            Layout.rightMargin: 25
            Layout.topMargin: 25

            currentIndex: bar.currentIndex

            ColumnLayout {
                spacing: 20

                GridLayout {
                    columns: 2
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    rowSpacing: 20

                    Text { 
                        text: "Language"
                        font.bold: true
                    }

                    ComboBox {
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
                        
                        Button {
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

                            GridLayout {
                                columns: 4
                                anchors.fill: parent

                                CircularIndicator {success: manifest.is_valid_file(manifest.audio)}
                                Text { 
                                    text: "Speech (.wav)"
                                    font.bold: true
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: manifest.audio
                                    horizontalAlignment: Text.AlignHCenter
                                    clip: true

                                }

                                Button {
                                    text: "..."
                                    onClicked: dialogSpeech.open();
                                    Layout.preferredWidth: 30
                                    Layout.preferredHeight: 30
                                }

                                CircularIndicator {success: manifest.is_valid_file(manifest.aoi)}

                                Text { 
                                    text: "Areas of Interest (.json)"
                                    font.bold: true
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: manifest.aoi
                                    horizontalAlignment: Text.AlignHCenter
                                    clip: true
                                }
                                Button {
                                    text: "..."
                                    onClicked: dialogAoi.open();
                                    Layout.preferredWidth: 30
                                    Layout.preferredHeight: 30
                                }

                                CircularIndicator {success: manifest.is_valid_notes_dir(manifest.notes)}
                                Text { 
                                    text: "Notes"
                                    font.bold: true
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: manifest.notes
                                    horizontalAlignment: Text.AlignHCenter
                                    clip: true
                                }
                                Button {
                                    text: "..."
                                    onClicked: dialogNotes.open();
                                    Layout.preferredWidth: 30
                                    Layout.preferredHeight: 30
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

                            GridLayout {
                                columns: 4
                                anchors.fill: parent

                                CircularIndicator {success: manifest.is_valid_file(manifest.video_workspace)}
                                Text { 
                                    text: "Workspace Video (.mp4)"
                                    font.bold: true
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: manifest.video_workspace
                                    horizontalAlignment: Text.AlignHCenter
                                    clip: true
                                }
                                Button {
                                    text: "..."
                                    onClicked: dialogVideoWorkspace.open();
                                    Layout.preferredWidth: 30
                                    Layout.preferredHeight: 30
                                }

                                CircularIndicator {success: manifest.is_valid_file(manifest.video_side)}
                                Text { 
                                    text: "Side Video (.mp4)"
                                    font.bold: true
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: manifest.video_side
                                    horizontalAlignment: Text.AlignHCenter
                                    clip: true
                                }
                                Button {
                                    text: "..."
                                    Layout.preferredWidth: 30
                                    Layout.preferredHeight: 30
                                    onClicked: dialogVideoSide.open();
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
                                    delegate: GroupBox {
                                        id: groupRec

                                        required property string recId
                                        required property string role
                                        required property string sourceGaze
                                        required property int index
                                        required property var model

                                        Layout.fillWidth: true
                                        Layout.fillHeight: true

                                        Layout.minimumWidth: contentWidth

                                        Layout.horizontalStretchFactor: 1

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
                                            
                                            onRejected: {
                                            }
                                        }

                                        background: Rectangle {
                                            y: groupRec.topPadding - groupRec.bottomPadding
                                            width: parent.width
                                            height: parent.height - groupRec.topPadding + groupRec.bottomPadding
                                            color: "transparent"
                                            border.color: "#aaa"
                                            radius: 3
                                        }

                                        label: RowLayout {
                                            height: 10
                                            width: parent.width

                                            Button {
                                                flat: true
                                                Layout.preferredWidth: 30
                                                height: parent.height
                                                icon.source: "../icons/trash.png"
                                                icon.color: "transparent"
                                                onClicked: {
                                                    manifest.recordings.removeRow(index)
                                                }
                                            }
                                            Button {
                                                flat: true
                                                Layout.preferredWidth: 30
                                                height: parent.height
                                                icon.source: "../icons/pen.png"
                                                icon.color: "transparent"
                                                onClicked: {
                                                    editRecIdDialog.open()
                                                }
                                            }
                                            Text {
                                                text: recId
                                                verticalAlignment: Text.AlignVCenter
                                                horizontalAlignment: Text.AlignLeft
                                                height: parent.height
                                                font.pixelSize: 16
                                                Layout.fillWidth: true
                                            }
                                        }

                                        GridLayout {
                                            anchors.fill: parent

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
                                            ComboBox {
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

                                            CircularIndicator {success: manifest.is_valid_file(manifest.video_workspace)}

                                            Text { 
                                                text: "Fixations"
                                                font.bold: true
                                            }

                                            Text {
                                                Layout.fillWidth: true
                                                Layout.minimumWidth: 150
                                                text: sourceGaze
                                                horizontalAlignment: Text.AlignHCenter
                                                clip: true
                                            }

                                            Button {
                                                text: "..."
                                                onClicked: dialogFixations.open()
                                                Layout.preferredWidth: 30
                                                Layout.preferredHeight: 30
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Button {
                            text: "New recording"
                            onClicked: {
                                manifest.recordings.add_new('', manifest.participant_roles[0]);
                            }
                        }
                    }
                }
            }
            ColumnLayout {
                id: transcriptTab

                property string currStdOut: "file:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of null\nfile:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of null\nfile:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of nullfile:///D:/Projects/reCAPit/frontend/windows/ManifestWindow.qml:528: TypeError: Cannot read property 'video_workspace' of null\n";

                GroupBox {
                    Layout.fillWidth: true

                    title: "Transcript"

                    GridLayout {
                        anchors.fill: parent
                        columns: 3
                        rowSpacing: 15
                        columnSpacing: 15

                        Text {
                            text: "Generate Transcript"
                            font.bold: true
                        }

                        ProgressBar {
                            Layout.fillWidth: true
                            id: transcriptRunningIndicator
                            indeterminate: false
                            value: 1.0
                        }

                        Connections {
                            target: preprocessingPipeline
                            function onTranscriptGlobalCompleted(returnCode) { 
                                transcriptRunningIndicator.indeterminate = false;
                            }
                            function onTranscriptRecordingCompleted(returnCode) { 
                                transcriptRunningIndicator2.indeterminate = false;
                            }
                        }

                        Button {
                            Layout.preferredHeight: 25
                            text: "Run"
                            enabled: !preprocessingPipeline.pipeline_running && preprocessingPipeline.global_transcript_ready
                            onClicked: {
                                transcriptRunningIndicator.indeterminate = true;
                                transcriptTab.currStdOut = "";
                                preprocessingPipeline.run_transcript_global()
                            }
                        }

                        Text {
                            text: "Split Transcript"
                            font.bold: true
                        }

                        ProgressBar {
                            Layout.fillWidth: true
                            id: transcriptRunningIndicator2
                            indeterminate: false
                            value: 1.0
                        }

                        Button {
                            Layout.preferredHeight: 25
                            text: "Run"
                            enabled: !preprocessingPipeline.pipeline_running && preprocessingPipeline.recording_transcript_ready
                            onClicked: {
                                transcriptRunningIndicator2.indeterminate = true;
                                transcriptTab.currStdOut = "";
                                preprocessingPipeline.run_transcript_recording()
                            }
                        }

                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.maximumHeight: 300
                    Layout.bottomMargin: 25
                    Layout.topMargin: 5
                    
                    color: "#e8e8e8"
                    radius: 5

                    Connections {
                        target: preprocessingPipeline
                        function onStdOutLine(line) { 
                            transcriptTab.currStdOut += "\n" + line;
                        }
                    }

                    ScrollView {
                        anchors.fill: parent
                        anchors.margins: 10
                        Text {
                            width: parent.width
                            id: stdoutText
                            color: "#666"
                            text: transcriptTab.currStdOut;
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }

        /*
        Row {
            Layout.margins: 20
            Button {
                text: "Confirm"
            }
        }
        */
    }
}
