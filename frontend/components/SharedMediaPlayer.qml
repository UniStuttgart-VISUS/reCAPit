// SharedMediaPlayer.qml
// A reusable MediaPlayer component that can be shared between multiple VideoOutputs

import QtQuick
import QtMultimedia

Item {
    id: root

    // Video source properties
    required property string topDownSource
    required property list<string> peripheralSources
    
    // Playback range
    property int startPosition: 0
    property int endPosition: 0
    
    // Current state (read-only from outside)
    readonly property alias playbackState: video.playbackState
    readonly property alias position: video.position
    readonly property alias duration: video.duration
    readonly property alias mediaStatus: video.mediaStatus
    
    // Normalized position within the start/end range (0.0 to 1.0)
    property real currentPosition: 0
    
    // The VideoOutput to render to - can be changed dynamically
    property var videoOutput: null
    
    // Current source index (0 = top-down, 1+ = peripheral cameras)
    property int currentSourceIndex: 0

    signal positionUpdated(int pos)

    MediaPlayer {
        id: video

        property real savedPosition: -1
        property int savedPlaybackState: -1

        source: root.currentSourceIndex === 0 
            ? root.topDownSource 
            : root.peripheralSources[root.currentSourceIndex - 1]
        
        videoOutput: root.videoOutput
        
        audioOutput: AudioOutput {
            volume: 1.0
        }

        onPositionChanged: {
            if (position > root.endPosition && root.endPosition > 0) {
                video.pause();
            }
            if (root.endPosition > root.startPosition) {
                root.currentPosition = (position - root.startPosition) / (root.endPosition - root.startPosition);
            }
            root.positionUpdated(position);
        }

        onMediaStatusChanged: (status) => {
            if (status === MediaPlayer.LoadedMedia && video.savedPosition !== -1) {
                video.setPosition(video.savedPosition);
                video.savedPosition = -1;
            }
        }
    }

    onStartPositionChanged: {
        video.setPosition(startPosition);
        currentPosition = 0;
    }

    onCurrentSourceIndexChanged: {
        video.savedPosition = video.position;
        video.savedPlaybackState = video.playbackState;
    }

    // Public methods
    function play() {
        video.play();
    }

    function pause() {
        video.pause();
    }

    function togglePlayPause() {
        if (video.playbackState === MediaPlayer.PlayingState) {
            video.pause();
        } else {
            video.play();
        }
    }

    function setPosition(posMsec) {
        video.setPosition(posMsec);
    }

    function jumpToPosition(posMsec) {
        video.setPosition(posMsec);
        video.play();
    }

    function setPositionNormalized(normalizedPos) {
        video.setPosition(startPosition + normalizedPos * (endPosition - startPosition));
    }
}
