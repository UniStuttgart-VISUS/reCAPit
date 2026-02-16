import QtQuick 2.15
import QtQml
import QtQuick.Controls.Basic

Item {
    enum AppState { Default, Search, Compressed }
    enum AppActions { LoadState, SaveState, ExportBookmarked, ScaleUp, ScaleDown, OpenProject, OpenPreferences, OpenAbout, Search, Reset, Quit }
}
