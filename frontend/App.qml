import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Dialogs
import QtQuick.Shapes 1.2
import QtQml
import QtQuick.Controls.Basic

import "components"
import "windows"
import "js/utils.js" as Utils
import "js/colorschemes.js" as Colorschemes
import "."

ApplicationWindow {
    id: appwin
    visible: true
    width: 1920
    height: 1080

    readonly property var timelineHeight: 25
    readonly property var placeholderWidth: 30
    readonly property var timelineVSpace: 7
    readonly property var timelineTopMargin: 50
    readonly property var rootTopMargin: 25
    readonly property int timelineSegmentHeight: 90 + 175 + topicSegments.SpeechLineCount() * (appwin.timelineHeight + appwin.timelineVSpace)

    property var cmapGlobal: {}
    property var currCardData

    signal reset()

    function compressSegments() {
        // TODO : Implement
    }

    PreferenceWindow {
        id: preferencePane
        width: 640
        height: 480
    }

    AboutWindow {
        id: aboutWindow
    }

    menuBar: CustomMenuBar {
        onOpenAboutWindow: {
            aboutWindow.show();
        }
        onOpenPreferenceWindow: {
            preferencePane.show();
        }
    }

    TopicCardDrawer {
        id: drawer

        height: appwin.height
        interactive: true
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        contentWidth: 600
        contentHeight: appwin.height

        cardData: appwin.currCardData
        colormap: appwin.cmapGlobal

        onSaveChanges: (user_title, user_text, user_notes) => {
            const modelRow = appwin.currCardData.SegmentIndex();
            topicSegments.timeline_segment_model.setTitle(modelRow, user_title);
            topicSegments.timeline_segment_model.setQuotesNote(modelRow, user_notes);
            topicSegments.timeline_segment_model.setQuotesText(modelRow, user_text);
        }
    }

    KeywordSearchDialog {
        id: keywordDialog
        anchors.centerIn: parent

        width: 500
        height: 350

        closePolicy: Popup.CloseOnEscape

        onKeywordSearch: (keywords) => {
            var targetIndices = topicSegments.KeywordMatches(keywords);
            for (var i = 0; i < cardsRoot.children.length; ++i) {
                const idx = cardsRoot.children[i].cardData.SegmentIndex();
                cardsRoot.children[i].opacity = targetIndices.includes(idx) ? 1.0 : 0.5;
            }
        }
    }

    Component.onCompleted: {
        appwin.cmapGlobal = Colorschemes.createCombinedColormaps(aoiModel.ColormapCategories());
        preferencePane.userConfig = aoiModel.UserConfig();
    }

    Connections {
        target: preferencePane
        function onSaveCurrentUserConfig(user_config) {
            aoiModel.SetUserConfig(user_config);

            for (const name of Object.keys(user_config["video_overlay"])) {
                topicSegments.UpdateOverlayColormap(name, user_config["video_overlay"][name]["colormap"]);
            }
            topicSegments.AdjustFilter(aoiModel.SegmentMinDurSec(), aoiModel.SegmentDisplayDurSec());
        }
    }

    Row {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 100
        z: 250
        spacing: 20

        FloatingButton {
            text: ""
            color: "#005fee"
            width: 75
            height: 75
            source: "../icons/reset.png"
            tooltipText: "Reset the timeline to its initial state"

            onClicked: function() {
                appwin.reset();
                scroll.ScrollBar.horizontal.position = 0.0;
            }
        }

        FloatingButton {
            text: ""
            color: "#005fee"
            width: 75
            height: 75
            source: "../icons/compress.png"
            tooltipText: "Compress the timeline, retaining only the marked segments."

            onClicked: function() {
                appwin.compressSegments();
                scroll.ScrollBar.horizontal.position = 0.0;
            }
        }

        FloatingButton {
            text: ""
            color: "#005fee"
            width: 75
            height: 75
            source: "../icons/search.png"
            tooltipText: "Open keyword search dialog"

            onClicked: function() {
                keywordDialog.open();
            }
        }
    }

    header: Frame {
        height: 50

        background: Rectangle {
            color: "#f8f8f8"
        }

        RowLayout {
            anchors.fill: parent
            spacing: 25

            TextInput {
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignVCenter

                text: "Enter headline here ..."
                font.pixelSize: 26
                font.weight: Font.Bold
                font.capitalization: Font.AllUppercase
                color: "#c8c7d1"
                horizontalAlignment: Text.AlignLeft
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            LegendCategories {
                title: "Roles"
                labels: aoiModel.Roles()
                cmap: appwin.cmapGlobal
            }

            LegendCategories {
                id: aoiLegend
                title: "AOIs"
                labels: aoiModel.Labels()
                cmap: appwin.cmapGlobal
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        LegendViews {
            id: legend

            Layout.preferredWidth: 40
            Layout.fillHeight: true

            color: "#f8f8f8"
            textColor: "#909090"
            z: 200

            streamLabels: aoiModel.GetMultiTimeLabels()
            identifiers: [...aoiModel.Identifiers()].sort()

            h1: 175
            h2: 30
            h3: 60 + topicSegments.SpeechLineCount() * (appwin.timelineHeight + appwin.timelineVSpace)
            h4: 500
        }

        Flickable {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true

            contentWidth: 15000
            contentHeight: 1000

            flickableDirection: Flickable.HorizontalFlick
            boundsBehavior: Flickable.StopAtBounds

            clip: true

            ScrollBar.horizontal: ScrollBar {
                policy: ScrollBar.AlwaysOn 
            }

            ColumnLayout {
                id: tsRootx
                spacing: 0
                width: scroll.contentWidth

                ListView {
                    id: tsRoot
                    z: 5
                    Layout.fillWidth: true
                    height: appwin.timelineSegmentHeight
                    orientation: ListView.Horizontal

                    property real start: topicSegments.MinTimestamp()
                    property real end: topicSegments.MaxTimestamp()

                    model: topicSegments.timeline_segment_model
                    delegate: TimelineSegment {
                        id: ts

                        required property string title
                        required property int segmentIdx
                        required property real startSec
                        required property real endSec
                        required property var timeEvents
                        required property var stackedData
                        required property var seqData
                        required property var thumbnailInfo
                        required property bool hasCard
                        required property int index

                        Component.onCompleted: {
                            // Not so nice solution to get the child's position in parent coordinates
                            let pos_x = scroll.contentWidth * (ts.startSec - tsRoot.start) / (tsRoot.end - tsRoot.start);
                            layoutManager.register_item(ts.segmentIdx, 
                                                        pos_x,
                                                        0.0,
                                                        ts.width, 
                                                        ts.hasCard);

                        }

                        Component.onDestruction: {
                            layoutManager.unregister_item(ts.segmentIdx);
                        }

                        onCardVisibilityChanged: (visible) => {
                            //topicSegments.timeline_segment_model.setHasCard(ts.index, visible);
                            layoutManager.set_active(ts.segmentIdx, visible);
                        }

                        width: Math.floor(15000 * (endSec - startSec) / (tsRoot.end - tsRoot.start));
                        height: parent.height

                        segmentTitle: ts.title
                        dia: ts.seqData
                        tan: ts.timeEvents
                        stacks: ts.stackedData
                        cmap: appwin.cmapGlobal
                        topicIndex: ts.segmentIdx
                        cardVisible: ts.hasCard
                        min_ts: ts.startSec
                        max_ts: ts.endSec
                        tickInfos: ts.thumbnailInfo
                    }
                }

                Item {
                    z: 100
                    id: cardsConnectorRoot
                    Layout.fillWidth: true
                    Layout.preferredHeight: 50

                    Repeater {
                        anchors.fill: parent
                        model: layoutManager.card_layout()

                        delegate: CardConnector {
                            id: cardConn

                            required property real srcPosX
                            required property real dstPosX
                            required property real segmentWidth

                            fromX: cardConn.srcPosX
                            fromY: 40 
                            toLeftX: cardConn.dstPosX
                            toRightX: cardConn.dstPosX + cardConn.segmentWidth
                            toY: 0
                        }
                    }
                }

                Item {
                    id: cardsRoot
                    Layout.fillWidth: true
                    Layout.preferredHeight: 400

                    Repeater {
                        anchors.fill: parent
                        model: cardList 

                        delegate: TopicCard {
                            id: topicCard

                            required property var cardDataX
                            required property var layoutData
                            required property bool isVisible
                            required property int index

                            visible: topicCard.isVisible

                            onClicked: {
                                appwin.currCardData = cardDataX;
                                drawer.open()
                            }

                            onMarkedChanged: {
                                const segmentIdx = topicCard.cardDataX.SegmentIndex();
                                topicSegments.timeline_segment_model.toggleMarked(segmentIdx);
                            }

                            x: topicCard.layoutData.x - (topicCard.layoutData.width - 50) / 2 
                            y: 0
                            width: topicCard.layoutData.width - 50
                            cardData: topicCard.cardDataX
                            cmap: appwin.cmapGlobal
                        }
                    }
                }
                Item { Layout.fillHeight: true }
            }
        }

        NavigationList {
            Layout.preferredWidth: boxW
            Layout.fillHeight: true
            model: topicSegments.timeline_segment_model
        }
    }
}
