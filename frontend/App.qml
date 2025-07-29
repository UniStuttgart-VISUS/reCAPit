import QtQuick 2.15
import QtQuick.Effects
import QtMultimedia
import QtQuick.Layouts 1.0
import QtQuick.Shapes 1.2
import QtQml

import "components"
import "windows"
import "js/utils.js" as Utils
import "js/colorschemes.js" as Colorschemes
import "."

import QtQuick.Controls.Basic

ApplicationWindow {
    id: appwin
    visible: true
    width: 2000
    height: 1080
    color: "white"
    title: ""

    readonly property var timelineHeight: 15
    readonly property var placeholderWidth: 30
    readonly property var timelineVSpace: 7
    readonly property var timelineTopMargin: 50
    readonly property var rootTopMargin: 25

    property var cmapGlobal: {}

    property int selectedSnippetIndex : -1

    readonly property int timelineSegmentHeight: 90 + 175 + topicSegments.SpeechLineCount() * (appwin.timelineHeight + appwin.timelineVSpace)

    property var segmentIndicesOfCards: []
    property var keywordMatchedIndices: []
    property var allCardData : []

    property var segmentIndicesWithCards : []
    property var targetSegmentIndices : []

    property int currentEditCardIndex: 0
    property bool drawerVisible: false

    property list<string> segmentIndicesMarkers : []
    property list<real> segmentIndicesScores : []

    signal buildStory()
    signal reset()

    function interpolateColor(value, colorscheme) {
        // Clamp value between 0 and 1
        value = Math.max(0, Math.min(1, value));
        var colors;

        if (colorscheme === "BuGn")
            colors = ["#edf8fb","#b2e2e2","#66c2a4","#238b45"];
        else if (colorscheme === "BuPu")
            colors = ["#edf8fb","#b3cde3","#8c96c6","#88419d"];
        else if (colorscheme === "GnBu")
            colors = ["#f0f9e8","#bae4bc","#7bccc4","#2b8cbe"];
        else if (colorscheme === "OrRd")
            colors = ["#fef0d9","#fdcc8a","#fc8d59","#d7301f"];
        else if (colorscheme === "PuBuGn")
            colors = ["#f6eff7","#bdc9e1","#67a9cf","#02818a"];
        else if (colorscheme === "PuBu")
            colors = ["#f1eef6","#bdc9e1","#74a9cf","#0570b0"];
        else if (colorscheme === "PuRd")
            colors = ["#f1eef6","#d7b5d8","#df65b0","#ce1256"];
        else if (colorscheme === "RdPu")
            colors = ["#feebe2","#fbb4b9","#f768a1","#ae017e"]
        else if (colorscheme === "YlGnBu")
            colors = ["#ffffcc","#a1dab4","#41b6c4","#225ea8"];
            //colors = ["#fafafa","#a1dab4","#41b6c4","#225ea8"];

        // Determine the bin index (0 to 3)
        const binIndex = Math.min(Math.floor(value * colors.length), colors.length - 1);

        // Return the color corresponding to the bin
        return colors[binIndex];
    }

    PreferenceWindow {
        id: preferencePane
        width: 640
        height: 480
    }

    AboutWindow {
        id: aboutWindow
    }

    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            Action { text: qsTr("&Open...") }
            Action { text: qsTr("&Save") }
            Action { text: qsTr("Save &As...") }
            MenuSeparator { }
            Action { 
                text: qsTr("Preferences") 
                shortcut: StandardKey.Preferences
                onTriggered: {
                    preferencePane.show();
                }
            
            }
            MenuSeparator { }
            Action { 
                text: qsTr("&Quit") 
                shortcut: StandardKey.Quit
                onTriggered: {
                    appwin.close();
                }
            }
        }
        Menu {
            title: qsTr("&View")
            Action { 
                text: qsTr("Scale up") 
                onTriggered: {
                    scroll.contentWidth *= 1.5;
                    appwin.reset();
                }
            }
            Action { 
                text: qsTr("Scale down") 
                onTriggered: {
                    scroll.contentWidth /= 1.5;
                    appwin.reset();
                }
            }
            Action { 
                text: qsTr("Reset") 
                onTriggered: {
                    var targetIndices = [];
                    for (var i = 0; i < appwin.allCardData.length; ++i) {
                        targetIndices.push(appwin.allCardData[i].SegmentIndex());
                    }

                    for (var i = 0; i < cardsRoot.children.length; ++i) {
                        const idx = cardsRoot.children[i].cardData.SegmentIndex();
                        cardsRoot.children[i].opacity = targetIndices.includes(idx) ? 1.0 : 0.5;
                        appwin.segmentIndicesScores[i] = 0.0;
                    }
                    targetSegmentIndices = targetIndices;
                }
            }
        }
        Menu {
            title: qsTr("&Help")
            Action { 
                text: qsTr("&About") 
                onTriggered: {
                    aboutWindow.show();
                }
            }
        }

        background: Rectangle {
            implicitWidth: 40
            implicitHeight: 30
            color: "#f8f8f8"
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

        cardIndex: appwin.segmentIndicesOfCards[appwin.currentEditCardIndex]
        cardData: appwin.allCardData[cardIndex]
        colormap: appwin.cmapGlobal

        onSaveChanges: (heading, quotes_text, quotes_notes) => {
            const cardIndex = appwin.segmentIndicesOfCards[appwin.currentEditCardIndex];
            var targetCard = cardsRoot.children[appwin.currentEditCardIndex];

            for (var idx = 0; idx < tsRoot.children.length; ++idx) {
                if (tsRoot.children[idx].topicIndex === cardIndex) {
                    tsRoot.children[idx].title = heading;
                }
            }
            topicSegments.SetLabel(cardIndex, heading);
            topicSegments.SetQuoteNote(cardIndex, quotes_notes);
            topicSegments.SetQuoteText(cardIndex, quotes_text);

            tsRoot.children[cardIndex].tickInfos = topicSegments.ThumbnailInfo(cardIndex);
            targetCard.cardData = topicSegments.GetTopicCardData(cardIndex)
            appwin.allCardData[cardIndex] = targetCard.cardData;
        }
    }

    KeywordSearchDialog {
        id: keywordDialog
        anchors.centerIn: parent

        width: 400
        height: 300

        onKeywordSearch: (keywords) => {
            appwin.keywordMatchedIndices = topicSegments.KeywordMatches(keywords);
            var targetIndices = [];

            for (var i = 0; i < appwin.allCardData.length; ++i) {
                const cardData = appwin.allCardData[i];
                const matched = appwin.keywordMatchedIndices.indexOf(cardData.SegmentIndex()) !== -1

                if (matched) {
                    targetIndices.push(cardData.SegmentIndex());
                }
            }
            for (var i = 0; i < cardsRoot.children.length; ++i) {
                const idx = cardsRoot.children[i].cardData.SegmentIndex();
                cardsRoot.children[i].opacity = targetIndices.includes(idx) ? 1.0 : 0.5;
                appwin.segmentIndicesScores[i] = targetIndices.includes(idx) ? 1.0 : 0.0;
            }
            targetSegmentIndices = targetIndices;
        }
    }

    function init_colorscheme() {
        const cc = aoiModel.ColormapCategories()
        var cmapGlobal = new Object()

        for (const data of Object.values(cc)) {
            const mappedColors = Colorschemes.createColorscheme(data.labels, data.colormap);
            for (const [val, color] of mappedColors) {
                cmapGlobal[val] = color;
            }
        }
        appwin.cmapGlobal = cmapGlobal;
    }

    Component.onCompleted: {
        init_colorscheme();
        preferencePane.userConfig = aoiModel.UserConfig();
        appwin.reset.connect(resetNow);
        resetNow();
    }

    Connections {
        target: preferencePane
        function onSaveCurrentUserConfig(user_config) {
            aoiModel.SetUserConfig(user_config);

            init_colorscheme();

            for (const name of Object.keys(user_config["video_overlay"])) {
                topicSegments.UpdateOverlayColormap(name, user_config["video_overlay"][name]["colormap"]);
            }

            topicSegments.AdjustFilter(aoiModel.SegmentMinDurSec(), aoiModel.SegmentDisplayDurSec());
            resetNow();
        }
    }

    Connections{
        target: topicSegments
        function onQueryResultsAvailable (snippet_index, output_scores, output_indices) {

            const selectedIndices = highlightHistoryEntries.get(snippet_index).selected;

            for (var i = 0; i < segmentIndicesMarkers.length; ++i) {
                appwin.segmentIndicesMarkers[i] = "";
                appwin.segmentIndicesScores[i] = 0.0;
            }

            for (var i = 0; i < selectedIndices.length; ++i) {
                appwin.segmentIndicesMarkers[selectedIndices[i]] = "⭐";
            }

            for (var i = 0; i < cardsRoot.children.length; ++i) {
                const target_index = cardsRoot.children[i].segmentIndex;

                if (output_indices.includes(target_index)) {
                    const j = output_indices.indexOf(target_index);
                    cardsRoot.children[i].color = appwin.interpolateColor(output_scores[j], "PuBuGn")
                    cardsRoot.children[i].score = output_scores[j];
                }
                else {
                    cardsRoot.children[i].color = appwin.interpolateColor(0.0, "PuBuGn")
                    cardsRoot.children[i].score = -1;
                }

                if (selectedIndices.includes(target_index)) {
                    cardsRoot.children[i].marked = true;
                }
                else {
                    cardsRoot.children[i].marked = false;
                }
            }

            for (var i = 0; i < output_indices.length; ++i) {
                console.log("%1 - %2 : %3".arg(highlightHistoryEntries.get(snippet_index).text).arg(topicSegments.GetLabel(output_indices[i])).arg(output_scores[i]));
                appwin.segmentIndicesScores[output_indices[i]] = output_scores[i];
                if (output_scores[i] >= 0.5) {
                    //appwin.segmentIndicesMarkers[output_indices[i]] = "💡";
                }
            }
            highlightHistoryEntries.setSuggestedTopicIndices(snippet_index, output_indices);
        }
    }

    function createNote(timestamp, topicIndex) {
        annotationDialog.timestamp = timestamp;
        annotationDialog.topicIndex = topicIndex;
        annotationDialog.open();
    }

    function deleteAllCards() {
        for (var i = 0; i < cardsRoot.children.length; ++i) {
            cardsConnectorRoot.children[i].destroy()
        }
        cardsRoot.children = [];
        cardsConnectorRoot.children = [];
    }

    function deleteAllSegments() {
        for (var i = 0; i < tsRoot.children.length; ++i) {
            tsRoot.children[i].destroy()
        }
        tsRoot.children = [];
    }

    function mergeWithLeft(index) {
        topicSegments.MergeWithLeft(index);
        resetNow();
    }

    function mergeWithRight(index) {
        topicSegments.MergeWithRight(index);
        resetNow();
    }

    function changeCardVisibility(index, visible) {
        topicSegments.SetHasCard(index, visible);

        if (visible)
            segmentIndicesWithCards = [index, ...segmentIndicesWithCards]
        else
            segmentIndicesWithCards = segmentIndicesWithCards.filter(x => x !== index)

        deleteAllCards();
        findCardLayout();
    }

    function resetNow() {
        var allCards = []
        for (var i = 0; i < topicSegments.rowCount(); ++i) {
            allCards.push(topicSegments.GetTopicCardData(i));
        }
        appwin.allCardData = allCards;

        deleteAllSegments();
        deleteAllCards();

        const allTopicIndices = [...Array(topicSegments.rowCount()).keys()];
        createSegments(allTopicIndices);
        findCardLayout();


        var indicesWithCards = []
        for (var i = 0; i < topicSegments.rowCount(); ++i) {
            const segmentVisible = allTopicIndices.indexOf(i) !== -1;
            if (segmentVisible && topicSegments.HasCard(i))
                indicesWithCards.push(i);

            appwin.segmentIndicesMarkers.push("");
            appwin.segmentIndicesScores.push(0);
        }

        segmentIndicesWithCards = indicesWithCards;
        targetSegmentIndices = [...indicesWithCards];
    }

    function compressSegments() {
        var targetIndices = [];

        for (var i = 0; i < appwin.allCardData.length; ++i) {
            const cardData = appwin.allCardData[i];
            const marked = cardData.IsMarked();

            if (marked) {
                targetIndices.push(cardData.SegmentIndex());
            }
        }

        if (targetIndices.length > 0) {
            deleteAllSegments();
            deleteAllCards();

            createSegments(targetIndices);
            findCardLayout();
        }
        else {
            console.log("WARNING: Build nothing to compress!")
        }
        targetSegmentIndices = targetIndices;
    }
 

    function createSegments(targetTopicIndices) {
        const start = topicSegments.MinTimestamp();
        const end = topicSegments.MaxTimestamp();

        var currX = 0;
        var lastSegmentVisible = true;
        var indicesWithCards = []

        for (var i = 0; i < topicSegments.rowCount(); ++i) {
            const start_ts = topicSegments.GetPosStart(i);
            const end_ts = topicSegments.GetPosEnd(i);
            const segmentVisible = targetTopicIndices.indexOf(i) !== -1;

            if (segmentVisible) {
                const width = Math.floor(tsRoot.width * (end_ts - start_ts) / (end - start));
                var ccComponent = Qt.createComponent("components/TimelineSegment.qml");
                if (ccComponent.status === Component.Error) {
                    console.log("Error loading component:", ccComponent.errorString());
                }
                const has_hard = topicSegments.HasCard(i);

                var ccObject = ccComponent.createObject(tsRoot, 
                    {title: topicSegments.GetLabel(i), 
                    dia: topicSegments.GetMultiRecData(i), 
                    tan: topicSegments.GetNotes(i),
                    stacksTop: topicSegments.GetTimeSeries("top", i),
                    stacksBottom:  topicSegments.GetTimeSeries("bottom", i),
                    min_ts: start_ts,
                    max_ts: end_ts,
                    tickInfos: topicSegments.ThumbnailInfo(i),
                    color: has_hard ? "#f8f8f8" : "#fff",
                    meta: aoiModel,
                    cmap: appwin.cmapGlobal,
                    x: currX,
                    width: width,
                    height: appwin.timelineSegmentHeight,
                    topicIndex: i,
                    hasCard: has_hard
                });
                ccObject.noteRequested.connect(appwin.createNote);
                ccObject.cardVisibilityChanged.connect(appwin.changeCardVisibility);
                ccObject.mergeWithLeft.connect(appwin.mergeWithLeft);
                ccObject.mergeWithRight.connect(appwin.mergeWithRight);
                currX += width;
            }
            else if (lastSegmentVisible) {
                var ccComponent = Qt.createComponent("components/PlaceHolder.qml");
                var ccObject = ccComponent.createObject(tsRoot, {x: currX, width: appwin.placeholderWidth, height: appwin.timelineSegmentHeight})
                currX += appwin.placeholderWidth;
            }

            lastSegmentVisible = segmentVisible;

            if (ccObject == null) {
                console.log("Error creating TimelineSegment / Placeholder");
            }
        }
    }

    function findCardLayout() {
        var indices = [];
        var target_loc = [];
        var target_pos_x = [];
        var target_pos_y = [];
        var target_width = [];
        var target_card_width = [];

        for (var i = 0; i < tsRoot.children.length; ++i) {
            if (tsRoot.children[i].hasCard) {
                tsRoot.children[i].cardIndex = indices.length;
                target_loc.push(tsRoot.children[i].x + tsRoot.children[i].width * 0.5)
                target_card_width.push(topicSegments.GetCardSize(tsRoot.children[i].topicIndex));
                target_pos_x.push(tsRoot.children[i].x);
                target_pos_y.push(tsRoot.children[i].y);
                target_width.push(tsRoot.children[i].width);
                indices.push(tsRoot.children[i].topicIndex);
            }
        }

        if (target_loc.length === 0) {
            console.log("Warning: No cards to layout!")
            return
        }

        const cards_loc = topicSegments.GetCardLayout(target_loc, target_card_width, scroll.contentWidth * 1.5);
        
        for (var i = 0; i < target_loc.length; ++i) {
            const cardData = appwin.allCardData[indices[i]];
            var tcComponent = Qt.createComponent("components/TopicCard.qml");
            var tcObject = tcComponent.createObject(cardsRoot, 
                                                    {
                                                        x: cards_loc[i] - (target_card_width[i] - 50) / 2, 
                                                        y: 0,
                                                        width: target_card_width[i] - 50,
                                                        cardData: cardData, 
                                                        segmentIndex: indices[i],
                                                        cardIndex: i,
                                                        cmap: appwin.cmapGlobal,
                                                        hasActivity: topicSegments.HasActivity(),
                                                        hasAttention: topicSegments.HasAttention(),
                                                    });

            if (tcObject == null) {
                console.log("Error creating TopicCard");
            }

            tcObject.onClicked.connect(function(index) {
                appwin.currentEditCardIndex = index;
                drawer.open()
            });

            tcObject.onMarkToggled.connect(function(index) {
                const mark = topicSegments.ToggleMark(index);

                if (mark) {
                    appwin.segmentIndicesMarkers[index] = "⭐";
                }
                else {
                    appwin.segmentIndicesMarkers[index] = "";
                }
            });

            var ccComponent = Qt.createComponent("components/CardConnector.qml");
            var ccObject = ccComponent.createObject(cardsConnectorRoot, {fromX: cards_loc[i], fromY: 40, toLeftX: target_pos_x[i], toRightX: target_pos_x[i] + target_width[i], toY: 0});

            if (ccObject == null) {
                console.log("Error creating CardConnector");
            }
        }
        appwin.segmentIndicesOfCards = indices;
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

            onClicked: function() {
                appwin.reset();
                //scroll.hScrollBar.position = 0.0;
            }
        }

        FloatingButton {
            text: ""
            color: "#005fee"
            width: 75
            height: 75
            source: "../icons/compress.png"

            onClicked: function() {
                appwin.compressSegments();
                //scroll.hScrollBar.position = 0.0;
            }
        }

        FloatingButton {
            text: ""
            color: "#005fee"
            width: 75
            height: 75
            source: "../icons/search.png"

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

            streamTopId: aoiModel.GetTopMultiTimeLabel()
            streamBottomId: aoiModel.GetBottomMultiTimeLabel()

            identifiers: aoiModel.Identifiers()

            h1: 175
            h2: 30
            h3: 60 + topicSegments.SpeechLineCount() * (appwin.timelineHeight + appwin.timelineVSpace)
            h4: 500
        }

        Flickable {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true

            contentWidth: 14000
            contentHeight: 1000

            flickableDirection: Flickable.HorizontalFlick
            boundsBehavior: Flickable.StopAtBounds

            clip: true

            ScrollBar.horizontal: ScrollBar {
                policy: ScrollBar.AlwaysOn 
            }

            ColumnLayout {
                spacing: 0

                Item {
                    id: tsRoot
                    z: 5
                    width: scroll.contentWidth
                    height: appwin.timelineSegmentHeight
                }

                Item {
                    z: 1
                    id: cardsConnectorRoot
                    width: scroll.contentWidth
                    height: 50
                }

                Item {
                    id: cardsRoot
                    width: scroll.contentWidth
                    height: 400
                }

                Item { Layout.fillHeight: true }    // <-- filler here
            }
        }

        ListView {
            id: repB

            Layout.preferredWidth: boxW
            Layout.fillHeight: true

            spacing: 0
            model: appwin.segmentIndicesMarkers

            property real boxW: 20 
            property real boxH: 20 

            clip: true
            
            delegate: Rectangle {
                required property int index
                required property string modelData

                width: repB.boxW
                height: repB.boxH
                color: (index < appwin.segmentIndicesScores.length) ? appwin.interpolateColor(appwin.segmentIndicesScores[index], "PuBuGn") : "#f8f8f8"
                border.color: '#d9d9d9'

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        scroll.ScrollBar.horizontal.position = tsRoot.children[index].x / tsRoot.width;
                        for (var i = 0; i < tsRoot.children.length; ++i) {
                            if (tsRoot.children[i].topicIndex === segmentIndicesWithCards[index]) {
                                scroll.ScrollBar.horizontal.position = tsRoot.children[i].x / tsRoot.width;
                            }
                        }
                    }
                }

                Label {
                    anchors.fill: parent
                    font.pixelSize: 16

                    text: modelData
                    opacity: 0.5

                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
}
