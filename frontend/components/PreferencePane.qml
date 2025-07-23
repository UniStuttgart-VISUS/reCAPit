import QtQuick 2.15
import QtQuick.Controls.Basic
import QtQuick.Layouts 2.15

Window {
    id: preferencePane
    property int currentIndex: 0
    property var userConfig

    readonly property var categoricalColormaps: ["Set1", "Set2", "Set3", "Paired", "Accent", "Tableau10", "Category10", "Observable10", "Purple6"]
    readonly property var linearContColormaps: ["CET-L14","CET-L15","CET-L16","CET-L17","CET-L18","CET-L19","CET-L20"]

    signal saveCurrentUserConfig(user_config: var)

    function currentUserConfig() {
        var user_config = preferencePane.userConfig;
        user_config["multisampling"] = sliderMSAA.value;
        user_config["colormaps"]["areas_of_interests"] =  categoricalColormaps[cmapAOIs.currentIndex];
        user_config["colormaps"]["roles"] =  categoricalColormaps[cmapRoles.currentIndex];
        return user_config;
    }

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
                    */
                    VerticalTabButton {
                        width: 150
                        height: 35
                        text: "Streamgraphs"
                        checked: currentIndex === 3
                        onClicked: currentIndex = 3
                    }
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
                                    
                                    contentItem: Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        
                                        Image {
                                            width: 40
                                            height: 20
                                            fillMode: Image.Stretch
                                            source: parent.parent.currentText ? "icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
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
                                Label { 
                                    text: "Areas of Interests:" 
                                    Layout.preferredWidth: 100
                                }
                                ComboBox  {
                                    id: cmapAOIs
                                    Layout.preferredWidth: 250
                                    model: preferencePane.categoricalColormaps
                                    currentIndex:preferencePane.categoricalColormaps.indexOf(categoriesGroup.colormaps["areas_of_interests"])
                                    
                                    contentItem: Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        
                                        Image {
                                            width: 40
                                            height: 20
                                            fillMode: Image.Stretch
                                            source: parent.parent.currentText ? "icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
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
                            Layout.preferredWidth: 500
                            title: "Video Overlays"

                            GridLayout {
                                anchors.fill: parent
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 5

                                Label { 
                                    Layout.preferredWidth: 100
                                    text: "Attention:" 
                                }
                                ComboBox  {
                                    id: comboAttention
                                    Layout.preferredWidth: 250
                                    model: preferencePane.linearContColormaps
                                    
                                    contentItem: Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        
                                        Image {
                                            width: 40
                                            height: 20
                                            fillMode: Image.Stretch
                                            source: parent.parent.currentText ? "icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
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
                                Label { 
                                    Layout.preferredWidth: 100
                                    text: "Movement:" 
                                }
                                ComboBox  {
                                    id: comboMovement
                                    Layout.preferredWidth: 250
                                    model: preferencePane.linearContColormaps
                                    
                                    contentItem: Row {
                                        anchors.left: parent.left
                                        anchors.leftMargin: 10
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 8
                                        
                                        Image {
                                            width: 40
                                            height: 20
                                            fillMode: Image.Stretch
                                            source: parent.parent.currentText ? "icons/colormaps/%1.png".arg(parent.parent.currentText) : ""
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
                                    to: 120
                                    stepSize: 5
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
                                    to: 120
                                    stepSize: 5
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
                    preferencePane.saveCurrentUserConfig(preferencePane.currentUserConfig());
                }
            }
        }
    }
}
