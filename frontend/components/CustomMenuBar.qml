import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Dialogs
import QtQuick.Shapes 1.2
import QtQml
import QtQuick.Controls.Basic

import "."

MenuBar {
    id: root

    signal openAboutWindow()
    signal openPreferenceWindow()

    MessageDialog {
        id: successDialog
        buttons: MessageDialog.Ok
    }

    FolderDialog {
        id: exportBookmarkedDialog
        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "")
            const success = topicSegments.export_bookmarked(dir_path)

            successDialog.title = "Export bookmarked segments";

            if (success) {
                successDialog.text = "Successfully exported bookmarked segments!";
            }
            else {
                successDialog.text = "Failed to export bookmarked segments to %1".arg(dir_path);
            }
            successDialog.open();
        }
    }

    FolderDialog {
        id: saveDialog
        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "")
            const success = topicSegments.export_state(dir_path)

            successDialog.title = "Save state";

            if (success) {
                successDialog.text = "Successfully saved state!";
            }
            else {
                successDialog.text = "Failed to save state to %1".arg(dir_path);
            }
            successDialog.open();
        }
    }

    FolderDialog {
        id: loadDialog
        currentFolder: aoiModel.ExportDir()
        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "")
            const success = topicSegments.import_state(dir_path)

            successDialog.title = "Restore State";

            if (success) {
                successDialog.text = "Successfully loaded state!";
            }
            else {
                successDialog.text = "Failed to load state from %1".arg(dir_path);
            }
            successDialog.open();
        }
    }

    Menu {
        title: qsTr("&File")

        Action { 
            text: qsTr("&Restore state...") 
            shortcut: StandardKey.Open
            onTriggered: {
                loadDialog.open();
            }
        }

        Action { 
            text: qsTr("&Save state") 
            shortcut: StandardKey.Save
            onTriggered: {
                saveDialog.open();
            }
        }

        Action { 
            text: qsTr("&Export bookmarked") 
            onTriggered: {
                exportBookmarkedDialog.open();
            }
        }

        Action { 
            text: qsTr("&Open Project") 
            onTriggered: {
                projectManager.open_manager();
                appwin.close();
            }
        }

        MenuSeparator { }
        Action { 
            text: qsTr("&Restore state...") 
            shortcut: StandardKey.Open
            onTriggered: {
                loadDialog.open();
            }
        }

        Action { 
            text: qsTr("&Save state") 
            shortcut: StandardKey.Save
            onTriggered: {
                saveDialog.open();
            }
        }

        MenuSeparator { }

        Action { 
            text: qsTr("&Preferences") 
            shortcut: StandardKey.Preferences
            onTriggered: {
                root.openPreferenceWindow();
            }
        
        }
        MenuSeparator { }
        Action { 
            text: qsTr("&Quit") 
            shortcut: StandardKey.Quit
            onTriggered: {
                appwin.close();
            }
        }
    }
    Menu {
        title: qsTr("&Edit")
        Action { 
            text: qsTr("Find")
            shortcut: StandardKey.Find
            onTriggered: {
                keywordDialog.open();
            }
        }
    }
    Menu {
        title: qsTr("&View")
        Action { 
            text: qsTr("Scale up") 
            shortcut: StandardKey.ZoomIn
            onTriggered: {
                scroll.contentWidth *= 1.5;
                appwin.reset();
            }
        }
        Action { 
            text: qsTr("Scale down") 
            shortcut: StandardKey.ZoomOut
            onTriggered: {
                scroll.contentWidth /= 1.5;
                appwin.reset();
            }
        }
        Action { 
            text: qsTr("Reset") 
            shortcut: StandardKey.Refresh
            onTriggered: {
                for (var i = 0; i < cardsRoot.children.length; ++i) {
                    const idx = cardsRoot.children[i].cardData.SegmentIndex();
                    cardsRoot.children[i].opacity = 1.0;
                }
            }
        }
    }
    Menu {
        title: qsTr("&Help")
        Action { 
            text: qsTr("&About") 
            onTriggered: {
                root.openAboutWindow();
            }
        }
    }

    background: Rectangle {
        implicitWidth: 40
        implicitHeight: 30
        color: "#f8f8f8"
    }
}

