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
    id: videoTab

    Repeater {
        model: preprocessingPipeline.get_scripts_model()
        delegate: ProcessRunner {
            Layout.fillWidth: true

            required property string titleX
            required property string descriptionX
            required property var realParamsX
            required property var intParamsX
            required property var boolParamsX
            required property var selectionParamsX
            required property var dependenciesX
            required property bool dependenciesSatisfiedX
            required property bool isRunningX
            required property var outputX
            required property int index
            required property string scriptTarget

            id: videoMovementRunner
            title: titleX
            description: descriptionX
            requirements: [...dependenciesX.sources, ...dependenciesX.artifacts]
            output: [...outputX.sources, ...outputX.artifacts]

            realParams: realParamsX
            intParams: intParamsX
            selectionParams: selectionParamsX
            boolParams: boolParamsX

            isRunning: isRunningX
            enabled: dependenciesSatisfiedX && !(isRunningX || preprocessingPipeline.pipeline_running)

            onRunTriggered: {
                preprocessingPipeline.run_script(index);
            }

            onParamChanged: (arg_id, arg_value) => {
                preprocessingPipeline.get_scripts_model().set_script_arg(index, arg_id, arg_value);
            }
        }
    }
}