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
		id: addonsList
		anchors {
			fill: parent
			margins: 10
		}
		displayMarginBeginning: 5
		displayMarginEnd: 5
		spacing: 4
		model: addonsModel
		delegate: Component {
			Rectangle {
				anchors.margins: 5
				border.width: 1
				anchors.left: parent.left
				anchors.right: parent.right
				height: 55
				Rectangle {
					id: addonNameVersion
					anchors.top: parent.top
					anchors.left: parent.left
					height: 35
					Text {
						id: addonName
						anchors.top: parent.top
						anchors.left: parent.left
						anchors.leftMargin: 10
						text: name
						font.pointSize: 12
					}
					Text {
						anchors.top: addonName.bottom
						anchors.left: parent.left
						anchors.leftMargin: 10
						text: version
						font.pointSize: 8
					}
				}
				Rectangle {
					anchors.top: addonNameVersion.bottom
					anchors.left: parent.left
					Text {
						anchors.left: parent.left
						anchors.leftMargin: 10
						text: uri
						font.pointSize: 12
					}
				}
			}
		}
	}

    statusBar: StatusBar {
        RowLayout {
            anchors.fill: parent
            Label { text: "Read Only" }
        }
    }
}
