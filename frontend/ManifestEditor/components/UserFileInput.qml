import QtQuick 2.15
import QtQuick.Layouts
import QtQuick.Shapes 1.2
import QtQuick.Dialogs
import QtQuick.Controls.Basic
import QtQml

RowLayout {
    property alias name: nameText.text
    property alias path: pathText.text
    property alias valid: indicator.success
    property bool isDir: false
    property list<string> fileExtensions: [""]

    spacing: 10

    signal userPathChanged(string newPath)

    FileDialog {
        id: dialogFile
        onAccepted: {
            const path = new URL(selectedFile).pathname.slice(1);
            userPathChanged(path);
        }
        nameFilters: fileExtensions
    }

    FolderDialog {
        id: dialogFolder
        onAccepted: {
            const path = new URL(selectedFolder).pathname.slice(1);
            userPathChanged(path);
        }
    }

    Rectangle {
        id: indicator
        property bool success: false

        width: 10
        height: 10
        radius: 10
        color: success ? "#0f0" : "#f00"
    }

    Text { 
        id: nameText
        font.bold: true
    }

    Text {
        id: pathText
        Layout.fillWidth: true
        text: manifest.aoi
        horizontalAlignment: Text.AlignHCenter
        clip: true
    }
    Button {
        text: "..."
        onClicked: isDir ? dialogFolder.open() : dialogFile.open()
        Layout.preferredWidth: 30
        Layout.preferredHeight: 30

        background: Rectangle {
            color: "white"
            radius: 2
        }
    }
}
