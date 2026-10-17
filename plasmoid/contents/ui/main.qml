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
    property string pairingUrl: ""
    property string pairingQr: ""
    function startPairing() {
        root.pairingUrl = "Préparation…"
        root.pairingQr = ""
        root.pairingVisible = true
        var xhr = new XMLHttpRequest()
        xhr.open("POST", "http://127.0.0.1:8765/pairing/start")
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE) return
            if (xhr.status === 200) {
                var result = JSON.parse(xhr.responseText)
                root.pairingUrl = result.url
                root.pairingQr = result.qr || ""
            } else {
                root.pairingUrl = "Appairage indisponible : vérifiez le service MX Link."
            }
        }
        xhr.send("{}")
    }

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
    property var historyEvents: []
    property bool historyExpanded: false
    property string expandedGroupId: ""
    property bool clearArmed: false
    property string historyMessage: ""

    onExpandedChanged: {
        // Ne jamais laisser une suppression armée après fermeture du panneau.
        if (!expanded)
            clearArmed = false
    }

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

    function refreshHistory() {
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return
            if (xhr.status === 200) {
                try {
                    var data = JSON.parse(xhr.responseText)
                    if (Array.isArray(data))
                        root.historyEvents = data
                } catch (e) {
                    root.historyMessage = "Historique indisponible"
                }
            }
        }
        xhr.open("GET", "http://127.0.0.1:8765/history")
        xhr.send()
    }

    function sendHistoryAction(path, payload, onSuccess) {
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return
            if (xhr.status === 200) {
                root.historyMessage = ""
                onSuccess()
            } else {
                root.historyMessage = xhr.status === 404
                    ? "Fichier ou lien indisponible"
                    : "Opération impossible"
                root.refreshHistory()
            }
        }
        xhr.open("POST", "http://127.0.0.1:8765/" + path)
        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send(JSON.stringify(payload))
    }

    function openHistoryItem(id, index) {
        sendHistoryAction("history/open", {"id": id, "index": index}, function() {})
    }

    function clearHistory() {
        sendHistoryAction("history/clear", {}, function() {
            root.clearArmed = false
            root.expandedGroupId = ""
            root.historyExpanded = false
            root.refreshHistory()
        })
    }

    function historyTitle(entry) {
        if (!entry || !entry.items || entry.items.length === 0)
            return "Échange"
        var name = entry.items[0].name
        return entry.items.length > 1
            ? name + "  +" + (entry.items.length - 1)
            : name
    }

    function historyDirection(entry) {
        return entry.direction === "out"
            ? "↑ Vers l’iPhone" : "↓ Depuis l’iPhone"
    }

    function historyTime(entry) {
        if (!entry.date)
            return ""
        var parts = entry.date.split("T")
        return parts.length > 1 ? parts[1].substring(0, 5) : ""
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
            "POST",
            "http://127.0.0.1:8765/open-folder"
        )

        xhr.setRequestHeader("Content-Type", "application/json")
        xhr.send("{}")
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

        onTriggered: {
            root.refreshStatus()
            root.refreshHistory()
        }
    }

    Component.onCompleted: {
        refreshStatus()
        refreshHistory()
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

            // Le symbole remplit la zone disponible, sans fond carré.
            width:
                Math.min(
                    parent.width,
                    parent.height
                ) * 0.96

            height: width

            source:
                root.online
                ? Qt.resolvedUrl("../images/mxlink-symbolic.svg")
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
            : root.historyExpanded
                ? Kirigami.Units.gridUnit * 26
                : Kirigami.Units.gridUnit * 19

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
                        ? Qt.resolvedUrl("../images/mxlink-symbolic.svg")
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
                        ) {
                            root.clearArmed = false
                            root.refreshConfig()
                        }
                    }

                    PlasmaComponents.ToolTip {
                        text: "Réglages"
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                visible: !root.settingsVisible

                PlasmaComponents.Label {
                    text: root.clearArmed ? "Effacer l’historique ?" : "Échanges récents"
                    font.bold: true
                    Layout.fillWidth: true
                }

                PlasmaComponents.ToolButton {
                    visible: root.clearArmed && root.historyEvents.length > 0
                    icon.name: "dialog-cancel"
                    text: "Annuler"
                    onClicked: root.clearArmed = false
                    PlasmaComponents.ToolTip {
                        text: "Annuler sans rien effacer"
                    }
                }

                PlasmaComponents.ToolButton {
                    visible: root.historyEvents.length > 0
                    icon.name: root.clearArmed ? "dialog-warning" : "edit-clear-history"
                    text: root.clearArmed ? "Effacer" : ""
                    onClicked: {
                        if (root.clearArmed)
                            root.clearHistory()
                        else
                            root.clearArmed = true
                    }
                    PlasmaComponents.ToolTip {
                        text: root.clearArmed ? "Confirmer l’effacement de l’historique" : "Vider l’historique"
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: root.historyExpanded
                    ? Kirigami.Units.gridUnit * 17
                    : Kirigami.Units.gridUnit * 9
                visible: !root.settingsVisible

                Flickable {
                    anchors.fill: parent
                    clip: true
                    contentHeight: historyColumn.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds

                    Column {
                        id: historyColumn
                        width: parent.width
                        spacing: Kirigami.Units.smallSpacing

                        Repeater {
                            model: root.historyExpanded
                                ? root.historyEvents
                                : root.historyEvents.slice(0, 3)

                            delegate: Rectangle {
                                id: historyEntry
                                required property var modelData
                                property var entry: modelData
                                width: historyColumn.width
                                height: entryColumn.implicitHeight + Kirigami.Units.smallSpacing * 2
                                radius: Kirigami.Units.smallSpacing
                                color: Kirigami.Theme.alternateBackgroundColor

                                Column {
                                    id: entryColumn
                                    x: Kirigami.Units.smallSpacing
                                    y: Kirigami.Units.smallSpacing
                                    width: parent.width - Kirigami.Units.smallSpacing * 2
                                    spacing: 2

                                    Item {
                                        width: parent.width
                                        height: Kirigami.Units.gridUnit * 2.45

                                        MouseArea {
                                            anchors.fill: parent
                                            cursorShape: historyEntry.entry.items.length > 1
                                                || historyEntry.entry.items[0].available
                                                ? Qt.PointingHandCursor : Qt.ArrowCursor
                                            onClicked: {
                                                var evt = historyEntry.entry
                                                if (evt.items.length > 1) {
                                                    root.expandedGroupId = root.expandedGroupId === evt.id
                                                        ? "" : evt.id
                                                } else if (evt.items[0].available) {
                                                    root.openHistoryItem(evt.id, 0)
                                                }
                                            }
                                        }

                                        RowLayout {
                                            anchors.fill: parent
                                            spacing: Kirigami.Units.smallSpacing

                                            Kirigami.Icon {
                                                source: root.typeIcon(historyEntry.entry.type)
                                                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                                                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                                            }

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 0
                                                PlasmaComponents.Label {
                                                    Layout.fillWidth: true
                                                    text: root.historyTitle(historyEntry.entry)
                                                    font.bold: true
                                                    opacity: historyEntry.entry.items[0].available ? 1 : 0.55
                                                    elide: Text.ElideMiddle
                                                }
                                                PlasmaComponents.Label {
                                                    text: root.historyDirection(historyEntry.entry)
                                                        + " · " + root.historyTime(historyEntry.entry)
                                                    opacity: 0.65
                                                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                                                }
                                            }
                                            Kirigami.Icon {
                                                source: historyEntry.entry.items.length > 1
                                                    ? (root.expandedGroupId === historyEntry.entry.id
                                                       ? "arrow-up" : "arrow-down")
                                                    : (historyEntry.entry.items[0].available
                                                       ? "document-open" : "dialog-warning")
                                                Layout.preferredWidth: Kirigami.Units.iconSizes.small
                                                Layout.preferredHeight: Kirigami.Units.iconSizes.small
                                            }
                                        }
                                    }

                                    Repeater {
                                        model: root.expandedGroupId === historyEntry.entry.id
                                            ? historyEntry.entry.items : []

                                        delegate: Item {
                                            id: historySubitem
                                            required property var modelData
                                            required property int index
                                            width: entryColumn.width
                                            height: Kirigami.Units.gridUnit * 1.8

                                            MouseArea {
                                                anchors.fill: parent
                                                enabled: historySubitem.modelData.available
                                                cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                                onClicked: root.openHistoryItem(historyEntry.entry.id, historySubitem.index)
                                            }
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: Kirigami.Units.gridUnit
                                                PlasmaComponents.Label {
                                                    Layout.fillWidth: true
                                                    text: historySubitem.modelData.name
                                                    elide: Text.ElideMiddle
                                                    opacity: historySubitem.modelData.available ? 1 : 0.45
                                                }
                                                Kirigami.Icon {
                                                    source: historySubitem.modelData.available
                                                        ? "document-open" : "dialog-warning"
                                                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                                                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                PlasmaComponents.Label {
                    anchors.centerIn: parent
                    visible: root.historyEvents.length === 0
                    text: "Aucun échange pour le moment"
                    opacity: 0.6
                }
            }

            PlasmaComponents.Label {
                Layout.fillWidth: true
                visible: !root.settingsVisible && root.historyMessage !== ""
                text: root.historyMessage
                color: Kirigami.Theme.negativeTextColor
            }

            PlasmaComponents.Button {
                Layout.fillWidth: true
                visible: !root.settingsVisible && root.historyEvents.length > 3
                flat: true
                text: root.historyExpanded ? "Réduire l’historique" : "Voir l’historique (" + root.historyEvents.length + ")"
                icon.name: root.historyExpanded ? "arrow-up" : "view-history"
                onClicked: root.historyExpanded = !root.historyExpanded
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

                        currentIndex:
                            root.openerIndex(
                                root.imageOpenerValues,
                                root.configImageOpener
                            )

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

                        currentIndex:
                            root.openerIndex(
                                root.pdfOpenerValues,
                                root.configPdfOpener
                            )

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
                    root.startPairing()
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
                        "Valable 5 minutes · une seule ouverture"

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
                        root.pairingQr

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
