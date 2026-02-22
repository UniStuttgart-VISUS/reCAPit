// CustomVideo.qml
// Video player component that uses an external SharedMediaPlayer

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
    required property SharedMediaPlayer mediaPlayer

    property var videoOverlaySources

    property var active: false
    property int selectionMode: Constants.CropSelectionMode.Inactive

    property bool aoiOverlayEnabled: false

    property alias selectionPosX: selectionRect.x
    property alias selectionPosY: selectionRect.y
    property alias selectionWidth: selectionRect.width
    property alias selectionHeight: selectionRect.height

    property bool hasVideoOverlays: videoOverlaySources ? Object.keys(videoOverlaySources).length > 0 : false
    property string activeVideoOverlay: "None"

    signal selectionChanged(var frame, real pos, real xpos, real ypos, real width, real height, string overlay_src)
    signal videoEnterFullscreen()

    color: "black"
    radius: 5
    focus: true

    function jumpToPosition(posMsec) {
        mediaPlayer.jumpToPosition(posMsec);
    }

    function setPosition(posMsec) {
        mediaPlayer.setPosition(posMsec);
    }

    onActiveChanged: {
        if (!active) {
            mediaPlayer.pause();
        }
    }

    onVisibleChanged: {
        if (visible) {
            // When this view becomes visible, connect the mediaPlayer to our VideoOutput
            mediaPlayer.videoOutput = videoOutput;
        }
    }

    Component.onCompleted: {
        if (visible) {
            mediaPlayer.videoOutput = videoOutput;
        }
    }

    component FrameOverlays: Item {
        required property var vidOut

        Rectangle {
            width: Math.max(parent.width * 0.20, 150)
            height: Math.max(parent.width * 0.05, 30)

            anchors.left: parent.left
            anchors.top: parent.top

            anchors.topMargin: 25

            color: "#88000000"

            topRightRadius: 5
            bottomRightRadius: 5

            visible: videoRoot.selectionMode !== Constants.CropSelectionMode.Inactive

            Label {
                anchors.fill: parent
                anchors.margins: parent.width * 0.05

                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter

                color: "#fff"
                text: {
                    switch(videoRoot.selectionMode) {
                        case Constants.CropSelectionMode.ActiveNoCorner:
                            return " Set 1st corner"
                        case Constants.CropSelectionMode.ActiveFirstCorner:
                            return " Set 2nd corner"
                    }
                    return "";
                }
                fontSizeMode: Text.Fit

                minimumPixelSize: 10
                font.pixelSize: 121
                font.bold: true
            }
        }

        Item {
            id: aoiFills

            function scalePoints(norm_points, contentRect) {
                return norm_points.map(p => {
                    p.x = p.x*contentRect.width + contentRect.x;
                    p.y = p.y*contentRect.height + contentRect.y;
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
                            path: aoiFills.scalePoints(aoiModel.AoiPolygonPoints(modelData), vidOut.contentRect);
                        }
                    }
                }
            }
        }

        Image {
            width: vidOut.contentRect.width
            height: vidOut.contentRect.height
            x: vidOut.contentRect.x
            y: vidOut.contentRect.y
            source: (hasVideoOverlays && activeVideoOverlay in videoOverlaySources) ? videoOverlaySources[activeVideoOverlay] : ""
            // Only show overlays on top-down video
            visible: hasVideoOverlays && activeVideoOverlay !== "None" && bar.currentIndex === 0
        }

        Item {
            id: gazeOverlay
            // Only show heatmap on top-down video
            visible: bar.currentIndex === 0

            width: vidOut.contentRect.width
            height: vidOut.contentRect.height

            x: vidOut.contentRect.x
            y: vidOut.contentRect.y
        }
    }

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: bar
            Layout.fillWidth: true

            currentIndex: mediaPlayer.currentSourceIndex

            onCurrentIndexChanged: {
                mediaPlayer.currentSourceIndex = bar.currentIndex;
            }

            CustomTabButton {
                text: String.fromCodePoint(0x1F4F7) + " Top-Down Camera"
            }

            Repeater {
                model: mediaPlayer.peripheralSources
                delegate: CustomTabButton {
                    text: String.fromCodePoint(0x1F4F7) + " %1. Side Camera".arg(index+1)
                }
            }

            background: Rectangle {
                color: "black"
                radius: 5
            }
        }

        Rectangle {
            id: frameContainer
            Layout.fillWidth: true
            Layout.fillHeight: true

            color: "black"

            VideoOutput {
                id: videoOutput
                anchors.fill: parent
                fillMode: VideoOutput.PreserveAspectFit
            }

            FrameOverlays {
                anchors.fill: parent
                vidOut: videoOutput
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
                    if (videoRoot.selectionMode === Constants.CropSelectionMode.Inactive) {
                        mediaPlayer.togglePlayPause();
                    }
                    else if (videoRoot.selectionMode === Constants.CropSelectionMode.ActiveNoCorner) {
                        selectionRect.x = mouse.x;
                        selectionRect.y = mouse.y;
                        selectionRect.width = 0;
                        selectionRect.height = 0;
                        mouseArea.anchorX = mouse.x;
                        mouseArea.anchorY = mouse.y;
                        videoRoot.selectionMode = Constants.CropSelectionMode.ActiveFirstCorner;
                    }
                    else if (videoRoot.selectionMode === Constants.CropSelectionMode.ActiveFirstCorner){
                        const cr = videoOutput.contentRect;
                        if (mouse.button === Qt.LeftButton) {
                            videoRoot.selectionChanged(videoOutput.videoSink, 
                                                    mediaPlayer.position,
                                                    (selectionRect.x - cr.x) / cr.width, 
                                                    (selectionRect.y - cr.y) / cr.height, 
                                                    selectionRect.width / cr.width, 
                                                    selectionRect.height / cr.height,
                                                    activeVideoOverlay);
                        }
                        selectionRect.width = 0;
                        selectionRect.height = 0;
                        videoRoot.selectionMode = Constants.CropSelectionMode.Inactive;
                    }
                }

                onPositionChanged: (mouse) => {
                    if (videoRoot.selectionMode == Constants.CropSelectionMode.ActiveFirstCorner) {
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

        VideoProgressBar {
            id: videoProgressBar
            Layout.fillWidth: true
            Layout.leftMargin: 10
            Layout.rightMargin: 10

            progressValue: videoRoot.mediaPlayer.currentPosition
            progressDisplayText: Utils.timeFormat(1e-3 * mediaPlayer.position)

            mediaStatusIcon: (mediaPlayer.playbackState === MediaPlayer.PlayingState) ? "../icons/media_pause.png" : "../icons/media_play.png"
            videoOverlaySources: videoRoot.videoOverlaySources ? Object.keys(videoRoot.videoOverlaySources).concat(["None"]) : ["None"]
            overlaySrcIcon: "../icons/gear.png"
            cropIcon: videoRoot.selectionMode === Constants.CropSelectionMode.Inactive ? "../icons/pen.png" : "../icons/pen_blue.png"
            aoiIcon: videoRoot.aoiOverlayEnabled ? "../icons/aoi_active.png" : "../icons/aoi_inactive.png"
            fullScreenIcon: "../icons/box_inactive.png"

            onProgressChanged: (pos) => {
                mediaPlayer.setPositionNormalized(pos);
            }

            onVideoEnterFullscreen: {
                videoRoot.videoEnterFullscreen();
            }

            onFrameCropToggled: {
                if (videoRoot.selectionMode === Constants.CropSelectionMode.Inactive) {
                    videoRoot.selectionMode = Constants.CropSelectionMode.ActiveNoCorner;
                    mediaPlayer.pause();
                }
                else
                    videoRoot.selectionMode = Constants.CropSelectionMode.Inactive;

                selectionRect.width = 0;
                selectionRect.height = 0;
            }

            onVideoOverlaySelected: (name) => {
                videoRoot.activeVideoOverlay = name;
            }

            onAoiVisibleToggled: {
                videoRoot.aoiOverlayEnabled = !videoRoot.aoiOverlayEnabled;
            }

            onVideoStatusToggled: {
                mediaPlayer.togglePlayPause();
            }
        }
    }
}
