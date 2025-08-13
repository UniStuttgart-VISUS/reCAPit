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
    required property var colormap

    property var drawerOpened: false

    signal saveChanges(string title, string quotes, string notes)

    background: Rectangle {
        color: "#f0f0f0"
    }

    function formattedDialogue(utterance_speaker_pairs, target_tokens) {
        var dialogueStr = "";
        var speaker_count = {};

        for (var idx = 0; idx < utterance_speaker_pairs.length; ++idx) {
            const speaker = utterance_speaker_pairs[idx].speaker;
            if (!speaker_count[speaker])
                speaker_count[speaker] = 1;

            const utterance_id = "%1%2".arg(speaker.toUpperCase().slice(0, 2)).arg(speaker_count[speaker]);
            dialogueStr += "<h3>%1 <font color=\"#aaa\">(%2)</font></h3><p>%3</p>".arg(speaker).arg(utterance_id).arg(utterance_speaker_pairs[idx].text);
            speaker_count[speaker] = speaker_count[speaker] + 1;
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

        dialogueTextSelection.setOutText(topicSegments.TextDialoguesOriginal(drawer.cardIndex));
        notesTextSelection.setOutText(topicSegments.TextNotes(drawer.cardIndex));
        notesTextSelection.labels = topicSegments.Labels(drawer.cardIndex)
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
            text: topicSegments.Title(drawer.cardIndex)
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

                    videoOverlaySources: topicSegments.VideoOverlaySources(drawer.cardIndex)
                    startPosition: topicSegments.PosStartSec(drawer.cardIndex) * 1000
                    endPosition: topicSegments.PosEndSec(drawer.cardIndex) * 1000
                    active: drawer.drawerOpened
                    topDownSource: topicSegments.VideoSourceTopDown()
                    peripheralSources: topicSegments.VideoSourcesPeripheral()
                    colormapAOIs: drawer.colormap

                    onSelectionChanged: (frame, pos_ms, xpos, ypos, width, height, overlay_src) => {
                        topicSegments.RegisterVideoCrop(frame, pos_ms, drawer.cardIndex, xpos, ypos, width, height, overlay_src); 
                        thumbnailPreview.model = topicSegments.ThumbnailCrops(drawer.cardIndex);
                        thumbnailPreview.model = Qt.binding(function() { return topicSegments.ThumbnailCrops(drawer.cardIndex)} )
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

                            model: topicSegments.ThumbnailCrops(drawer.cardIndex)
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
                    textContent: drawer.formattedDialogue(topicSegments.GetUtteranceSpeakerPairs(drawer.cardIndex), keywordDialog.userKeywords)
                    placeHolderText: "Insert excerpts from the above dialogue here"
                    pastedTextColor: "blue"
                }

                TextSelection {
                    id: notesTextSelection
                    Layout.preferredWidth: 550
                    Layout.fillHeight: true
                    Layout.verticalStretchFactor: 1

                    labels: topicSegments.Labels(drawer.cardIndex)
                    title: String.fromCodePoint(0x1F5D2) + "  Notes  " + String.fromCodePoint(0x1F5D2)
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
                    notesTextSelection.labels = topicSegments.Labels(drawer.cardIndex);
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