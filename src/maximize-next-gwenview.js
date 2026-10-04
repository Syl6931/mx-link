let done = false;

function isGwenview(w) {
    if (!w)
        return false;

    const cls = String(w.resourceClass || "").toLowerCase();
    const name = String(w.resourceName || "").toLowerCase();

    return cls.includes("gwenview") || name.includes("gwenview");
}

function handleWindow(w) {
    if (done || !isGwenview(w))
        return;

    done = true;

    // Maximisation horizontale + verticale
    w.setMaximize(true, true);

    // Et premier plan
    workspace.activeWindow = w;
}

workspace.windowAdded.connect(handleWindow);
