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
    readonly property var timelineVSpace: 10
    readonly property var timelineTopMargin: 50
    readonly property var rootTopMargin: 25

    // Height constants for TimelineSegment internal layout
    readonly property int aoiRiverHeight: 175
    readonly property int topicBarHeight: 30
    readonly property int axisHeight: 30
    readonly property int seqItemHeight: aoiModel.timeline_count() * (appWindow.timelineHeight + appWindow.timelineVSpace)
    readonly property int cardsConnectorHeight: 50
    readonly property int cardsAreaHeight: 400

    // Total height for each TimelineSegment
    readonly property int timelineSegmentHeight: aoiRiverHeight + topicBarHeight + axisHeight + seqItemHeight + axisHeight

    property var cmapGlobal: {}
    property var currCardData
    property bool showSplitViewHandles: true
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
        id: saveDialog
        title: "Save as \"%1\"".arg(nameTextInput.text);
        property bool exportOnlyBookmarks

        onAccepted: {
            const dir_path = selectedFolder.toString().replace(/^file:\/\/\//, "");
            var success = false;

            success = projectViewer.export_cards(nameTextInput.text, dir_path, exportOnlyBookmarks);
            successDialog.title = "Save as \"%1\"".arg(nameTextInput.text);

            if (success) {
                if (exportOnlyBookmarks) {
                    successDialog.text = "Successfully saved bookmarked cards as \"%1\" to directory %2".arg(nameTextInput.text).arg(dir_path);
                }
                else {
                    successDialog.text = "Successfully saved all cards as \"%1\" to directory %2".arg(nameTextInput.text).arg(dir_path);
                }
            }
            else {
                if (exportOnlyBookmarks) {
                    successDialog.text = "Failed to save bookmarked cards as \"%1\" to directory %2".arg(nameTextInput.text).arg(dir_path);
                }
                else {
                    successDialog.text = "Failed to save all cards as \"%1\" to directory %2".arg(nameTextInput.text).arg(dir_path);
                }
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
                case Constants.AppActions.ExportBookmarked:
                    {
                        saveDialog.exportOnlyBookmarks = (action === Constants.AppActions.ExportBookmarked);
                        if (nameTextInput.text !== "") {
                            saveDialog.open();
                        }
                        else {
                            successDialog.title = "Failed to save";
                            successDialog.text = "Please specify a name in the text field before saving!";
                            successDialog.open();
                        }
                    }
                    break;
                case Constants.AppActions.EnableSplitView:
                    appWindow.showSplitViewHandles = true;
                    break;
                case Constants.AppActions.DisableSplitView:
                    appWindow.showSplitViewHandles = false;
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

    property bool hideApp: false

    KeywordSearchDialog {
        id: keywordDialog
        anchors.centerIn: parent

        width: 500
        height: 350

        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        onAboutToShow: {
            appWindow.hideApp = true;
        }

        onAboutToHide: {
            appWindow.hideApp = false;
        }

        onKeywordSearch: (keywords) => {
            const has_matched = timeline_segment_model.keyword_match(keywords);
            if (has_matched) {
                appWindow.state = Constants.AppState.Search;
            }
            // Also true when there are no keywords entered or search was discarded by user
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

            /*
            for (const name of Object.keys(user_config["video_overlay"])) {
                topicSegments.UpdateOverlayColormap(name, user_config["video_overlay"][name]["colormap"]);
            }
            topicSegments.AdjustFilter(aoiModel.SegmentMinDurSec(), aoiModel.SegmentDisplayDurSec());
            */
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
        height: 60

        background: Rectangle {
            color: "#f8f8f8"
        }

        RowLayout {
            anchors.fill: parent
            spacing: 25

            TextField {
                id: nameTextInput
                Layout.fillHeight: true
                Layout.preferredWidth: contentWidth
                Layout.minimumWidth: 250

                text: ""
                placeholderText: "Enter name here ..."
                font.pixelSize: 20
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
        id: rootContainer

        layer.enabled: true
        anchors.fill: parent
        spacing: 0
        visible: !appWindow.hideApp

        LegendViews {
            id: legend

            Layout.preferredWidth: 40
            Layout.fillHeight: true

            color: "#f8f8f8"
            textColor: "#909090"
            z: 200

            streamLabels: aoiModel.GetMultiTimeLabels()
            identifiers: [...aoiModel.Identifiers()].sort()

            // Bind directly to the actual heights of the content items
            // tsRoot contains TimelineSegment with internal stretch factors (AOIRiver: 5, seqItem: 3)
            timelineAreaHeight: tsRoot.height
            topicCardsAreaHeight: cardsConnectorRoot.height + cardsRoot.height

            // Fixed heights for internal components
            topicBarHeight: appWindow.topicBarHeight
            axisHeight: appWindow.axisHeight

            // Stretch factors matching TimelineSegment.qml layout
            aoiRiverStretchFactor: 5
            seqItemStretchFactor: 3
        }

        Flickable {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true

            contentWidth: layoutManager.max_width
            contentHeight: tsRootx.implicitHeight

            flickableDirection: Flickable.HorizontalFlick
            boundsBehavior: Flickable.StopAtBounds

            clip: true

            ScrollBar.horizontal: ScrollBar {
                policy: ScrollBar.AlwaysOn 
            }

            SplitView {
                id: tsRootx
                spacing: 0
                width: scroll.contentWidth
                implicitHeight: tsRoot.contentHeight + cardsConnectorRoot.contentHeight + cardsRoot.contentHeight
                orientation: Qt.Vertical

                handle: Rectangle {
                    id: rectHandle
                    visible: appWindow.showSplitViewHandles
                    implicitWidth: 4
                    implicitHeight: 4
                    color: "#9b81e8"

                    SequentialAnimation on color {
                        running: parent.visible
                        loops: Animation.Infinite

                        ColorAnimation {
                            to: Qt.lighter("#9b81e8", 1.3) 
                            duration: 1500
                            easing.type: Easing.InOutQuad
                        }
                        ColorAnimation {
                            to: Qt.darker("#9b81e8", 1.3) 
                            duration: 1500
                            easing.type: Easing.InOutQuad
                        }
                    }
                }


                ListView {
                    id: tsRoot
                    z: 5
                    SplitView.fillWidth: true
                    SplitView.preferredHeight: appWindow.timelineSegmentHeight
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
                        }

                        onCardVisibilityChanged: (visible) => {
                            timeline_segment_model.setHasCard(ts.index, visible);
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

                ColumnLayout {
                    SplitView.fillWidth: true

                    Item {
                        id: cardsConnectorRoot
                        z: 50

                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        Layout.preferredHeight: appWindow.cardsConnectorHeight

                        Repeater {
                            anchors.fill: parent
                            model: layoutManager.card_layout()

                            delegate: CardConnector {
                                id: cardConn

                                required property real srcPosX
                                required property real dstPosX
                                required property real segmentWidth

                                fromX: cardConn.srcPosX
                                fromY: cardsConnectorRoot.height - 10 
                                toLeftX: cardConn.dstPosX
                                toRightX: cardConn.dstPosX + cardConn.segmentWidth
                                toY: 1
                            }
                        }
                    }

                    Item {
                        id: cardsRoot
                        Layout.fillWidth: true
                        Layout.preferredHeight: appWindow.cardsAreaHeight

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
                }
                Rectangle { 
                    SplitView.fillHeight: true 
                    SplitView.fillWidth: true 
                }
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

    MultiEffect {
        source: rootContainer
        anchors.fill: rootContainer
        brightness: -0.1
        blurEnabled: true
        blurMax: 21
        blur: 1.0
        visible: appWindow.hideApp
        autoPaddingEnabled: false
    }
}
