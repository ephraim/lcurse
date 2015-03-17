import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.2

Rectangle {
    id: window
    visible: true

    TableView {
        id: tableView

        frameVisible: false
        sortIndicatorVisible: true

        anchors.fill: parent

        Layout.minimumWidth: 400
        Layout.minimumHeight: 240
        Layout.preferredWidth: 600
        Layout.preferredHeight: 400

		itemDelegate: Item {
			Text {
				anchors.verticalCenter: parent.verticalCenter
				text: title
			}
		}

        model: ListModel {
            id: sourceModel
            ListElement {
                title: "Moby-Dick"
                author: "Herman Melville"
            }
            ListElement {
                title: "The Adventures of Tom Sawyer"
                author: "Mark Twain"
            }
            ListElement {
                title: "Cat’s Cradle"
                author: "Kurt Vonnegut"
            }
            ListElement {
                title: "Farenheit 451"
                author: "Ray Bradbury"
            }
            ListElement {
                title: "It"
                author: "Stephen King"
            }
            ListElement {
                title: "On the Road"
                author: "Jack Kerouac"
            }
            ListElement {
                title: "Of Mice and Men"
                author: "John Steinbeck"
            }
            ListElement {
                title: "Do Androids Dream of Electric Sheep?"
                author: "Philip K. Dick"
            }
            ListElement {
                title: "Uncle Tom’s Cabin"
                author: "Harriet Beecher Stowe"
            }
            ListElement {
                title: "The Call of the Wild"
                author: "Jack London"
            }
            ListElement {
                title: "The Old Man and the Sea"
                author: "Ernest Hemingway"
            }
            ListElement {
                title: "A Streetcar Named Desire"
                author: "Tennessee Williams"
            }
            ListElement {
                title: "Catch-22"
                author: "Joseph Heller"
            }
            ListElement {
                title: "One Flew Over the Cuckoo’s Nest"
                author: "Ken Kesey"
            }
            ListElement {
                title: "The Murders in the Rue Morgue"
                author: "Edgar Allan Poe"
            }
            ListElement {
                title: "Breakfast at Tiffany’s"
                author: "Truman Capote"
            }
            ListElement {
                title: "Death of a Salesman"
                author: "Arthur Miller"
            }
            ListElement {
                title: "Post Office"
                author: "Charles Bukowski"
            }
            ListElement {
                title: "Herbert West—Reanimator"
                author: "H. P. Lovecraft"
            }
        }
    }
}
