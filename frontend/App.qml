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
    id: appWindow
    visible: true
    width: 1920
    height: 1080

    readonly property var timelineHeight: 25
    readonly property var placeholderWidth: 30
    readonly property var timelineVSpace: 7
    readonly property var timelineTopMargin: 50
    readonly property var rootTopMargin: 25
    readonly property int timelineSegmentHeight: 90 + 175 + aoiModel.timeline_count() * (appWindow.timelineHeight + appWindow.timelineVSpace)

    property var cmapGlobal: {}
    property var currCardData
    property int state: Constants.AppState.Default

    function compressSegments() {
        appWindow.state = Constants.AppState.Compressed;
    }

    function reset() {
        appWindow.state = Constants.AppState.Default;
    }

    Shortcut {
        sequence: "Ctrl+Q"
        onActivated: {
            close();
        }
    }

    Shortcut {
        sequence: "Ctrl+R"
        onActivated: {
            reset();
        }
    }

    MessageDialog {
        id: successDialog
        buttons: MessageDialog.Ok
    }

    FolderDialog {
        id: exportBookmarkedDialog
        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "")
            const success = topicSegments.export_bookmarked(dir_path)

            successDialog.title = "Export bookmarked segments";

            if (success) {
                successDialog.text = "Successfully exported bookmarked segments!";
            }
            else {
                successDialog.text = "Failed to export bookmarked segments to %1".arg(dir_path);
            }
            successDialog.open();
        }
    }

    FolderDialog {
        id: saveDialog
        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "")
            const success = topicSegments.export_state(dir_path)

            successDialog.title = "Save state";

            if (success) {
                successDialog.text = "Successfully saved state!";
            }
            else {
                successDialog.text = "Failed to save state to %1".arg(dir_path);
            }
            successDialog.open();
        }
    }

    FolderDialog {
        id: loadDialog
        currentFolder: aoiModel.ExportDir()
        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "")
            const success = topicSegments.import_state(dir_path)

            successDialog.title = "Restore State";

            if (success) {
                successDialog.text = "Successfully loaded state!";
            }
            else {
                successDialog.text = "Failed to load state from %1".arg(dir_path);
            }
            successDialog.open();
        }
    }

    PreferenceWindow {
        id: preferenceWindow
        width: 640
        height: 480
    }

    AboutWindow {
        id: aboutWindow
    }

    menuBar: CustomMenuBar {
        onActionRequested: (action) => {
            switch (action) {
                case Constants.AppActions.LoadState:
                    loadDialog.open();
                    break;
                case Constants.AppActions.SaveState:
                    saveDialog.open();
                    break;
                case Constants.AppActions.ExportBookmarked:
                    exportBookmarkedDialog.open();
                    break;
                case Constants.AppActions.ScaleUp:
                    layoutManager.max_width *= 1.5;
                    break;
                case Constants.AppActions.ScaleDown:
                    layoutManager.max_width /= 1.5;
                    break;
                case Constants.AppActions.OpenProject:
                    projectManager.open_manager();
                    appWindow.close();
                    break;
                case Constants.AppActions.OpenPreferences:
                    preferenceWindow.show();
                    break;
                case Constants.AppActions.OpenAbout:
                    aboutWindow.show();
                    break;
                case Constants.AppActions.Search:
                    keywordDialog.open();
                    break;
                case Constants.AppActions.Reset:
                    appWindow.reset();
                    break;
                case Constants.AppActions.Quit:
                    appWindow.close();
                    break;
            }
        }
    }

    TopicCardDrawer {
        id: drawer

        height: appWindow.height
        interactive: true
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        contentWidth: 600
        contentHeight: appWindow.height

        cardData: appWindow.currCardData
        colormap: appWindow.cmapGlobal

        onSaveChanges: (user_title, user_text, user_notes) => {
            appWindow.currCardData.Title = user_title;
            appWindow.currCardData.UserQuotes = user_text;
            appWindow.currCardData.UserNotes = user_notes;
        }
    }

    KeywordSearchDialog {
        id: keywordDialog
        anchors.centerIn: parent

        width: 500
        height: 350

        closePolicy: Popup.CloseOnEscape

        onKeywordSearch: (keywords) => {
            const has_matched = timeline_segment_model.keyword_match(keywords);
            if (has_matched) {
                appWindow.state = Constants.AppState.Search;
            }
            // I also true when there are no keywords entered or search was discarded by user
            else {
                appWindow.state = Constants.AppState.Default;
            }
        }
    }

    Component.onCompleted: {
        appWindow.cmapGlobal = Colorschemes.createCombinedColormaps(aoiModel.ColormapCategories());
        preferenceWindow.userConfig = aoiModel.UserConfig();
    }

    Connections {
        target: preferenceWindow
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

            onClicked: {
                appWindow.reset();
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

            onClicked: {
                appWindow.compressSegments();
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

            onClicked: {
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
                cmap: appWindow.cmapGlobal
            }

            LegendCategories {
                id: aoiLegend
                title: "AOIs"
                labels: aoiModel.Labels()
                cmap: appWindow.cmapGlobal
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
            h3: 60 + aoiModel.timeline_count() * (appWindow.timelineHeight + appWindow.timelineVSpace)
            h4: 500
        }

        Flickable {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true

            contentWidth: layoutManager.max_width
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
                    height: appWindow.timelineSegmentHeight
                    orientation: ListView.Horizontal

                    property real start: aoiModel.start_offset_sec()
                    property real end: aoiModel.total_duration_sec()

                    onContentWidthChanged: {
                        Qt.callLater(() => {
                            for (var idx = 0; idx < tsRoot.count; idx++) {
                                const item = tsRoot.itemAtIndex(idx);

                                const marked = timeline_segment_model.isMarked(idx);
                                const hasCard = timeline_segment_model.hasCard(idx);
                                const isCompressed = (appWindow.state === Constants.AppState.Compressed && !marked) 
                                const pos_x = item.mapToItem(tsRoot, 0.0, 0.0).x;

                                layoutManager.update_item(idx, 
                                                          pos_x,
                                                          0.0,
                                                          item.width, 
                                                          hasCard && !isCompressed);
                            }
                        });
                        Qt.callLater(layoutManager.updateCardLayout);
                    }

                    model: timeline_segment_model
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
                        required property bool marked
                        required property string displayState
                        required property int index

                        opacity: (appWindow.state === Constants.AppState.Search) && displayState !== "highlighted" ? 0.5 : 1.0
                        
                        readonly property bool isCompressed: (appWindow.state === Constants.AppState.Compressed && !marked) 
                        readonly property real baseWidth: Math.floor(layoutManager.max_width * (endSec - startSec) / (tsRoot.end - tsRoot.start));

                        Component.onCompleted: {
                            layoutManager.register_item(ts.segmentIdx);
                        }

                        Component.onDestruction: {
                            layoutManager.unregister_item(ts.segmentIdx);
                            Qt.callLater(layoutManager.updateCardLayout)
                        }

                        onCardVisibilityChanged: (visible) => {
                            //timeline_segment_model.setHasCard(ts.index, visible);
                            layoutManager.set_active(ts.segmentIdx, visible);
                            Qt.callLater(layoutManager.updateCardLayout)
                        }

                        width: isCompressed ? 20 : baseWidth
                        height: parent.height
                        hideContent: isCompressed

                        segmentTitle: ts.title
                        dia: ts.seqData
                        tan: ts.timeEvents
                        stacks: ts.stackedData
                        cmap: appWindow.cmapGlobal
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

                            required property var layoutData
                            required property var cardDataX

                            readonly property real srcPosX: layoutData.srcPosX
                            readonly property real cardWidth: layoutData.cardWidth
                            readonly property int segmentIdx: cardDataX.SegmentIndex
                            //property var cardDataX: timeline_segment_model.topic_card_data(segmentIdx)

                            readonly property string displayState: cardDataX.DisplayState
                            opacity: (appWindow.state === Constants.AppState.Search) && displayState !== "highlighted" ? 0.5 : 1.0

                            Connections {
                                target: cardDataX

                                function onTitleChanged() {
                                    timeline_segment_model.setTitle(segmentIdx, cardDataX.Title);
                                }
                                function onUserQuotesChanged() {
                                    timeline_segment_model.setQuotesText(segmentIdx, cardDataX.UserQuotes);
                                }
                                function onUserNotesChanged() {
                                    timeline_segment_model.setQuotesNote(segmentIdx, cardDataX.UserNotes);
                                }
                                function onMarkedChanged() {
                                    timeline_segment_model.setMarked(segmentIdx, cardDataX.Marked);
                                }
                                function onThumbnailAdded(frame, pos_ms, selection_rect, overlay_src) {
                                    // Not super clean way to propagate label to back to TopicCardData
                                    const label = timeline_segment_model.register_video_crop(frame, pos_ms, segmentIdx, selection_rect, overlay_src); 
                                    cardDataX.add_label(label);
                                }
                            }

                            onClicked: {
                                appWindow.currCardData = cardDataX;
                                drawer.open();
                            }

                            x: topicCard.srcPosX - (topicCard.cardWidth - 50) / 2 
                            y: 0
                            width: topicCard.cardWidth - 50
                            cardData: topicCard.cardDataX
                            cmap: appWindow.cmapGlobal
                        }
                    }
                }
                Item { Layout.fillHeight: true }
            }
        }

        NavigationList {
            Layout.preferredWidth: boxW
            Layout.fillHeight: true
            model: timeline_segment_model
            highlightsActive: appWindow.state === Constants.AppState.Search

            onNavigateTo: (index) => {
                const pos_x = layoutManager.card_layout().getDstPosX(index);
                scroll.ScrollBar.horizontal.position = pos_x / tsRootx.width;
            }
        }
    }
}
