import QtQuick
import QtQuick.Layouts
import QtCore

import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property bool online: false
    property string lastError: ""

    property string lastType: ""
    property string lastName: ""
    property string lastTime: ""
    property int lastSize: 0

    property string batchType: ""

    property string lastDirection: "in"

    property var batchNames: []
    property int batchCount: 0
    property int batchBytes: 0

    property bool settingsVisible: false
    property bool pairingVisible: false
    property string pairingUrl: "http://localhost:8767/setup"
    property bool configLoaded: false

    property string configReceiveDir: ""

    property string resolvedReceiveDir:
        StandardPaths.writableLocation(
            StandardPaths.DownloadLocation
        ) + "/MX Link"
    property bool configOpenImages: true
    property string configImageOpener: "default"
    property bool configOpenPdfs: true
    property string configPdfOpener: "default"
    property bool configNotifications: true

    property var imageOpenerLabels: ["Par défaut"]
    property var imageOpenerValues: ["default"]
    property var pdfOpenerLabels: ["Par défaut"]
    property var pdfOpenerValues: ["default"]
    property string configMessage: ""

    toolTipMainText: "MX Link"

    toolTipSubText: {
        if (!online)
            return "Indisponible"

        if (batchCount > 1) {
            return batchLabel(
                batchType,
                batchCount
            )
        }

        if (lastName !== "")
            return "Dernier reçu : " + lastName

        return "Prêt"
    }

    function typeIcon(type) {
        if (type === "image")
            return "image-x-generic"

        if (type === "pdf")
            return "application-pdf"

        if (type === "url")
            return "internet-web-browser"

        if (type === "text")
            return "edit-paste"

        if (type === "file")
            return "document"

        return "smartphone"
    }

    function typeLabel(type) {
        if (type === "image")
            return "Photo"

        if (type === "pdf")
            return "PDF"

        if (type === "url")
            return "Lien"

        if (type === "text")
            return "Texte"

        if (type === "file")
            return "Fichier"

        return "Réception"
    }

    function batchLabel(type, count) {
        if (count <= 1)
            return typeLabel(type)

        if (type === "image")
            return count + " photos"

        if (type === "pdf")
            return count + " PDF"

        if (type === "file")
            return count + " fichiers"

        return typeLabel(type)
    }

    function formatBytes(bytes) {
        if (!bytes || bytes <= 0)
            return ""

        if (bytes < 1024)
            return bytes + " o"

        if (bytes < 1024 * 1024)
            return (
                bytes / 1024
            ).toFixed(1) + " Ko"

        if (bytes < 1024 * 1024 * 1024)
            return (
                bytes / (1024 * 1024)
            ).toFixed(1) + " Mo"

        return (
            bytes / (
                1024 * 1024 * 1024
            )
        ).toFixed(2) + " Go"
    }

    function namesLabel() {
        if (
            root.lastDirection !== "out"
            || !root.batchNames
            || root.batchNames.length === 0
        )
            return root.lastName

        var limit = 4
        var shown = []

        for (
            var i = 0;
            i < Math.min(
                root.batchNames.length,
                limit
            );
            ++i
        )
            shown.push(
                root.batchNames[i]
            )

        if (
            root.batchNames.length
            > limit
        )
            shown.push(
                "… +"
                + (
                    root.batchNames.length
                    - limit
                )
                + " autres"
            )

        return shown.join("\n")
    }


    function activityLabel() {
        var type =
            batchType !== ""
            ? batchType
            : lastType

        var count =
            batchCount > 0
            ? batchCount
            : 1

        var label =
            batchLabel(
                type,
                count
            )

        var bytes =
            count > 1
            ? batchBytes
            : lastSize

        var size =
            formatBytes(bytes)

        if (size !== "")
            return label + " · " + size

        return label
    }

    function refreshStatus() {
        var xhr = new XMLHttpRequest()

        xhr.onreadystatechange = function() {
            if (
                xhr.readyState
                !== XMLHttpRequest.DONE
            )
                return

            if (xhr.status !== 200) {
                root.online = false
                root.lastError =
                    "Pas de réponse du service"
                return
            }

            try {
                var data =
                    JSON.parse(
                        xhr.responseText
                    )

                root.online =
                    data.status === "ready"

                root.lastType =
                    data.last_type || ""

                root.lastName =
                    data.last_name || ""

                root.lastTime =
                    data.last_time || ""

                root.lastSize =
                    data.last_size || 0

                root.batchType =
                    data.batch_type || ""

                root.lastDirection = data.last_direction || "in"

                root.batchNames = data.batch_names || []

                root.batchCount =
                    data.batch_count || 0

                root.batchBytes =
                    data.batch_bytes || 0

                root.lastError = ""

            } catch (e) {
                root.online = false
                root.lastError =
                    "Réponse invalide"
            }
        }

        xhr.onerror = function() {
            root.online = false
            root.lastError =
                "Connexion impossible"
        }

        xhr.open(
            "GET",
            "http://127.0.0.1:8765/state"
        )

        xhr.send()
    }

    function refreshConfig() {
        var xhr = new XMLHttpRequest()

        xhr.onreadystatechange = function() {
            if (
                xhr.readyState
                !== XMLHttpRequest.DONE
            )
                return

            if (xhr.status !== 200) {
                root.configMessage =
                    "Impossible de lire la configuration"
                return
            }

            try {
                var data =
                    JSON.parse(
                        xhr.responseText
                    )

                root.configReceiveDir =
                    data.receive_dir || ""

                root.resolvedReceiveDir =
                    data.receive_dir_resolved
                    || (
                        StandardPaths.writableLocation(
                            StandardPaths.DownloadLocation
                        )
                        + "/MX Link"
                    )

                root.configOpenImages =
                    data.open_images !== false

                root.configOpenPdfs =
                    data.open_pdfs !== false

                root.configImageOpener =
                    data.image_opener || "default"

                root.configPdfOpener =
                    data.pdf_opener || "default"

                root.configNotifications =
                    data.notifications !== false

                root.configLoaded = true

                if (
                    root.imageOpenerLabels.length <= 1
                    && root.pdfOpenerLabels.length <= 1
                )
                    root.loadOpeners()

            } catch (e) {
                root.configMessage =
                    "Configuration invalide"
            }
        }

        xhr.open(
            "GET",
            "http://127.0.0.1:8765/config"
        )

        xhr.send()
    }

    function openerIndex(values, value) {
        for (var i = 0; i < values.length; ++i) {
            if (values[i] === value)
                return i
        }

        return 0
    }

    function syncOpenerSelections() {
        imageOpenerCombo.currentIndex =
            openerIndex(
                imageOpenerValues,
                configImageOpener
            )

        pdfOpenerCombo.currentIndex =
            openerIndex(
                pdfOpenerValues,
                configPdfOpener
            )
    }

    function loadOpeners() {
        var xhr = new XMLHttpRequest()

        xhr.onreadystatechange = function() {
            if (
                xhr.readyState
                !== XMLHttpRequest.DONE
            )
                return

            if (xhr.status !== 200)
                return

            try {
                var data =
                    JSON.parse(xhr.responseText)

                var imageLabels = []
                var imageValues = []
                var pdfLabels = []
                var pdfValues = []

                var images = data.images || []
                var pdfs = data.pdfs || []

                for (var i = 0; i < images.length; ++i) {
                    imageLabels.push(images[i].label)
                    imageValues.push(images[i].value)
                }

                for (var j = 0; j < pdfs.length; ++j) {
                    pdfLabels.push(pdfs[j].label)
                    pdfValues.push(pdfs[j].value)
                }

                root.imageOpenerLabels = imageLabels
                root.imageOpenerValues = imageValues
                root.pdfOpenerLabels = pdfLabels
                root.pdfOpenerValues = pdfValues

                root.syncOpenerSelections()

            } catch (e) {
            }
        }

        xhr.open(
            "GET",
            "http://127.0.0.1:8765/openers"
        )

        xhr.send()
    }

    function updateConfig(values) {
        var xhr = new XMLHttpRequest()

        xhr.onreadystatechange = function() {
            if (
                xhr.readyState
                !== XMLHttpRequest.DONE
            )
                return

            if (xhr.status !== 200) {
                root.configMessage =
                    "Erreur lors de l’enregistrement"
                return
            }

            try {
                var data =
                    JSON.parse(
                        xhr.responseText
                    )

                root.configReceiveDir =
                    data.receive_dir || ""

                root.resolvedReceiveDir =
                    data.receive_dir_resolved
                    || root.resolvedReceiveDir

                root.configOpenImages =
                    data.open_images !== false

                root.configOpenPdfs =
                    data.open_pdfs !== false

                root.configImageOpener =
                    data.image_opener || "default"

                root.configPdfOpener =
                    data.pdf_opener || "default"

                root.configNotifications =
                    data.notifications !== false

                root.syncOpenerSelections()

                root.configMessage =
                    "Enregistré"

                clearMessageTimer.restart()

            } catch (e) {
                root.configMessage =
                    "Réponse invalide"
            }
        }

        xhr.open(
            "POST",
            "http://127.0.0.1:8765/config"
        )

        xhr.setRequestHeader(
            "Content-Type",
            "application/json"
        )

        xhr.send(
            JSON.stringify(values)
        )
    }

    function saveReceiveDir() {
        updateConfig({
            "receive_dir":
                configReceiveDir.trim()
        })
    }

    function openReceiveFolder() {
        var xhr = new XMLHttpRequest()

        xhr.open(
            "GET",
            "http://127.0.0.1:8765/open-folder"
        )

        xhr.send()
    }

    Timer {
        id: clearMessageTimer

        interval: 1800
        repeat: false

        onTriggered:
            root.configMessage = ""
    }

    Timer {
        interval: 3000
        repeat: true
        running: true

        onTriggered:
            root.refreshStatus()
    }

    Component.onCompleted: {
        refreshStatus()
        refreshConfig()
    }

    compactRepresentation: MouseArea {
        hoverEnabled: true

        implicitWidth:
            Kirigami.Units.gridUnit * 2

        implicitHeight:
            Kirigami.Units.gridUnit * 2

        onClicked:
            root.expanded =
                !root.expanded

        Kirigami.Icon {
            anchors.centerIn: parent

            width:
                Math.min(
                    parent.width,
                    parent.height
                ) * 0.75

            height: width

            source:
                root.online
                ? "smartphone"
                : "network-disconnect"

            isMask: true

            color:
                Kirigami.Theme.textColor
        }
    }

    fullRepresentation: Item {

        implicitWidth:
            Kirigami.Units.gridUnit * 21

        implicitHeight:
            root.settingsVisible
            ? Kirigami.Units.gridUnit * 29
            : Kirigami.Units.gridUnit * 16

        Layout.preferredWidth:
            implicitWidth

        Layout.preferredHeight:
            implicitHeight

        ColumnLayout {
            anchors.fill: parent

            anchors.margins:
                Kirigami.Units.largeSpacing

            spacing:
                Kirigami.Units.largeSpacing

            RowLayout {
                spacing:
                    Kirigami.Units.largeSpacing

                Kirigami.Icon {
                    source:
                        root.online
                        ? "smartphone"
                        : "network-disconnect"

                    Layout.preferredWidth:
                        Kirigami.Units.iconSizes.medium

                    Layout.preferredHeight:
                        Kirigami.Units.iconSizes.medium

                    isMask: true

                    color:
                        root.online
                        ? Kirigami.Theme.positiveTextColor
                        : Kirigami.Theme.negativeTextColor
                }

                ColumnLayout {
                    spacing: 0

                    PlasmaComponents.Label {
                        text: "MX Link"

                        font.bold: true

                        font.pixelSize:
                            Kirigami.Theme.defaultFont.pixelSize
                            * 1.2
                    }

                    PlasmaComponents.Label {
                        text:
                            root.online
                            ? "Prêt"
                            : "Indisponible"

                        color:
                            root.online
                            ? Kirigami.Theme.positiveTextColor
                            : Kirigami.Theme.negativeTextColor
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                PlasmaComponents.ToolButton {
                    icon.name:
                        "view-refresh"

                    onClicked: {
                        root.refreshStatus()
                        root.refreshConfig()
                    }

                    PlasmaComponents.ToolTip {
                        text: "Actualiser"
                    }
                }

                PlasmaComponents.ToolButton {
                    checkable: true
                    checked:
                        root.settingsVisible

                    icon.name:
                        "configure"

                    onClicked: {
                        root.settingsVisible =
                            !root.settingsVisible

                        if (
                            root.settingsVisible
                        )
                            root.refreshConfig()
                    }

                    PlasmaComponents.ToolTip {
                        text: "Réglages"
                    }
                }
            }

            PlasmaComponents.Label {
                text: "Dernière activité"
                opacity: 0.65
            }

            Rectangle {
                Layout.fillWidth: true

                Layout.preferredHeight:
                    Kirigami.Units.gridUnit * (
                        root.lastDirection === "out"
                        && root.batchNames
                        && root.batchNames.length > 1
                        ? 4.2
                          + Math.min(
                              root.batchNames.length - 1,
                              4
                          ) * 1.05
                        : 4.2
                    )

                radius:
                    Kirigami.Units.smallSpacing

                color:
                    Kirigami.Theme.alternateBackgroundColor

                visible:
                    root.online
                    && root.lastName !== ""
                    && !root.settingsVisible

                RowLayout {
                    anchors.fill: parent

                    anchors.margins:
                        Kirigami.Units.largeSpacing

                    spacing:
                        Kirigami.Units.largeSpacing

                    Kirigami.Icon {
                        source:
                            root.typeIcon(
                                root.batchType !== ""
                                ? root.batchType
                                : root.lastType
                            )

                        Layout.preferredWidth:
                            Kirigami.Units.iconSizes.medium

                        Layout.preferredHeight:
                            Kirigami.Units.iconSizes.medium
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        PlasmaComponents.Label {
                            text:
                                (root.lastDirection === "out" ? "↑ MXBook → iPhone · " : "↓ iPhone → MXBook · ") + root.activityLabel()
                            opacity: 0.65
                        }

                        PlasmaComponents.Label {
                            Layout.fillWidth: true

                            text:


                                root.namesLabel()

                            font.bold: true

                            elide:
                                Text.ElideMiddle

                            maximumLineCount: 5
                        }

                        PlasmaComponents.Label {
                            text:
                                root.lastTime !== ""
                                ? "Reçu à "
                                  + root.lastTime
                                : ""

                            opacity: 0.65
                        }
                    }
                }
            }

            ColumnLayout {
                visible:
                    root.settingsVisible

                Layout.fillWidth: true

                spacing:
                    Kirigami.Units.largeSpacing

                PlasmaComponents.Label {
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    text: "Réception"
                    font.bold: true
                }

                                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    PlasmaComponents.CheckBox {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        Layout.fillWidth: true
                        text: "Ouvrir les photos"
                        checked:
                            root.configOpenImages

                        onClicked:
                            root.updateConfig({
                                "open_images":
                                    checked
                            })
                    }

                    PlasmaComponents.ComboBox {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        id: imageOpenerCombo
                        Layout.preferredWidth:
                            Kirigami.Units.gridUnit * 11

                        enabled:
                            root.configOpenImages

                        model:
                            root.imageOpenerLabels

                        onActivated: function(index) {
                            if (
                                index >= 0
                                && index < root.imageOpenerValues.length
                            ) {
                                root.updateConfig({
                                    "image_opener":
                                        root.imageOpenerValues[index]
                                })
                            }
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing

                    PlasmaComponents.CheckBox {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        Layout.fillWidth: true
                        text: "Ouvrir les PDF"
                        checked:
                            root.configOpenPdfs

                        onClicked:
                            root.updateConfig({
                                "open_pdfs":
                                    checked
                            })
                    }

                    PlasmaComponents.ComboBox {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        id: pdfOpenerCombo
                        Layout.preferredWidth:
                            Kirigami.Units.gridUnit * 11

                        enabled:
                            root.configOpenPdfs

                        model:
                            root.pdfOpenerLabels

                        onActivated: function(index) {
                            if (
                                index >= 0
                                && index < root.pdfOpenerValues.length
                            ) {
                                root.updateConfig({
                                    "pdf_opener":
                                        root.pdfOpenerValues[index]
                                })
                            }
                        }
                    }
                }

PlasmaComponents.CheckBox {
    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    text:
                        "Afficher les notifications"

                    checked:
                        root.configNotifications

                    onClicked:
                        root.updateConfig({
                            "notifications":
                                checked
                        })
                }

                PlasmaComponents.Label {
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    text:
                        "Dossier de réception"

                    font.bold: true
                }

                PlasmaComponents.TextField {
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    Layout.fillWidth: true

                    text:
                        root.configReceiveDir

                    placeholderText:
                        "Vide = Téléchargements/MX Link"

                    onTextEdited:
                        root.configReceiveDir =
                            text

                    onAccepted:
                        root.saveReceiveDir()
                }

                PlasmaComponents.Label {
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    Layout.fillWidth: true

                    text:
                        root.configReceiveDir === ""
                        ? "Automatique : "
                          + root.resolvedReceiveDir
                        : "Destination : "
                          + root.resolvedReceiveDir

                    opacity: 0.6

                    elide:
                        Text.ElideMiddle
                }

                RowLayout {
                    Layout.fillWidth: true

                    PlasmaComponents.Button {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        text:
                            "Enregistrer"

                        icon.name:
                            "document-save"

                        onClicked:
                            root.saveReceiveDir()
                    }

                    PlasmaComponents.Button {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        text:
                            "Dossier par défaut"

                        onClicked: {
                            root.configReceiveDir = ""

                            root.updateConfig({
                                "receive_dir": ""
                            })
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    PlasmaComponents.Label {
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        text:
                            root.configMessage

                        color:
                            Kirigami.Theme.positiveTextColor
                    }
                }
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true

                visible:
                    !root.online

                text:
                    root.lastError

                color:
                    Kirigami.Theme.negativeTextColor

                wrapMode:
                    Text.WordWrap
            }

            Item {
                Layout.fillHeight: true
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true

                text:
                    "Ouvrir le dossier de réception"

                icon.name:
                    "folder-download"

                onClicked:
                    root.openReceiveFolder()
            }


            PlasmaComponents.Button {
                Layout.fillWidth: true

                visible:
                    !root.settingsVisible

                text:
                    root.pairingVisible
                    ? "Masquer le QR code"
                    : "Appairer un iPhone"

                icon.name:
                    "smartphone"

                onClicked:
                    root.pairingVisible = true
            }

            
        }

        Rectangle {
            anchors.fill: parent
            z: 100

            visible:
                root.pairingVisible

            color:
                Kirigami.Theme.backgroundColor

            // Empêche les clics de traverser vers l'écran normal
            MouseArea {
                anchors.fill: parent
            }

            ColumnLayout {
                anchors.fill: parent

                anchors.margins:
                    Kirigami.Units.largeSpacing

                spacing:
                    Kirigami.Units.smallSpacing

                z: 1

                RowLayout {
                    Layout.fillWidth: true

                    PlasmaComponents.Label {
                        Layout.fillWidth: true

                        text:
                            "Appairer un iPhone"

                        font.bold: true
                    }

                    PlasmaComponents.ToolButton {
                        icon.name:
                            "window-close"

                        onClicked:
                            root.pairingVisible = false

                        PlasmaComponents.ToolTip {
                            text: "Fermer"
                        }
                    }
                }

                PlasmaComponents.Label {
                    Layout.fillWidth: true

                    text:
                        "Scannez ce QR code avec l’iPhone"

                    horizontalAlignment:
                        Text.AlignHCenter
                }

                Image {
                    Layout.alignment:
                        Qt.AlignHCenter

                    Layout.preferredWidth:
                        Kirigami.Units.gridUnit * 8

                    Layout.preferredHeight:
                        Kirigami.Units.gridUnit * 8

                    source:
                        Qt.resolvedUrl(
                            "../images/pairing-qr.png"
                        )

                    fillMode:
                        Image.PreserveAspectFit

                    smooth: false
                }

                PlasmaComponents.Label {
                    Layout.fillWidth: true

                    text:
                        root.pairingUrl

                    opacity: 0.65

                    horizontalAlignment:
                        Text.AlignHCenter

                    elide:
                        Text.ElideMiddle
                }

                Item {
                    Layout.fillHeight: true
                }
            }
        }

    }
}
