import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQuick.Effects

import "."
import "utils.js" as Utils

Item {
    id: topicCardRoot
    required property var cardData
    required property int segmentIndex
    required property int cardIndex
    required property var cmapAOI
    required property var cmapRole

    required property bool hasAttention
    required property bool hasActivity

    signal onClicked(targetIndex: int)
    signal onEntered(targetIndex: int)
    signal onMarkToggled(targetIndex: int)
    property bool marked : cardData.IsMarked()

    property alias color: matchIndicator.color
    property real score : -1


    ColumnLayout {
        spacing: 25
        height: 1200
        width: topicCardRoot.width

        Item {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop

            implicitHeight: 200 + containerRect.implicitHeight + containerRect2.implicitHeight + containerRect3.implicitHeight
            implicitWidth: containerRect.implicitWidth

            Rectangle {
                id: topicCard
                anchors.fill: parent
                y: 10
                radius: 15
                color: '#fafafa' 

                border.color: '#f4f4f4'
                border.width: 5

                MouseArea{
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true 
                    propagateComposedEvents: true

                    onClicked: (mouse) => {
                        topicCardRoot.onClicked(topicCardRoot.cardIndex);
                        if (mouse)
                            mouse.accepted = true;
                    }
                    onEntered: (mouse) => {
                        topicCard.border.width = 5;
                        topicCard.border.color = '#deb41d'
                        topicCardRoot.onEntered(topicCardRoot.segmentIndex);
                        if (mouse)
                            mouse.accepted = true;
                    }
                    onExited: (mouse) => {
                        topicCard.border.width = 5;
                        topicCard.border.color = '#f4f4f4'
                        if (mouse)
                            mouse.accepted = true;
                    }
                }

                function getPieData(labelDistr, cmap) {
                    var pieData = [];
                    var total = 0;

                    for (const [key, value] of Object.entries(labelDistr)) {
                        pieData.push({name: key, value: value, color: cmap.get(key)})
                        total += value;
                    }
                    if (total < 1) {
                        pieData.push({name: "rest", value: 1-total, color: "#fafafa"})
                    }
                    return pieData;
                }

                PieChart {
                    id: pieSpeakerTime
                    sourcePic: "icons/speech.png"
                    data: topicCard.getPieData(cardData.SpeakerTimeDistribution(), topicCardRoot.cmapRole)
                    width: 50; height: 50; x: topicCardRoot.width - 25; y: 50; z: 5
                }
                PieChart {
                    id: pieAoiActivity
                    sourcePic: "icons/move.png"
                    data: topicCard.getPieData(cardData.AoiActivityDistribution(), topicCardRoot.cmapAOI)
                    width: 50; height: 50; x: topicCardRoot.width - 25; y: 120; z: 5
                    visible: topicCardRoot.hasActivity
                }

                PieChart {
                    id: pieAoiAttention
                    sourcePic: "icons/eye.png"
                    data: topicCard.getPieData(cardData.AoiAttentionDistribution(), topicCardRoot.cmapAOI)
                    width: 50; height: 50; x: topicCardRoot.width - 25; y: 190; z: 5
                    visible: topicCardRoot.hasAttention
                }


                ColumnLayout {
                    spacing: 10

                    anchors.fill: parent

                    anchors.topMargin: 25
                    anchors.bottomMargin: 10
                    anchors.leftMargin: 30
                    anchors.rightMargin: 30

                    implicitHeight: containerRect.implicitHeight + containerRect2.implicitHeight
                    implicitWidth: containerRect.implicitWidth


                    // Title
                    Row {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80

                        spacing: 5

                        Image {
                            width: 30
                            height: 30

                            source: "icons/star.png"
                            opacity: topicCardRoot.marked ? 1 : 0.25

                            MouseArea{
                                anchors.fill: parent
                                onClicked: {
                                    topicCardRoot.marked = topicCardRoot.cardData.ToggleMark()
                                    //topicCardRoot.marked = !topicCardRoot.marked;
                                    topicCardRoot.onMarkToggled(topicCardRoot.segmentIndex);
                                }
                            }
                        }

                        Text {
                            id: topicCardTitle
                            width: parent.width - 30
                            color: "#000"
                            horizontalAlignment: Text.AlignHCenter
                            font.bold: true
                            font.pixelSize: 18
                            text: topicCardRoot.cardData.Title()
                            wrapMode: Text.Wrap
                            elide: Text.ElideRight
                        }
                    }

                    /*
                    Rectangle {
                        id: matchIndicator
                        Layout.fillWidth: true
                        Layout.preferredHeight: 30

                        visible: true
                        color: "#fff";
                        radius: 20

                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 5
                            anchors.rightMargin: 5

                            verticalAlignment: Text.AlignVCenter
                            horizontalAlignment: Text.AlignHCenter

                            color: "#000"
                            font.pixelSize: 16
                            font.bold: true
                            text: "Match: 78%"
                            wrapMode: Text.Wrap
                        }
                    }
                    */


                    /*
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        SwipeView {
                            id: view

                            currentIndex: 0
                            anchors.fill: parent

                            Item {
                                id: firstPage
                                Text {
                                    anchors.fill: parent
                                    anchors.margins: 5
                                    verticalAlignment: Text.AlignVCenter
                                    color: "#000"
                                    font.pixelSize: 14
                                    text: topicCardRoot.cardData.KeywordsDialogueString()
                                    wrapMode: Text.Wrap
                                    elide: Text.ElideRight
                                }
                            }
                            Item {
                                id: secondPage
                                Image {
                                    source: topicCardRoot.cardData.HeatmapMoveSource()
                                    fillMode: Image.PreserveAspectFit
                                    anchors.fill: parent
                                    anchors.margins: 20
                                }
                            }
                            Item {
                                id: thirdPage
                                Image {
                                    source: topicCardRoot.cardData.HeatmapGazeSource()
                                    fillMode: Image.PreserveAspectFit
                                    anchors.fill: parent
                                    anchors.margins: 20
                                }
                            }
                        }

                        PageIndicator {
                            id: indicator

                            count: view.count
                            currentIndex: view.currentIndex

                            anchors.bottom: view.bottom
                            anchors.horizontalCenter: parent.horizontalCenter
                        }
                    }
                    */
                    /*
                    Rectangle {
                        id: containerRectSummary
                        Layout.fillWidth: true

                        color: '#fff'
                        radius: 10

                        implicitHeight: txt3.implicitHeight + 10
                        implicitWidth: txt3.implicitWidth

                        visible: topicCardRoot.cardData.Summary() !== ""

                        Text {
                            id: txt3

                            anchors.fill: parent
                            anchors.leftMargin: 5
                            anchors.rightMargin: 5

                            horizontalAlignment: Text.AlignJustify
                            color: "#888"
                            font.pixelSize: 11
                            text: "Summary: " + topicCardRoot.cardData.Summary()
                            wrapMode: Text.Wrap
                        }
                    }
                    */

                    Rectangle {
                        id: containerRect
                        Layout.fillWidth: true

                        color: '#fff'
                        radius: 10

                        implicitHeight: txt.implicitHeight + 10
                        implicitWidth: txt.implicitWidth

                        visible: topicCardRoot.cardData.TextDialoguesFormatted() !== ""

                        Text {
                            id: txt

                            anchors.fill: parent
                            anchors.leftMargin: 5
                            anchors.rightMargin: 5

                            verticalAlignment: Text.AlignVCenter
                            color: "#000"
                            font.pixelSize: 14
                            text: String.fromCodePoint(0x1F5E8) + " " + topicCardRoot.cardData.TextDialoguesFormatted()
                            wrapMode: Text.Wrap
                        }
                    }

                    Rectangle {
                        id: containerRect2
                        Layout.fillWidth: true

                        color: '#fff'
                        radius: 10

                        implicitHeight: txt2.implicitHeight + 10
                        implicitWidth: txt2.implicitWidth

                        visible: topicCardRoot.cardData.TextNotes() !== ""

                        Text {
                            id: txt2

                            anchors.fill: parent
                            anchors.leftMargin: 5
                            anchors.rightMargin: 5

                            verticalAlignment: Text.AlignVCenter
                            color: "#000"
                            font.pixelSize: 14
                            text: String.fromCodePoint(0x1F5D2) + " " + topicCardRoot.cardData.TextNotes()
                            wrapMode: Text.Wrap
                        }
                    }

                    Rectangle {
                        id: containerRect3
                        Layout.fillWidth: true

                        //Layout.preferredWidth: 350

                        implicitWidth: imgGrid.implicitWidth
                        implicitHeight: imgGrid.implicitHeight + 50

                        visible: topicCardRoot.cardData.ThumbnailCrops().length > 0

                        color: '#fff'
                        radius: 10

                        GridLayout {
                            id: imgGrid
                            anchors.fill: parent
                            anchors.margins: 15
                            columns: 2
                            rows: 5

                            Repeater {
                                model: topicCardRoot.cardData.ThumbnailCrops()
                                delegate: 
                                Item {
                                    id: outer

                                    required property var modelData
                                    required property int index

                                    property int columnSpan: 1

                                    Layout.preferredHeight: 125
                                    Layout.fillWidth: true
                                    Layout.columnSpan: outer.columnSpan

                                    Rectangle {
                                        id: rectImg
                                        anchors.fill: parent

                                        property int rotationAngle: 0
                                        property bool editing: false

                                        border.color: editing ? "#f00" : "#f4f4f4"
                                        border.width: 2

                                        MouseArea {
                                            anchors.fill: parent
                                            acceptedButtons: Qt.LeftButton | Qt.RightButton

                                            onClicked: (mouse) => { 
                                                if (mouse.button === Qt.RightButton) 
                                                    contextMenu.popup()
                                            }

                                            onPressAndHold: (mouse) => {
                                                if (mouse.source === Qt.MouseEventNotSynthesized)
                                                    contextMenu.popup()
                                            }

                                            Menu {
                                                id: contextMenu

                                                onAboutToShow: {
                                                    rectImg.editing = true;
                                                }

                                                onAboutToHide: {
                                                    rectImg.editing = false;
                                                }

                                                MenuItem { 
                                                    text: "Rotate 90 deg. clockwise"
                                                    onTriggered: {
                                                        if (rectImg.rotationAngle === 0)
                                                            rectImg.rotationAngle = 90;
                                                        else if (rectImg.rotationAngle === 90)
                                                            rectImg.rotationAngle = 180;
                                                        else if (rectImg.rotationAngle === 180)
                                                            rectImg.rotationAngle = 270;
                                                        else
                                                            rectImg.rotationAngle = 0;
                                                    }
                                                }
                                                MenuItem { 
                                                    text: "Rotate 90 deg. counterclockwise" 
                                                    onTriggered: {
                                                        if (rectImg.rotationAngle === 0)
                                                            rectImg.rotationAngle = 270;
                                                        else if (rectImg.rotationAngle === 90)
                                                            rectImg.rotationAngle = 0;
                                                        else if (rectImg.rotationAngle === 180)
                                                            rectImg.rotationAngle = 90;
                                                        else
                                                            rectImg.rotationAngle = 180;
                                                    }
                                                }
                                                MenuItem { 
                                                    text: "Scale up" 
                                                    enabled: outer.columnSpan === 1
                                                    onTriggered: {
                                                        outer.columnSpan = 2;
                                                    }
                                                }
                                                MenuItem { 
                                                    text: "Scale down" 
                                                    enabled: outer.columnSpan === 2
                                                    onTriggered: {
                                                        outer.columnSpan = 1;
                                                    }
                                                }
                                            }
                                        }

                                        Image {
                                            id: imgThumb
                                            anchors.fill: parent
                                            source: outer.modelData["path"] + "#" + rectImg.rotationAngle
                                            fillMode: Image.PreserveAspectFit
                                        }

                                    }

                                    Row {
                                        anchors.verticalCenter: rectImg.top
                                        anchors.horizontalCenter: rectImg.horizontalCenter

                                        spacing: 5

                                        Rectangle {
                                            color: "black"
                                            width: labelText.implicitWidth + 10
                                            radius: 10
                                            height: 16

                                            Text {
                                                id: labelText

                                                anchors.centerIn: parent
                                                horizontalAlignment: Text.AlignHCenter
                                                verticalAlignment: Text.AlignVCenter

                                                color: "white"
                                                text: outer.modelData["label"]
                                                font.pixelSize: 11
                                                font.weight: Font.Bold
                                            }
                                        }
                                        Repeater {
                                            model: outer.modelData["within_aois"]

                                            delegate: Rectangle {
                                                id: inner
                                                required property var modelData

                                                width: 12
                                                height: 12
                                                radius: 5
                                                y: 2

                                                color: topicCardRoot.cmapAOI.get(inner.modelData)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Timespan label (top)
            Rectangle {
                width: 150
                height: 20
                radius: 20

                anchors.verticalCenter: topicCard.top
                anchors.horizontalCenter: topicCard.horizontalCenter

                color: '#373735' 

                Text {
                    anchors.centerIn: parent
                    color: "#fff"
                    font.pixelSize: 14
                    font.bold: true
                    text: Utils.timeFormat(topicCardRoot.cardData.PosStartSec()) + " - " + Utils.timeFormat(topicCardRoot.cardData.PosEndSec())
                }
            }

            // Match label (bottom)
            Rectangle {
                id: matchIndicator

                width: 50
                height: 20
                radius: 20

                anchors.verticalCenter: topicCard.bottom
                anchors.horizontalCenter: topicCard.horizontalCenter

                //color: '#373735' 
                color: '#fafafa' 
                border.color: '#f4f4f4'
                border.width: 0
                visible: topicCardRoot.score > 0.0

                Text {
                    anchors.centerIn: parent
                    color: "#000"
                    font.pixelSize: 10
                    font.bold: true
                    text: Math.floor(topicCardRoot.score * 100.0).toString().padStart(2, '0') 
                }
            }
        }

        // Text Quotes
        /*
        Rectangle {
            Layout.fillWidth: true

            radius: 20
            color: '#fafafa' 

            border.color: '#f4f4f4'
            border.width: 5

            implicitHeight: containerRect.implicitHeight
            implicitWidth: containerRect.implicitWidth

        }
        */

        // Notes Quotes
        /*
        Rectangle {
            Layout.fillWidth: true

            radius: 20
            color: '#fafafa' 

            border.color: '#f4f4f4'
            border.width: 5

            implicitHeight: containerRect2.implicitHeight
            implicitWidth: containerRect2.implicitWidth


        }
        */

        /*
        Rectangle {
            Layout.preferredWidth: 350
            Layout.preferredHeight: imgGrid.implicitHeight + 50
            visible: topicCardRoot.cardData.ThumbnailCrops().length > 0

            radius: 15
            color: '#fafafa' 

            border.color: '#f4f4f4'
            border.width: 5

            GridLayout {
                id: imgGrid
                anchors.fill: parent
                anchors.margins: 15
                columns: 2
                rows: 5

                Repeater {
                    model: topicCardRoot.cardData.ThumbnailCrops()
                    delegate: 
                    Item {
                        id: outer

                        required property var modelData
                        required property int index

                        Layout.preferredHeight: 125
                        Layout.fillWidth: true

                        Rectangle {
                            id: rectImg
                            anchors.fill: parent

                            property int rotationAngle: 0
                            border.color: "#f4f4f4"
                            border.width: 2

                            MouseArea {
                                anchors.fill: parent
                                onClicked: { 
                                    rectImg.rotationAngle = (rectImg.rotationAngle + 90) % 360;
                                }
                            }

                            Image {
                                id: imgThumb
                                anchors.fill: parent
                                source: outer.modelData["path"] + "#" + rectImg.rotationAngle
                                fillMode: Image.PreserveAspectFit
                            }

                        }

                        Row {
                            anchors.verticalCenter: rectImg.top
                            anchors.horizontalCenter: rectImg.horizontalCenter

                            spacing: 5

                            Rectangle {
                                color: "black"
                                width: labelText.implicitWidth + 10
                                radius: 10
                                height: 16

                                Text {
                                    id: labelText

                                    anchors.centerIn: parent
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter

                                    color: "white"
                                    text: outer.modelData["label"]
                                    font.pixelSize: 11
                                    font.weight: Font.Bold
                                }
                            }
                            Repeater {
                                model: outer.modelData["within_aois"]

                                delegate: Rectangle {
                                    id: inner
                                    required property var modelData

                                    width: 12
                                    height: 12
                                    y: 2

                                    color: topicCardRoot.cmapAOI.get(inner.modelData)
                                }
                            }
                        }
                    }
                }
            }
        }
        */

        Item {
            Layout.preferredWidth: topicCardRoot.width
            Layout.fillHeight: true
        }
    }
}