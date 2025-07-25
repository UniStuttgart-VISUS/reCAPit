import "../components"
import "../components/colorschemes.js" as Colorschemes

import QtQuick 2.15
import QtQuick.Controls.Basic
import QtQuick.Layouts 2.15

Window {
    id: preferencePane
    property int currentIndex: 0
    property var userConfig

    readonly property var categoricalColormaps: Object.keys(Colorschemes.CATEGORICAL)
    readonly property var linearContColormaps: Colorschemes.CONTINUOUS

    signal saveCurrentUserConfig(user_config: var)

    ColumnLayout {
        anchors.fill: parent

        Row {
            Layout.fillHeight: true
            Layout.fillWidth: true
            spacing: 10

            Column {
                spacing: 0
                Column {
                    width: 150
                    spacing: 0

                    VerticalTabButton {
                        width: 150
                        height: 35
                        text: "General"
                        checked: currentIndex === 0
                        onClicked: currentIndex = 0
                    }
                    VerticalTabButton {
                        width: 150
                        height: 35
                        text: "Colormaps"
                        checked: currentIndex === 1
                        onClicked: currentIndex = 1
                    }
                    VerticalTabButton {
                        width: 150
                        height: 35
                        text: "Segmentation"
                        checked: currentIndex === 2
                        onClicked: currentIndex = 2
                    }
                    /*
                    VerticalTabButton {
                        width: 150
                        height: 35
                        text: "Timelines"
                        checked: currentIndex === 3
                        onClicked: currentIndex = 3
                    }
                    VerticalTabButton {
                        width: 150
                        height: 35
                        text: "Streamgraphs"
                        checked: currentIndex === 3
                        onClicked: currentIndex = 3
                    }
                    */
                }
            }

            // Tab content
            StackLayout {
                currentIndex: preferencePane.currentIndex
                width: parent.width - 150
                height: parent.height

                Rectangle {
                    color: "#f4f4f4"
                    radius: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Label {
                            font.pixelSize: 24
                            font.capitalization: Font.Capitalize
                            text: "General"
                            color: "#333"
                        }
                        GridLayout {
                            columns: 3
                            columnSpacing: 10
                            rowSpacing: 5

                            Label { 
                                text: "MSAA:" 
                                Layout.preferredWidth: 100
                            }
                            Slider  {
                                id: sliderMSAA
                                Layout.preferredWidth: 250
                                snapMode: Slider.SnapAlways
                                live: true
                                from: 1
                                value: preferencePane.userConfig["multisampling"]
                                to: 8
                                stepSize: 1

                                onMoved: {
                                    preferencePane.userConfig["multisampling"] = sliderMSAA.value;
                                }
                            }
                            Label { 
                                text: "%1x".arg(sliderMSAA.value)
                                Layout.preferredWidth: 100
                            }
                        }
                        Item {
                            Layout.fillHeight: true
                        }
                    }
                }

                Rectangle {
                    color: "#f4f4f4"
                    radius: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Label {
                            font.pixelSize: 24
                            font.capitalization: Font.Capitalize
                            text: "Colormaps"
                            color: "#333"
                        }

                        GroupBox {
                            id: categoriesGroup

                            title: "Categories"
                            Layout.preferredWidth: 400

                            property var colormaps: preferencePane.userConfig["colormaps"]

                            GridLayout {
                                anchors.fill: parent
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 5

                                Label { 
                                    text: "Roles:" 
                                    Layout.preferredWidth: 100
                                }
                                ComboBox  {
                                    id: cmapRoles
                                    Layout.preferredWidth: 250
                                    model: preferencePane.categoricalColormaps
                                    currentIndex:preferencePane.categoricalColormaps.indexOf(categoriesGroup.colormaps["roles"])

                                    onActivated: (index) => {
                                        preferencePane.userConfig["colormaps"]["roles"] =  categoricalColormaps[cmapRoles.currentIndex];
                                    }
                                    
                                    contentItem: Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        
                                        Image {
                                            width: 40
                                            height: 20
                                            fillMode: Image.Stretch
                                            source: parent.parent.currentText ? "../icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        
                                        Text {
                                            text: parent.parent.currentText
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: "#000000"
                                        }
                                    }
                                    
                                    delegate: ItemDelegate {
                                        width: parent.width
                                        height: 35
                                        
                                        Row {
                                            anchors.left: parent.left
                                            anchors.leftMargin: 10
                                            anchors.verticalCenter: parent.verticalCenter
                                            spacing: 8
                                            
                                            Image {
                                                width: 40
                                                height: 20
                                                fillMode: Image.Stretch
                                                source: "../icons/colormaps/%1.png".arg(modelData)
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                            
                                            Text {
                                                text: modelData
                                                anchors.verticalCenter: parent.verticalCenter
                                                color: parent.parent.highlighted ? "#ffffff" : "#000000"
                                            }
                                        }
                                        
                                        background: Rectangle {
                                            color: parent.highlighted ? "#0078d4" : "transparent"
                                        }
                                    }
                                }
                                Label { 
                                    text: "Areas of Interests:" 
                                    Layout.preferredWidth: 100
                                }
                                ComboBox  {
                                    id: cmapAOIs
                                    Layout.preferredWidth: 250
                                    model: preferencePane.categoricalColormaps
                                    currentIndex:preferencePane.categoricalColormaps.indexOf(categoriesGroup.colormaps["areas_of_interests"])

                                    onActivated: (index) => {
                                        preferencePane.userConfig["colormaps"]["areas_of_interests"] =  categoricalColormaps[cmapAOIs.currentIndex];
                                    }
                                    
                                    contentItem: Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        
                                        Image {
                                            width: 40
                                            height: 20
                                            fillMode: Image.Stretch
                                            source: parent.parent.currentText ? "../icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        
                                        Text {
                                            text: parent.parent.currentText
                                            anchors.verticalCenter: parent.verticalCenter
                                            color: "#000000"
                                        }
                                    }
                                    
                                    delegate: ItemDelegate {
                                        width: parent.width
                                        height: 35
                                        
                                        Row {
                                            anchors.left: parent.left
                                            anchors.leftMargin: 10
                                            anchors.verticalCenter: parent.verticalCenter
                                            spacing: 8
                                            
                                            Image {
                                                width: 40
                                                height: 20
                                                fillMode: Image.Stretch
                                                source: "icons/colormaps/%1.png".arg(modelData)
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                            
                                            Text {
                                                text: modelData
                                                anchors.verticalCenter: parent.verticalCenter
                                                color: parent.parent.highlighted ? "#ffffff" : "#000000"
                                            }
                                        }
                                        
                                        background: Rectangle {
                                            color: parent.highlighted ? "#0078d4" : "transparent"
                                        }
                                    }
                                }
                            }
                        }
                        GroupBox {
                            id: overlaysGroup
                            Layout.preferredWidth: 500
                            title: "Video Overlays"
                            property var colormaps: preferencePane.userConfig["video_overlay"]

                            ColumnLayout {
                                anchors.fill: parent
                                spacing: 10

                                Repeater {
                                    model: Object.keys(overlaysGroup.colormaps)
                                    delegate: Column {
                                        required property string modelData;
                                        spacing: 10

                                        Label { 
                                            width: 100
                                            text: modelData
                                        }
                                        ComboBox  {
                                            id: comboAttention
                                            width: 250
                                            model: preferencePane.linearContColormaps
                                            currentIndex: preferencePane.linearContColormaps.indexOf(overlaysGroup.colormaps[modelData]["colormap"])

                                            onActivated: (index) => {
                                                preferencePane.userConfig["video_overlay"][modelData]["colormap"] = linearContColormaps[index];
                                                console.log("OK");
                                            }
                                            
                                            contentItem: Row {
                                                anchors.left: parent.left
                                                anchors.leftMargin: 10
                                                anchors.verticalCenter: parent.verticalCenter
                                                spacing: 5
                                                
                                                Image {
                                                    width: 40
                                                    height: 20
                                                    fillMode: Image.Stretch
                                                    source: parent.parent.currentText ? "../icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
                                                    anchors.verticalCenter: parent.verticalCenter
                                                }
                                                
                                                Text {
                                                    text: parent.parent.currentText
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    color: "#000000"
                                                }
                                            }
                                            
                                            delegate: ItemDelegate {
                                                width: parent.width
                                                height: 35
                                                
                                                Row {
                                                    anchors.left: parent.left
                                                    anchors.leftMargin: 10
                                                    anchors.verticalCenter: parent.verticalCenter
                                                    spacing: 8
                                                    
                                                    Image {
                                                        width: 40
                                                        height: 20
                                                        fillMode: Image.Stretch
                                                        source: "../icons/colormaps/%1.png".arg(modelData)
                                                        anchors.verticalCenter: parent.verticalCenter
                                                    }
                                                    
                                                    Text {
                                                        text: modelData
                                                        anchors.verticalCenter: parent.verticalCenter
                                                        color: parent.parent.highlighted ? "#ffffff" : "#000000"
                                                    }
                                                }
                                                
                                                background: Rectangle {
                                                    color: parent.highlighted ? "#0078d4" : "transparent"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Item {
                            Layout.fillHeight: true
                        }
                    }
                }

                Rectangle {
                    color: "#f4f4f4"
                    radius: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Label {
                            font.pixelSize: 24
                            font.capitalization: Font.Capitalize
                            text: "Segmentation"
                            color: "#333"
                        }
                        GroupBox {
                            Layout.preferredWidth: 600
                            title: "Filter"
                            GridLayout {
                                columns: 3
                                columnSpacing: 10
                                rowSpacing: 5

                                Label { 
                                    text: "Minimum Duration:" 
                                    Layout.preferredWidth: 100
                                }
                                Slider  {
                                    id: sliderMinDur
                                    Layout.preferredWidth: 250
                                    live: true
                                    from: 1
                                    value: 30
                                    to: 180
                                    stepSize: 5

                                    onMoved: {
                                        preferencePane.userConfig["segments"]["min_dur_sec"] =  sliderMinDur.value;
                                    }
                                }
                                DataLabel {
                                    text: "%1 sec.".arg(sliderMinDur.value)
                                }

                                Label { 
                                    text: "Expanded Duration:" 
                                    Layout.preferredWidth: 100
                                }
                                Slider  {
                                    id: sliderExp
                                    Layout.preferredWidth: 250
                                    live: true
                                    from: 1
                                    value: 45
                                    to: 180
                                    stepSize: 5
                                    onMoved: {
                                        preferencePane.userConfig["segments"]["display_dur_sec"] =  sliderExp.value;
                                    }
                                }
                                DataLabel {
                                    text: "%1 sec.".arg(sliderExp.value)
                                }
                            }
                        }
                        Item {
                            Layout.fillHeight: true
                        }
                    }
                }


                Rectangle {
                    color: "#f4f4f4"
                    radius: 2

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10

                        Label {
                            font.pixelSize: 24
                            font.capitalization: Font.Capitalize
                            text: "Streamgraphs"
                            color: "#333"
                        }

                        GroupBox {
                            title: "Top"
                            GridLayout {
                                anchors.fill: parent
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 5

                                Label { text: "Source:" }
                                ComboBox  {
                                    Layout.preferredWidth: 150
                                    flat: true
                                    model: ["attention", "movement", "other"]
                                }
                                Label { text: "Log scale:" }
                                Switch  {
                                    checked: true
                                }
                            }
                        }
                        GroupBox {
                            title: "Bottom"
                            GridLayout {
                                anchors.fill: parent
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 5

                                Label { text: "Source:" }
                                ComboBox  {
                                    Layout.preferredWidth: 150
                                    flat: true
                                    model: ["attention", "movement", "other"]
                                }
                                Label { text: "Log scale:" }
                                Switch  {
                                    Layout.preferredHeight: 10
                                    checked: true
                                }
                            }
                        }
                        Item {
                            Layout.fillHeight: true
                        }
                    }
                }

                /*
                Rectangle {
                    color: "#f4f4f4"
                    radius: 2
                    Label {
                        anchors.centerIn: parent
                        text: "Content of Tab 4"
                    }
                }
                Rectangle {
                    color: "#f4f4f4"
                    radius: 2
                    Label {
                        anchors.centerIn: parent
                        text: "Content of Tab 5"
                    }
                }
                */
            }
        }
        Row {
            Layout.preferredHeight: 50
            Layout.fillWidth: true
            layoutDirection: Qt.RightToLeft

            spacing: 25
            padding: 10

            Button {
                anchors.verticalCenter: parent.verticalCenter
                text: "Close"
                height: 30
                onClicked: {
                    preferencePane.close();
                }
            }

            Button {
                anchors.verticalCenter: parent.verticalCenter
                text: "Save"
                height: 30
                onClicked: {
                    preferencePane.close();
                    preferencePane.saveCurrentUserConfig(preferencePane.userConfig);
                }
            }
        }
    }
}
