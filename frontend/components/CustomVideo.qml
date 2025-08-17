// VideoPlayer.qml

import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtMultimedia
import QtQuick.Shapes 1.2
import com.kochme.media 1.0

import "."
import "../js/utils.js" as Utils

Rectangle {
    id: videoRoot

    required property var colormapAOIs

    required property string topDownSource
    required property list<string> peripheralSources

    property alias playbackState: video.playbackState
    property int startPosition
    property int endPosition
    property var active: false
    property int selectionMode: 0
    property var videoSink
    property var videoOverlaySources

    property bool aoiOverlayEnabled: false

    property alias selectionPosX: selectionRect.x
    property alias selectionPosY: selectionRect.y
    property alias selectionWidth: selectionRect.width
    property alias selectionHeight: selectionRect.height

    property bool hasVideoOverlays: Object.keys(videoOverlaySources).length > 0

    signal selectionChanged(var frame, real pos, real xpos, real ypos, real width, real height, string overlay_src)

    color: "black"
    radius: 5
    focus: true

    onActiveChanged: {
        if (!active) {
            video.pause();
        }
    }

    onStartPositionChanged: {
        video.setPosition(startPosition);
        control.value = 0
    }

    MediaPlayer {
        id: video

        property real savedPosition: -1
        property int savedPlaybackState: -1

        source: videoRoot.topDownSource
        videoOutput: videoOutput
        audioOutput: AudioOutput {
            volume: 1.0
        }

        onPositionChanged: (pos) => {
            if (pos > endPosition) {
                video.pause();
            }
            control.value = 100 * (pos - startPosition) / (endPosition - startPosition);
            const gaze_idx = Math.floor(0.001 * position * 4);
        }

        onMediaStatusChanged: (status) => {
            if (status === MediaPlayer.LoadedMedia && video.savedPosition !== -1) {
                video.setPosition(video.savedPosition);
                /*
                if (video.savedPlaybackState === MediaPlayer.PlayingState) {
                    video.play();
                }
                */
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: bar
            Layout.fillWidth: true

            onCurrentIndexChanged: {
                video.savedPosition = video.position;
                video.savedPlaybackState = video.playbackState
                video.source = (bar.currentIndex === 0) ? videoRoot.topDownSource : videoRoot.peripheralSources[bar.currentIndex - 1]
            }

            CustomTabButton {
                text: String.fromCodePoint(0x1F4F7) + " Top-Down Camera"
            }

            Repeater {
                model: videoRoot.peripheralSources
                delegate: CustomTabButton {
                    text: String.fromCodePoint(0x1F4F7) + " %1. Side Camera".arg(index+1)
                    //enabled: videoRoot.hasGazeHeatmap
                }
            }

            background: Rectangle {
                color: "black"
                radius: 5
            }
            /*
            CustomTabButton {
                text: "Movement"
                enabled: videoRoot.hasMoveHeatmap
            }
            */
        }

        Rectangle {
            id: frameContainer
            Layout.fillWidth: true
            Layout.fillHeight: true

            color: "black"
            //border.color: "red"
            //border.width: videoRoot.selectionMode > 0 ? 3 : 0

            VideoOutput {
                id: videoOutput
                anchors.fill: parent
            }

            Item {
                id: aoiFills
                anchors.fill: parent

                function scalePoints(norm_points, width, height) {
                    return norm_points.map(p => {
                        p.x *= width;
                        p.y *= height;
                        return p;
                    });
                }

                Repeater {
                    model: aoiModel.Labels()
                    delegate: Shape {
                        required property string modelData;
                        anchors.fill: parent

                        function makeColorTransparent(rgb_hex, alpha_hex) {
                            return "#" + alpha_hex + rgb_hex.slice(1);
                        }

                        ShapePath {
                            fillColor: makeColorTransparent(videoRoot.colormapAOIs[modelData], videoRoot.aoiOverlayEnabled ? "88" : "00")
                            strokeColor: makeColorTransparent(videoRoot.colormapAOIs[modelData], videoRoot.aoiOverlayEnabled ? "ff" : "00")
                            strokeWidth: 1

                            PathPolyline {
                                path: aoiFills.scalePoints(aoiModel.AoiPolygonPoints(modelData), aoiFills.width, aoiFills.height);
                            }
                        }
                    }
                }
            }

            Image {
                width: videoOutput.contentRect.width
                height: videoOutput.contentRect.height
                x: videoOutput.contentRect.x
                y: videoOutput.contentRect.y
                source: (hasVideoOverlays && childGroup.checkedButton && childGroup.checkedButton.text in videoOverlaySources) ? videoOverlaySources[childGroup.checkedButton.text] : ""
                // Only show overlays on top-down video
                visible:  hasVideoOverlays && childGroup.checkedButton.text !== "None" && bar.currentIndex === 0
            }

            Item {
                id: gazeOverlay

                // Only show heatmap on top-down video
                visible: bar.currentIndex === 0

                width: videoOutput.contentRect.width
                height: videoOutput.contentRect.height

                x: videoOutput.contentRect.x
                y: videoOutput.contentRect.y
            }

            Rectangle {
                id: selectionRect
                color: "lightblue"
                border.color: "blue"
                opacity: 0.5
                width: 0
                height: 0
            }

            MouseArea {
                id: mouseArea

                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton

                property int anchorX;
                property int anchorY;

                onClicked: (mouse) => {
                    if (videoRoot.selectionMode === 0) {
                        video.playbackState == MediaPlayer.PlayingState ? video.pause() : video.play()
                    }
                    else if (videoRoot.selectionMode === 1) {
                        selectionRect.x = mouse.x;
                        selectionRect.y = mouse.y;
                        selectionRect.width = 0;
                        selectionRect.height = 0;
                        mouseArea.anchorX = mouse.x;
                        mouseArea.anchorY = mouse.y;
                        videoRoot.selectionMode = 2;
                    }
                    else {
                        const cr = videoOutput.contentRect;

                        if (mouse.button === Qt.LeftButton) {
                            
                            var overlay_src = childGroup.checkedButton.text;

                            videoRoot.selectionChanged(videoOutput.videoSink, 
                                                    video.position,
                                                    (selectionRect.x - cr.x) / cr.width, 
                                                    (selectionRect.y - cr.y) / cr.height, 
                                                    selectionRect.width / cr.width, 
                                                    selectionRect.height / cr.height,
                                                    overlay_src);
                        }

                        selectionRect.width = 0;
                        selectionRect.height = 0;
                        videoRoot.selectionMode = 1;
                    }
                }

                onPositionChanged: (mouse) => {
                    if (videoRoot.selectionMode == 2) {
                        selectionRect.width = Math.abs(mouse.x - mouseArea.anchorX);
                        selectionRect.height = Math.abs(mouse.y - mouseArea.anchorY)

                        if (mouse.x < mouseArea.anchorX) {
                            selectionRect.x = mouse.x;
                        }
                        else {
                            selectionRect.x = mouseArea.anchorX;
                        }
                        if (mouse.y < mouseArea.anchorY) {
                            selectionRect.y = mouse.y;
                        }
                        else {
                            selectionRect.y = mouseArea.anchorY;
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            spacing: 10

            Text {
                text: Utils.timeFormat(video.position/1000);
                font.family: "Arial"
                font.pointSize: 10
                font.bold: true
                color: "white"
            }

            Slider {
                id: control
                Layout.preferredHeight: 30
                Layout.fillWidth: true

                from: 1
                value: 0
                to: 100

                onMoved: {
                    video.setPosition(startPosition + control.position * (endPosition - startPosition));
                }

                background: Rectangle {
                    x: control.leftPadding
                    y: control.topPadding + control.availableHeight / 2 - height / 2
                    implicitWidth: 200
                    implicitHeight: 4
                    width: control.availableWidth
                    height: implicitHeight
                    radius: 2
                    color: "#bdbebf"

                    Rectangle {
                        width: control.visualPosition * parent.width
                        height: parent.height
                        color: "#fff"
                        radius: 2
                    }
                }

                handle: Rectangle {
                    x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
                    y: control.topPadding + control.availableHeight / 2 - height / 2
                    implicitWidth: 16
                    implicitHeight: 16
                    radius: 8
                    color: control.pressed ? "#f0f0f0" : "#f6f6f6"
                    border.color: "#bdbebf"
                }
            }
            ButtonGroup {
                id: childGroup
                exclusive: true
            }

            Item {
                Layout.preferredHeight: 20
                Layout.preferredWidth: 20
                id: control2

                property list<string> model: Object.keys(videoOverlaySources).concat(["None"])
                visible: hasVideoOverlays

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        dropdownPopup.open();
                    }
                }

                Image {
                    anchors.fill: parent
                    source: "../icons/gear.png"
                    fillMode: Image.PreserveAspectFit
                }

                Popup {
                    id: dropdownPopup

                    y: control2.height - 1
                    width: 125
                    implicitHeight: contentItem.implicitHeight + 10
                    padding: 5

                    contentItem: ListView {
                        clip: true
                        spacing: 5
                        implicitHeight: contentHeight
                        model: control2.model 
                        delegate: CheckBox {
                            checked: true
                            anchors.margins: 1
                            required property string modelData
                            text: modelData
                            ButtonGroup.group: childGroup
                            font.pixelSize: 12
                        }
                        currentIndex: 0

                        ScrollIndicator.vertical: ScrollIndicator { }
                    }

                    background: Rectangle {
                        border.color: "#333"
                        radius: 2
                    }
                }
            }

            Image {
                Layout.preferredHeight: 20
                Layout.preferredWidth: 20

                source: videoRoot.selectionMode === 0 ? "../icons/box_inactive.png" : "../icons/box_active.png"

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (videoRoot.selectionMode == 0)
                            videoRoot.selectionMode = 1;
                        else
                            videoRoot.selectionMode = 0;

                        selectionRect.width = 0;
                        selectionRect.height = 0;

                        video.pause();
                    }
                }
            }

            Image {
                Layout.preferredHeight: 20
                Layout.preferredWidth: 20

                source: videoRoot.aoiOverlayEnabled ? "../icons/aoi_active.png" : "../icons/aoi_inactive.png"

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        videoRoot.aoiOverlayEnabled = !videoRoot.aoiOverlayEnabled;
                    }
                }
            }

        }
    }
}