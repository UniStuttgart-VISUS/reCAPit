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

ScrollView {
    required property string targetScriptDir

    contentWidth: availableWidth
    contentHeight: videoTab.implicitHeight

    ColumnLayout {
        id: videoTab
        width: parent.width

        Repeater {
            model: preprocessingPipeline.get_scripts_model()
            delegate: ProcessRunner {
                Layout.fillWidth: true

                required property string scriptTitle
                required property string scriptDescription
                required property var scriptRealParams
                required property var scriptIntParams
                required property var scriptBoolParams
                required property var scriptSelectionParams
                required property var scriptTextParams
                required property var scriptDependencies
                required property bool scriptDependenciesSatisfied
                required property bool scriptRunning
                required property var scriptOutput
                required property int index
                required property string scriptTarget
                required property string scriptDir

                visible: scriptDir === targetScriptDir

                id: videoMovementRunner
                title: scriptTitle
                description: scriptDescription
                requirements: [...scriptDependencies.sources, ...scriptDependencies.artifacts]
                output: [...scriptOutput.sources, ...scriptOutput.artifacts]

                realParams: scriptRealParams
                intParams: scriptIntParams
                selectionParams: scriptSelectionParams
                boolParams: scriptBoolParams
                textParams: scriptTextParams

                isRunning: scriptRunning
                enabled: scriptDependenciesSatisfied && !(scriptRunning || preprocessingPipeline.pipeline_running)

                onRunTriggered: {
                    preprocessingPipeline.run_script(index);
                }
                onParamChanged: (arg_id, arg_value) => {
                    preprocessingPipeline.get_scripts_model().set_script_arg(index, arg_id, arg_value);
                }
            }
        }
    }
}