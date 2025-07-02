import QtQuick 6.0
import QtQuick.Controls 6.0
import QtQuick.Layouts 6.0

Item {
    id: root

    property var text
    property alias font: editor.font
    property alias textMargin: editor.textMargin
    property var edits: []

    property string baseText: text
    property list<var> categories : [{name: 'Empty', color: '#ccc'}]
    property list<string> colors: ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF", "#D5BAFF"]

    property int highlightId : 0

    signal codeSnippetSelected(int snippetIndex)

    Rectangle {
        anchors.fill: parent
        color: "#f0f0f0"
        radius: 5
    }

    function codeText(categoryIndex) {
        const color = root.categories[categoryIndex].color;
        const name = root.categories[categoryIndex].name;

        const startIndex = editor.selectionStart;
        const length = editor.selectedText.length;

        console.log(`start: ${startIndex}, length: ${length}`);

        if (!isNaN(startIndex) && !isNaN(length) && length > 0) {

            const plainText = editor.getText(0, editor.length); 
            const highlight = plainText.substring(startIndex, startIndex + length);

            //highlightHistoryEntries.append({name: name, text: highlight, color: color, hid: root.highlightId});
            highlightHistoryEntries.addSnippet(name, highlight, color, root.highlightId);
            editor.addHighlight(startIndex, length, color, root.highlightId);
            root.highlightId += 1;
        }
    }

    Loader { 
        id: addCategoryDialog2
        sourceComponent: codeDialog 
    }

    Connections {
        target: addCategoryDialog2.item
        function onCodeAdded (newCategoryName, colorIndex) {
            if (newCategoryName !== "") {
                root.categories.push({name: newCategoryName, color: root.colors[colorIndex]})
                categoryDropdown.currentIndex = root.categories.length - 1;
                codeText(categoryDropdown.currentIndex);
            }
        }
    }

    Menu {
        id: popup
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        Menu {
            title:  String.fromCodePoint(0x1F58D) + " Assign existing code"
            Repeater {
                model: root.categories
                delegate: MenuItem {
                    required property var modelData
                    required property int index

                    onTriggered: codeText(index);

                    contentItem: RowLayout {
                        anchors.fill: parent

                        anchors.leftMargin: 5
                        anchors.rightMargin: 5

                        Rectangle {
                            Layout.preferredWidth: 12
                            Layout.preferredHeight: 12
                            radius: 6
                            color: modelData.color
                            border.color: "#cccccc"
                        }
                        Label {
                            Layout.fillWidth: true
                            text: modelData.name
                            verticalAlignment: Label.AlignVCenter
                            horizontalAlignment: Label.AlignLeft
                            font.pixelSize: 10
                        }
                    }
                }
            }
        }

        MenuSeparator {}
        MenuItem {
            text:  String.fromCodePoint(0x1F58D) + " Assign new code"
            onTriggered: {
                addCategoryDialog2.item.open()
                addCategoryDialog2.item.title = "Assign new code";
            }
        }
    }

    /*
    ListModel {
        id: highlightHistoryEntries
    }
    */

    ColumnLayout {
        id: container

        property var highlightColor: "#91b1d1"
        anchors.fill: parent
        spacing: 10

        ToolBar {
            Layout.fillWidth: true
            visible: false

            RowLayout {
                spacing: 10
                ComboBox {
                    id: categoryDropdown
                    model: root.categories
                    Layout.preferredWidth: 150
                    textRole: "name"

                    delegate: ItemDelegate {
                        id: delegate2

                        required property var modelData
                        required property int index

                        width: categoryDropdown.width

                        contentItem: RowLayout {
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                radius: 8
                                color: modelData.color
                                border.color: "#cccccc"
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.name
                                verticalAlignment: Label.AlignVCenter
                                horizontalAlignment: Label.AlignLeft
                            }
                        }
                        highlighted: categoryDropdown.highlightedIndex === index
                    }
                }

                ToolButton {
                    id: assignCodeBtn

                    text:  String.fromCodePoint(0x1F58D) + " Assign <u>%1</u> code".arg(categoryDropdown.currentText);

                    contentItem: Text {
                        text: assignCodeBtn.text
                        textFormat: Text.StyledText
                    }
                    onClicked: codeText(categoryDropdown.currentIndex)
                }

                ToolButton {
                    text:  String.fromCodePoint(0x1F58D) + " Create new code"
                    onClicked: {
                        addCategoryDialog.item.open()
                        addCategoryDialog.item.title = "Create new code";
                    }
                }
            }
        }

        RowLayout {
            spacing: 10

            Layout.fillWidth: true
            Layout.fillHeight: true

            Rectangle {
                id: mainRect

                Layout.fillHeight: true
                Layout.fillWidth: true

                color: "white"
                radius: 5
                border.color: "#cccccc"
                border.width: 1

                Loader { 
                    id: addCategoryDialog
                    sourceComponent: codeDialog 
                    anchors.centerIn: mainRect
                }

                Connections {
                    target: addCategoryDialog.item
                    function onCodeAdded (newCategoryName, colorIndex) {
                        if (newCategoryName !== "") {
                            root.categories.push({name: newCategoryName, color: root.colors[colorIndex]})
                            categoryDropdown.currentIndex = root.categories.length - 1;
                        }
                    }
                }

                Flickable {
                    anchors.fill: parent
                    contentWidth: parent.width
                    contentHeight: editor.paintedHeight
                    clip: true

                    TextEdit {
                        id: editor
                        width: parent.width
                        wrapMode: TextEdit.Wrap
                        textFormat: TextEdit.RichText
                        color: "black"
                        font.pixelSize: 16
                        text: baseText
                        selectByMouse: true
                        mouseSelectionMode: TextEdit.SelectCharacters
                        persistentSelection: true

                        MouseArea {
                            anchors.fill: parent
                            acceptedButtons: Qt.RightButton
                            propagateComposedEvents: true
                            cursorShape: Qt.IBeamCursor

                            onClicked: (mouse) => {
                                if (mouse.button == Qt.RightButton)
                                {
                                    const cursorRectangle = editor.cursorRectangle;
                                    popup.x = mouse.x + cursorRectangle.width;
                                    popup.y = mouse.y + cursorRectangle.height;
                                    mouse.accepted = true;
                                    popup.open()
                                }
                            }
                        }


                        function find_annotation(hid) {
                            const formattedText = editor.getFormattedText(0, editor.length);
                            
                            var pattern = new RegExp(String.raw`<a href="${hid}"><span[\w\s\=\"\-\:\#\;]*>`, "g");
                            var match = pattern.exec(formattedText)

                            if (match == null) {
                                console.error(`Could not find <a> starting tag of id=${hid} in editor text!`);
                                return;
                            }

                            const ref_star_len = match[0].length;
                            const ref_start_index = match.index;

                            pattern = /<\/a>/;
                            match = pattern.exec(formattedText.slice(ref_start_index));

                            if (match == null) {
                                console.error(`Could not find <a> closing tag of id=${hid} in editor text!`);
                                return;
                            }

                            return {'start': ref_start_index, 'end': ref_start_index + match.index, 'length': ref_star_len};
                        }
                        
                        onEditingFinished: {
                            const formattedText = editor.getFormattedText(0, editor.length);

                            for (var idx = 0; idx < highlightHistoryEntries.rowCount(); idx++) {
                                const entry = highlightHistoryEntries.get(idx);
                                const res = editor.find_annotation(entry.hid);
                                const ref_text = formattedText.slice(res.start+res.length, res.end);

                                highlightHistoryEntries.setText(idx, ref_text);
                            }
                        }

                        function addHighlight(startIndex, length, highlightColor, hid) {
                            const formattedText = editor.getFormattedText(0, editor.length);
                            const plainText = editor.getText(0, editor.length); 

                            if (startIndex < 0 || startIndex >= plainText.length || length <= 0) {
                                console.warn("Invalid range for highlighting.")
                                return
                            }

                            const highlight = plainText.substring(startIndex, startIndex + length)

                            // TODO: Setting text-decoration to none sometimes gets ignored.
                            const insertText = `<a href="${hid}" style="text-decoration: underline; color: #000; background-color: ${highlightColor}">${highlight}</a>`

                            editor.insert(startIndex, insertText);
                            editor.remove(startIndex + length, startIndex + 2*length);
                        }
                    }
                }
            }

            ListView {
                id: highlightHistory
                model: highlightHistoryEntries

                Layout.preferredWidth: 250
                Layout.fillHeight: true

                spacing: 25
                clip: true
                headerPositioning: ListView.OverlayHeader
                currentIndex: -1

                header: Component {
                    Item {
                        width: 250
                        height: 50
                    }
                }

                onCurrentIndexChanged: {
                    codeSnippetSelected(currentIndex);
                }

                delegate: Rectangle {
                    id: codeSnippet

                    required property var modelData
                    required property int index

                    width: highlightHistory.width - 10
                    height: annotationContainer.implicitHeight
                    radius: 3

                    border.width : ListView.isCurrentItem ? 3 : 0
                    border.color: "#ddd"

                    Menu {
                        id: contextHistoryMenu
                        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
                        anchors.centerIn: parent

                        Menu {
                            title:  String.fromCodePoint(0x1F58D) + " Change code"
                            Repeater {
                                model: root.categories
                                delegate: MenuItem {
                                    required property var modelData
                                    required property int index

                                    onTriggered: {
                                        const formattedText = editor.getFormattedText(0, editor.length);
                                        const entry = highlightHistoryEntries.get(codeSnippet.index);
                                        const res = editor.find_annotation(entry.hid);

                                        const highlight = formattedText.slice(res.start+res.length, res.end);
                                        const insertText = `<a href="${entry.hid}" style="text-decoration: underline; color: #000; background-color: ${modelData.color}">${highlight}</a>`

                                        editor.text = `${formattedText.slice(0, res.start)}${insertText}${formattedText.slice(res.end, formattedText.length)}`;

                                        highlightHistoryEntries.setName(codeSnippet.index, modelData.name);
                                        highlightHistoryEntries.setColor(codeSnippet.index, modelData.color);
                                    }

                                    contentItem: RowLayout {
                                        anchors.fill: parent

                                        anchors.leftMargin: 5
                                        anchors.rightMargin: 5

                                        Rectangle {
                                            Layout.preferredWidth: 12
                                            Layout.preferredHeight: 12
                                            radius: 6
                                            color: modelData.color
                                            border.color: "#cccccc"
                                        }
                                        Label {
                                            Layout.fillWidth: true
                                            text: modelData.name
                                            verticalAlignment: Label.AlignVCenter
                                            horizontalAlignment: Label.AlignLeft
                                            font.pixelSize: 10
                                        }
                                    }
                                }
                            }
                        }

                        MenuItem { 
                            text: "Delete" 
                            onTriggered:  {
                                const formattedText = editor.getFormattedText(0, editor.length);
                                const entry = highlightHistoryEntries.get(index);
                                const res = editor.find_annotation(entry.hid);

                                editor.text = `${formattedText.slice(0, res.start)}${formattedText.slice(res.start+res.length, res.end)}${formattedText.slice(res.end, formattedText.length)}`;
                                highlightHistoryEntries.removeSnippet(index);
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        onClicked: (mouse) => {
                            if (mouse.button == Qt.LeftButton) {
                                highlightHistory.currentIndex = index;
                            }
                            else if (mouse.button == Qt.RightButton) {
                                contextHistoryMenu.open();
                            }
                        }
                    }
                    
                    ColumnLayout {
                        id: annotationContainer

                        width: parent.width
                        spacing: 10

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 20 

                            RowLayout {
                                anchors.centerIn: parent

                                Rectangle {
                                    width: 10
                                    height: 10
                                    radius: 5
                                    color: modelData.color
                                    border.color: "#cccccc"
                                }
                                Label {
                                    text: modelData.name
                                    font.bold: true
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                        }
                        Label {
                            id: labelText
                            Layout.maximumWidth: annotationContainer.width
                            text: modelData.text
                            wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignLeft
                            padding: 5
                        }
                    }
                }
            }
        }
    }

    Component {
        id: codeDialog
        Dialog {
            modal: true
            focus: true
            width: 300
            height: 225

            standardButtons: Dialog.Ok | Dialog.Cancel
            signal codeAdded(string msg, int index)

            anchors.centerIn: Overlay.overlay

            onAccepted: {
                codeAdded(categoryName.text, colorList.currentIndex);
            }

            onOpened: {
                categoryName.clear();
                categoryName.forceActiveFocus();
                colorList.currentIndex = 0;
            }

            contentItem: ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10

                ColumnLayout {
                    spacing: 10

                    GroupBox {
                        title: "Name"
                        Layout.fillWidth: true

                        TextField {
                            id: categoryName
                            width: parent.width
                            anchors.verticalCenter: parent.verticalCenter
                            placeholderText: "Enter code name here"
                        }
                    }

                    GroupBox {
                        title: "Color"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 60

                        ListView {
                            id: colorList
                            anchors.fill: parent
                            spacing: 10
                            model: root.colors
                            orientation: ListView.Horizontal
                            currentIndex: 0

                            delegate: Rectangle {
                                required property var modelData
                                required property int index

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        colorList.currentIndex = index;
                                    }
                                }

                                width: 20
                                height: 20
                                radius: 10
                                color: modelData
                                border.color: ListView.isCurrentItem ? "#888" : "#fff"
                                border.width: ListView.isCurrentItem ? 2 : 2
                            }
                        }
                    }
                }
            }
        }
    }
}
