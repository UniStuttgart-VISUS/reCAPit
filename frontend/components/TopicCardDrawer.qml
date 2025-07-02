import QtQuick 2.15
import QtQuick.Controls.Basic 2.15
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

Drawer {
    id: drawer

    interactive: true
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    required property int cardIndex
    required property var cardData
    required property var colormapAOIs

    property var drawerOpened: false

    signal saveChanges(string title, string quotes, string notes)

    background: Rectangle {
        color: "#f0f0f0"
    }


    function formattedDialogue(dialogue, target_tokens) {
        const dial = dialogue.FullDialogue()
        var dialogueStr = "";
        var srcCount = {};

        for (var idx = 0; idx < dial.length; ++idx) {
            const subject_id = dial[idx].src;
            if (!srcCount[subject_id])
                srcCount[subject_id] = 1;

            const utterance_id = "%1%2".arg(subject_id.toUpperCase().slice(0, 2)).arg(srcCount[subject_id]);
            dialogueStr += "<h3>%1 <font color=\"#aaa\">(%2)</font></h3><p>%3</p>".arg(subject_id).arg(utterance_id).arg(dial[idx].text);
            srcCount[subject_id] = srcCount[subject_id] + 1;
        }

        for (var idx = 0; idx < target_tokens.length; ++idx) {
            const token = target_tokens[idx];
            var pos = dialogueStr.toLowerCase().indexOf(token);

            while (pos !== -1) {
                dialogueStr = dialogueStr.slice(0, pos-1) + " <b>" + dialogueStr.slice(pos, pos+token.length) + "</b>" + dialogueStr.slice(pos+token.length);
                pos = dialogueStr.toLowerCase().indexOf(token, pos+3+token.length);
            }
        }
        return dialogueStr;
    }

    onOpened: {
        video.selectionMode = 0;
        video.selectionWidth = 0;
        video.selectionHeight = 0;
        drawer.drawerOpened = true;

        dialogueTextSelection.setOutText(drawer.cardData.TextDialoguesOriginal());
        notesTextSelection.setOutText(drawer.cardData.TextNotes());
    }

    onClosed: {
        drawer.drawerOpened = false;
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        TextInput {
            Layout.fillWidth: true
            Layout.preferredHeight: 50

            id: heading
            text: drawer.cardData.Title()
            wrapMode: Text.WordWrap

            font.pixelSize: 20
            font.weight: Font.Bold

            maximumLength: 75
            selectByMouse: true 
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.verticalStretchFactor: 2
            contentHeight: drawerRoot.implicitHeight

            ColumnLayout{
                anchors.fill: parent
                id: drawerRoot
                spacing: 10

                CustomVideo {
                    id: video

                    Layout.preferredWidth: 550
                    Layout.preferredHeight: 550

                    heatmapGazeSource: topicSegments.HeatmapGazeSource(drawer.cardIndex)
                    heatmapMoveSource: topicSegments.HeatmapMoveSource(drawer.cardIndex)

                    hasGazeHeatmap: topicSegments.HasGazeHeatmap()
                    hasMoveHeatmap: topicSegments.HasMoveHeatmap()

                    gazeOverlayData: topicSegments.GazeOverlayData()
                    gazeOverlayIds: topicSegments.GazeOverlayIDs()

                    startPosition: drawer.cardData.PosStartSec() * 1000
                    endPosition: drawer.cardData.PosEndSec() * 1000
                    active: drawer.drawerOpened
                    topDownSource: topicSegments.VideoSourceTopDown()
                    peripheralSources: topicSegments.VideoSourcesPeripheral()
                    colormapAOIs: drawer.colormapAOIs

                    onSelectionChanged: (frame, pos_ms, xpos, ypos, width, height, overlay_src) => {
                        topicSegments.RegisterVideoCrop(frame, pos_ms, drawer.cardIndex, xpos, ypos, width, height, overlay_src); 
                        thumbnailPreview.model = topicSegments.GetTopicCardData(drawer.cardIndex).ThumbnailCrops();
                        thumbnailPreview.model = Qt.binding(function() { return drawer.cardData.ThumbnailCrops()} )
                    }
                }

                GroupBox {
                    id: thumbnailsBox
                    Layout.preferredWidth: 550
                    Layout.preferredHeight: 100
                    title: String.fromCodePoint(0x1F533) + "  Video Crops  " + String.fromCodePoint(0x1F533)

                    label: Label {
                        x: thumbnailsBox.leftPadding
                        width: thumbnailsBox.availableWidth
                        text: thumbnailsBox.title
                        font.pixelSize: 16
                        font.bold: true
                        elide: Text.ElideRight
                    }

                    background: Rectangle {
                        y: thumbnailsBox.topPadding - thumbnailsBox.bottomPadding
                        width: parent.width
                        height: parent.height - thumbnailsBox.topPadding + thumbnailsBox.bottomPadding
                        color: "transparent"
                        border.color: "#e0e0e0"
                        border.width: 1
                        radius: 5
                    }

                    Rectangle {
                        anchors.fill: parent
                        radius: 5

                        ListView {
                            id: thumbnailPreview
                            orientation: ListView.Horizontal
                            anchors.fill: parent
                            clip: true

                            model: drawer.cardData.ThumbnailCrops()
                            delegate: 
                            Item {
                                id: outer

                                required property var modelData
                                required property int index

                                width: 60
                                height: 60

                                Rectangle {
                                    id: rectImg
                                    anchors.fill: parent
                                    //border.width: 2

                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: { 
                                        }
                                    }

                                    Image {
                                        id: imgThumb
                                        anchors.fill: parent
                                        source: outer.modelData["path"] + "#0"
                                        fillMode: Image.PreserveAspectFit
                                    }
                                }
                            }
                        }
                    }
                }

                GroupBox {
                    id: dialogueSummarySelection

                    Layout.preferredWidth: 550
                    Layout.preferredHeight: summaryTextArea.implicitHeight + 50
                    Layout.fillHeight: true
                    Layout.verticalStretchFactor: 1

                    label: Label {
                        x: dialogueSummarySelection.leftPadding
                        width: dialogueSummarySelection.availableWidth
                        text: String.fromCodePoint(0x1F50D) + "  Summary  " + String.fromCodePoint(0x1F50D)
                        font.pixelSize: 16
                        font.bold: true
                        elide: Text.ElideRight
                    }

                    background: Rectangle {
                        y: dialogueSummarySelection.topPadding - dialogueSummarySelection.bottomPadding
                        width: parent.width
                        height: parent.height - dialogueSummarySelection.topPadding + dialogueSummarySelection.bottomPadding
                        color: "transparent"
                        border.color: "#e0e0e0"
                        border.width: 1
                        radius: 5
                    }

                    TextArea  {
                        id: summaryTextArea
                        anchors.fill: parent
                        
                        text: topicSegments.GetSummary(drawer.cardIndex)
                        textFormat: Text.RichText
                        wrapMode: Text.WordWrap

                        background: Rectangle {
                            radius: 5
                        }

                        font.pixelSize: 14
                        readOnly: true
                        selectByMouse: true
                    }
                }

                TextSelection {
                    id: dialogueTextSelection
                    Layout.preferredWidth: 550
                    Layout.fillHeight: true
                    Layout.verticalStretchFactor: 1

                    labels: []
                    title: String.fromCodePoint(0x1F5E8) + "  Dialogue  " + String.fromCodePoint(0x1F5E8)
                    //textContentQuote: drawer.cardData.TextDialoguesOriginal()
                    textContent: drawer.formattedDialogue(topicSegments.GetDialogueLine(drawer.cardIndex), keywordDialog.userKeywords)
                    placeHolderText: "Insert excerpts from the above dialogue here"
                    pastedTextColor: "blue"
                }

                TextSelection {
                    id: notesTextSelection
                    Layout.preferredWidth: 550
                    Layout.fillHeight: true
                    Layout.verticalStretchFactor: 1

                    labels: drawer.cardData.Labels()
                    title: String.fromCodePoint(0x1F5D2) + "  Notes  " + String.fromCodePoint(0x1F5D2)
                    //textContentQuote: drawer.cardData.TextNotes()
                    textContent: topicSegments.GetNotes(drawer.cardIndex).allHTML()
                    placeHolderText: "Insert excerpts from the above notes here"
                    pastedTextColor: "purple"
                }
            }
        }

        Row {
            spacing: 10
            Layout.fillWidth: true
            Layout.preferredHeight: 40

            Button {
                width: 200
                height: 40
                text: "Save Changes"
                onClicked: {
                    saveChanges(heading.text, dialogueTextSelection.getOutText(), notesTextSelection.getOutText());
                    notesTextSelection.labels = drawer.cardData.Labels();
                }
            }

            Button {
                width: 100
                height: 40
                text: "Cancel"
                onClicked: {
                    drawer.close();
                }
            }
        }
    }
}