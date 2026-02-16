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

    signal actionRequested(int action)

    Menu {
        title: qsTr("&File")

        Action { 
            text: qsTr("&Restore state...") 
            shortcut: StandardKey.Open
            onTriggered: {
                root.actionRequested(Constants.AppActions.LoadState);
            }
        }

        Action { 
            text: qsTr("&Save state") 
            shortcut: StandardKey.Save
            onTriggered: {
                root.actionRequested(Constants.AppActions.SaveState);
            }
        }

        Action { 
            text: qsTr("&Export bookmarked") 
            onTriggered: {
                root.actionRequested(Constants.AppActions.ExportBookmarked);
            }
        }

        Action { 
            text: qsTr("&Open Project") 
            onTriggered: {
                root.actionRequested(Constants.AppActions.OpenProject);
            }
        }

        MenuSeparator { }

        Action { 
            text: qsTr("&Preferences") 
            shortcut: StandardKey.Preferences
            onTriggered: {
                root.actionRequested(Constants.AppActions.OpenPreferences);
            }
        }
        MenuSeparator { }
        Action { 
            text: qsTr("&Quit") 
            shortcut: StandardKey.Quit
            onTriggered: {
                root.actionRequested(Constants.AppActions.Quit);
            }
        }
    }
    Menu {
        title: qsTr("&Edit")
        Action { 
            text: qsTr("Find")
            shortcut: StandardKey.Find
            onTriggered: {
                root.actionRequested(Constants.AppActions.Search);
            }
        }
    }
    Menu {
        title: qsTr("&View")
        Action { 
            text: qsTr("Scale up") 
            shortcut: StandardKey.ZoomIn
            onTriggered: {
                root.actionRequested(Constants.AppActions.ScaleUp);
            }
        }
        Action { 
            text: qsTr("Scale down") 
            shortcut: StandardKey.ZoomOut
            onTriggered: {
                root.actionRequested(Constants.AppActions.ScaleDown);
            }
        }
        Action { 
            text: qsTr("Reset") 
            shortcut: StandardKey.Refresh
            onTriggered: {
                root.actionRequested(Constants.AppActions.Reset);
            }
        }
    }
    Menu {
        title: qsTr("&Help")
        Action { 
            text: qsTr("&About") 
            onTriggered: {
                root.actionRequested(Constants.AppActions.OpenAbout);
            }
        }
    }

    background: Rectangle {
        implicitWidth: 40
        implicitHeight: 30
        color: "#f8f8f8"
    }
}

