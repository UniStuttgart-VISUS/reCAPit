import QtQuick
import QtQuick.Window
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtMultimedia
import QtQuick.Shapes 1.2
import com.kochme.media 1.0

import "."
import "../js/utils.js" as Utils


RowLayout {
    id: videoProgressBar
    spacing: 10

    required property var videoOverlaySources
    required property real progressValue
    required property string progressDisplayText

    required property string aoiIcon
    required property string mediaStatusIcon
    required property string overlaySrcIcon
    required property string cropIcon
    required property string fullScreenIcon

    signal progressChanged(real position)
    signal videoStatusToggled()
    signal videoOverlaySelected(string name)
    signal aoiVisibleToggled()
    signal frameCropToggled()
    signal videoEnterFullscreen()

    Image {
        id: playPauseBtn

        Layout.preferredHeight: 20
        Layout.preferredWidth: 20

        source: videoProgressBar.mediaStatusIcon
        fillMode: Image.PreserveAspectFit

        MouseArea {
            anchors.fill: parent
            onClicked: {
                videoProgressBar.videoStatusToggled();
            }
        }
    }

    Text {
        //text: Utils.timeFormat(videoPosition/1000);
        text: progressDisplayText
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
        value: 100 * progressValue
        to: 100

        onMoved: {
            //videoProgressBar.videoPositionChanged2(startPosition + control.position * (endPosition - startPosition));
            videoProgressBar.progressChanged(control.position);
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

        onClicked: (button) => {
            videoProgressBar.videoOverlaySelected(button.text);
        }
    }

    Item {
        Layout.preferredHeight: 20
        Layout.preferredWidth: 20
        id: control2

        property list<string> model: videoProgressBar.videoOverlaySources
        visible: videoProgressBar.videoOverlaySources.length > 0

        MouseArea {
            anchors.fill: parent
            onClicked: {
                dropdownPopup.open();
            }
        }

        Image {
            anchors.fill: parent
            source: videoProgressBar.overlaySrcIcon
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

        source: videoProgressBar.cropIcon

        MouseArea {
            anchors.fill: parent
            onClicked: {
                videoProgressBar.frameCropToggled();
            }
        }
    }

    Image {
        Layout.preferredHeight: 20
        Layout.preferredWidth: 20

        source: videoProgressBar.aoiIcon

        MouseArea {
            anchors.fill: parent
            onClicked: {
                videoProgressBar.aoiVisibleToggled();
            }
        }
    }
    Image {
        Layout.preferredHeight: 20
        Layout.preferredWidth: 20

        source: videoProgressBar.fullScreenIcon

        MouseArea {
            anchors.fill: parent
            onClicked: {
                videoProgressBar.videoEnterFullscreen();
            }
        }
    }
}