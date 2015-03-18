import QtQuick 2.4
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.0

ApplicationWindow {
	id: window
    visible: true
	width: 800
	height: 600

	ListView {
		visible: true
		anchors.fill: parent
		model: addonsModel
		delegate: Text {
			text: name + "(" + version + "):" + uri
		}
	}

    statusBar: StatusBar {
        RowLayout {
            anchors.fill: parent
            Label { text: "Read Only" }
        }
    }
}
