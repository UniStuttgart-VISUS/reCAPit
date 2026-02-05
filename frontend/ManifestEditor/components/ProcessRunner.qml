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

GroupBox {
    id: root 

    property alias isRunning: progressBar.running
    property alias enabled: btn.enabled
    property string description
    property var pathInfo: ({path: "", is_valid: false, is_dir: false, file_extensions: [""]})
    property var requirements

    property var realParams: []
    property var selectionParams: []

    signal runTriggered()
    signal userPathChanged(string path)
    signal paramChanged(string name, var value)

    component RealParamComponent: RowLayout {
        required property var paramData

        Text {
            font.bold: true
            text: paramData.name
        }

        Slider {
            id: paramSlider
            from: paramData.from
            to: paramData.to
            stepSize: paramData.stepSize
            onMoved: {
                paramChanged(paramData.name, paramSlider.value)
            }
        }

        Text {
            text: "%1 %2".arg(paramSlider.value).arg(paramData.unit)
        }

    }

    component SelectionParamComponent: RowLayout {
        required property var paramData

        Text {
            text: paramData.name
        }

        CustomComboBox {
            id: paramSlider
            model: paramData.options

            onActivated: {
                paramChanged(paramData.name, currentText)
            }
        }
    }

    label: GridLayout {
        x: root.leftPadding
        width: root.availableWidth
        rowSpacing: 5
        columnSpacing: 10
        columns: 3

        CustomButton {
            Layout.row: 0
            Layout.column: 0

            id: btn
            text: "Run"
            onClicked: {
                root.runTriggered();
            }
        }

        Text {
            Layout.row: 0
            Layout.column: 1

            Layout.fillWidth: true
            horizontalAlignment: Text.AlignLeft
            text: root.title
            font.pixelSize: 16
        }

        Text {
            Layout.row: 1
            Layout.column: 0
            Layout.columnSpan: 2

            text: " 🛈 " + root.description
            height: parent.height
            font.pixelSize: 12
            color: "#aaa"
            verticalAlignment: Text.AlignBottom 
        }

        BusyIndicator  {
            id: progressBar
            Layout.row: 0
            Layout.column: 2
            Layout.columnSpan: 1
            Layout.rowSpan: 2
            running: false
        }
    }

    ColumnLayout {
        spacing: 10

        anchors.fill: parent

        UserFileInput {
            Layout.fillWidth: true
            name: "File path"
            path: root.pathInfo.path
            valid: root.pathInfo.is_valid
            isDir: root.pathInfo.is_dir
            fileExtensions: root.pathInfo.file_extensions ?? [""]
            onUserPathChanged: (newPath) => {
                root.userPathChanged(newPath);
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "Requirements"
                font.bold: true
            }

            Repeater {
                Layout.fillWidth: true
                model: root.requirements

                delegate: Rectangle {
                    id: rect
                    required property var modelData
                    color: "#eee"
                    radius: 10

                    width: rectRow.implicitWidth * 1.25
                    height: rectRow.implicitHeight * 1.25

                    Row {
                        anchors.centerIn: parent
                        id: rectRow
                        spacing: 10

                        Rectangle {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 10
                            height: 10
                            radius: 10
                            color: modelData.satisfies ? "#0f0" : "#f00"
                        }

                        Text {
                            text: modelData.name
                        }
                    }
                }
            }
        }

        GroupBox {
            Layout.fillWidth: true
            visible: root.realParams.length + root.selectionParams.length > 0

            title: "Parameters"
            ColumnLayout {
                anchors.fill: parent
                Repeater {
                    Layout.fillWidth: true
                    model: root.realParams

                    delegate: RealParamComponent {
                        required property var modelData
                        paramData: modelData
                    }
                }
                Repeater {
                    Layout.fillWidth: true
                    model: root.selectionParams

                    delegate: SelectionParamComponent {
                        required property var modelData
                        paramData: modelData
                    }
                }
            }
        }
    }
}
