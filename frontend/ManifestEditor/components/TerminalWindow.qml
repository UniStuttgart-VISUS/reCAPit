import QtQuick 2.15
import QtQuick.Controls.Basic
import QtQuick.Layouts

Window {
    id: terminalWindow
    visible: true
    width: 500
    height: 300
    color: "#1e1e1e"
    title: "Process Output"

    property bool autoClose: false

    function appendLine(text, color) {
        outputModel.append({line: text, lineColor: color});
        // Auto-scroll to bottom
        Qt.callLater(function() {
            outputListView.positionViewAtEnd();
        });
    }

    function clear() {
        outputModel.clear();
    }

    ListModel {
        id: outputModel
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 5

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#0d0d0d"
            radius: 4
            border.color: "#333"
            border.width: 1

            ListView {
                id: outputListView
                anchors.fill: parent
                anchors.margins: 8
                model: outputModel
                clip: true
                spacing: 2

                delegate: Text {
                    required property string line
                    required property string lineColor

                    width: outputListView.width
                    text: line
                    textFormat: Text.StyledText
                    color: lineColor
                    font.family: "Consolas, 'Courier New', monospace"
                    font.pixelSize: 12
                    wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                }

                ScrollBar.vertical: ScrollBar {
                    active: true
                    policy: ScrollBar.AsNeeded
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Item {
                Layout.fillWidth: true
            }

            Button {
                id: closeButton
                text: "Close"
                onClicked: terminalWindow.close()
                
                background: Rectangle {
                    implicitWidth: 80
                    implicitHeight: 30
                    color: closeButton.down ? "#444" : "#555"
                    radius: 4
                }
                
                contentItem: Text {
                    text: closeButton.text
                    color: "#fff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }

    Connections {
        target: preprocessingPipeline
        function onStdOutLine(line) {
            terminalWindow.appendLine(line, "#0f0");
        }
        function onStdErrLine(line) {
            terminalWindow.appendLine(line, "#0f0");
        }
        function onRunningStatusChanged() {
            if (!preprocessingPipeline.pipeline_running && terminalWindow.autoClose) {
                // Add a small delay before closing so user can see final output
                closeTimer.start();
            }
        }
    }

    Timer {
        id: closeTimer
        interval: 2000  // 2 second delay before auto-close
        repeat: false
        onTriggered: {
            terminalWindow.close();
        }
    }
}
