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
    property var requirements
    property var output

    property var realParams: []
    property var selectionParams: []
    property var boolParams: []
    property var intParams: []
    property var textParams: []

    signal runTriggered()
    signal paramChanged(string name, var value)

    clip: true

    component PillComponent: Rectangle {
        required property string title
        required property bool satisfied

        color: "#eee"
        radius: 10

        width: rectRow.implicitWidth * 1.25
        height: rectRow.implicitHeight * 1.25

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            hoverEnabled: true
        }

        ToolTip.visible: mouseArea.containsMouse
        ToolTip.text: satisfied ? qsTr("OK"): qsTr("This requirement is not satisfied")

        Row {
            anchors.centerIn: parent
            id: rectRow
            spacing: 10

            Rectangle {
                anchors.verticalCenter: parent.verticalCenter
                width: 10
                height: 10
                radius: 10
                color: satisfied ? "#0f0" : "#f00"
            }

            Text {
                text: title
            }
        }
    }

    component RealParamComponent: RowLayout {
        required property var paramData

        Text {
            Layout.preferredWidth: 200
            font.bold: true
            text: paramData.name
        }

        Slider {
            Layout.fillWidth: true
            id: paramSlider
            from: paramData.from
            to: paramData.to
            stepSize: paramData.stepSize
            value: paramData.value

            onMoved: {
                paramChanged(paramData.id, paramSlider.value)
            }
        }
        Text {
            text: "%1 %2".arg(paramSlider.value).arg(paramData.unit)
        }
    }

    component TextInputParamComponent: RowLayout {
        required property var paramData

        Text {
            Layout.preferredWidth: 200
            font.bold: true
            text: paramData.name
        }

        TextField {
            id: paramTextField
            inputMask: paramData.inputMask
            Layout.fillWidth: true
            text: paramData.value

            onEditingFinished: {
                paramChanged(paramData.id, text)
            }
        }
    }

    component SelectionParamComponent: RowLayout {
        required property var paramData

        Text {
            Layout.preferredWidth: 200
            font.bold: true
            text: paramData.name
        }

        CustomComboBox {
            id: paramSlider
            model: paramData.options
            Layout.fillWidth: true
            currentIndex: paramData.options.indexOf(paramData.value)

            onActivated: {
                paramChanged(paramData.id, currentText)
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

    contentItem: ColumnLayout {
        spacing: 10
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "Input"
                font.bold: true
            }

            Repeater {
                Layout.fillWidth: true
                model: root.requirements

                delegate: PillComponent {
                    required property var modelData
                    title: modelData.name
                    satisfied: modelData.exists
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "Output"
                font.bold: true
            }

            Repeater {
                Layout.fillWidth: true
                model: root.output

                delegate: PillComponent {
                    required property var modelData
                    title: modelData.name
                    satisfied: modelData.exists
                }
            }
        }

        GroupBox {
            Layout.fillWidth: true
            visible: root.realParams.length + root.selectionParams.length > 0

            title: "Parameters"
            ColumnLayout {
                width: parent.width
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
                    model: root.intParams

                    delegate: RealParamComponent {
                        required property var modelData
                        paramData: modelData
                    }
                }
                Repeater {
                    Layout.fillWidth: true
                    model: root.textParams

                    delegate: TextInputParamComponent {
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
                Repeater {
                    Layout.fillWidth: true
                    model: root.boolParams

                    delegate: SelectionParamComponent {
                        required property var modelData
                        paramData: Object.assign({}, modelData, {options: ["yes", "no"]})
                    }
                }
            }
        }
    }
}
