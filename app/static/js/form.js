const canvas = document.getElementById("drawCanvas");
const ctx = canvas.getContext("2d");
const max_hist = 10;

function resizeCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

let isDrawing = false;
let lastX = 0;
let lastY = 0;
let drawingColor = "#8a65c9"; // "#c2a7ef";
let lineWidth = 2;
let history = [];
let historyIndex = -1;
let isEraser = false;

function getCoordinates(e) {
    const rect = canvas.getBoundingClientRect();
    if (e.type.includes("touch")) {
        return {
            x: e.touches[0].clientX - rect.left,
            y: e.touches[0].clientY - rect.top,
        };
    }
    return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
    };
}

function startDrawing(e) {
    e.preventDefault();
    isDrawing = true;
    const coords = getCoordinates(e);
    [lastX, lastY] = [coords.x, coords.y];
}

function draw(e) {
    e.preventDefault();
    if (!isDrawing) return;

    const coords = getCoordinates(e);

    if (isEraser) {
        // Clear pixels instead of drawing color
        ctx.clearRect(
            coords.x - lineWidth / 2,
            coords.y - lineWidth / 2,
            lineWidth,
            lineWidth
        );
    } else {
        ctx.strokeStyle = drawingColor;
        ctx.lineWidth = lineWidth;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";

        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();
    }

    [lastX, lastY] = [coords.x, coords.y];
}

function stopDrawing(e) {
    if (e) e.preventDefault();
    if (isDrawing) {
        isDrawing = false;
        saveState();
    }
}

// Move getCookie function to global scope
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

function saveState() {
    if (historyIndex >= max_hist - 1) {
        history.shift();
    }
    history.push(canvas.toDataURL());
    historyIndex = history.length - 1;

    uploadState();
}

function uploadState() {
    // Save to server
    const documentId =
        document.querySelector("[data-document-id]").dataset.documentId;
    if (!documentId) {
        console.error("No document ID found");
        return;
    }

    const formData = new FormData();
    fetch(canvas.toDataURL())
        .then((res) => res.blob())
        .then((blob) => {
            formData.append("img_content", blob, "canvas_state.png");


            return fetch(`/api/documents/${documentId}/update-state/`, {
                method: "PATCH",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: formData,
            });
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then((data) => {
            console.log("State saved successfully:", data);
        })
        .catch((error) => {
            console.error("Error saving state:", error);
        });
}

function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        restoreState(history[historyIndex]);
        // saveState();
        uploadState();
    }
}

function redo() {
    if (historyIndex < history.length - 1) {
        historyIndex++;
        restoreState(history[historyIndex]);
        // saveState();
        uploadState();
    }
    // saveCanvasAsPNG();
}

function downloadCanvasAsPNG() {
    const dataURL = canvas.toDataURL("image/png");
    const link = document.createElement("a");
    link.download = "drawing.png";
    link.href = dataURL;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function renderNote() {
    // Show the loading indicator
    // const loadingIndicator = document.getElementById("loadingIndicator");
    // loadingIndicator.style.display = "block";

    const renderButtonIcon = document.querySelector("#renderButton img");
    const originalIconSrc = renderButtonIcon.src;
    const pinwheelIcon = document.getElementById("pinwheel").src;
    renderButtonIcon.src = pinwheelIcon; // Replace with the path to a spinner icon
    renderButtonIcon.classList.add("spinner");

    // const sleep = ms => new Promise(r => setTimeout(r, ms));
    await sleep(500);

    // Convert canvas to data URL
    const dataURL = canvas.toDataURL("image/png");

    // Create form data and append the blob
    const formData = new FormData();
    fetch(dataURL)
        .then((res) => res.blob())
        .then((blob) => {
            formData.append("image", blob, "drawing.png");

            // Send to server
            return fetch("/render", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: formData,
            });
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json(); // Parse JSON response instead of blob
        })
        .then((data) => {
            // Convert base64 PDF back to blob
            const pdfBlob = base64ToBlob(data.pdf, 'application/pdf');
            const pdfUrl = URL.createObjectURL(pdfBlob);

            // Update the PDF viewer
            const pdfViewer = document.querySelector("#main-render object");
            pdfViewer.data = pdfUrl;

            // Update the LaTeX editor if it exists
            const editableCode = document.getElementById("editable-code");
            if (editableCode) {
                editableCode.value = data.latex;
                update(data.latex); // Update syntax highlighting
            }

            // Show the preview if not already visible
            const toggle = document.getElementById("preview-toggle");
            toggleSwitch(toggle);
        })
        .catch((error) => {
            console.error("Error:", error);
        })
        .finally(() => {
            // Revert the icon and remove spinner class
            renderButtonIcon.src = originalIconSrc;
            renderButtonIcon.classList.remove("spinner");
        });
        
        
        // .finally(() => {
        //     // Hide the loading indicator
        //     loadingIndicator.style.display = "none";
        // });

}

// Helper function to convert base64 to blob
function base64ToBlob(base64, type = 'application/pdf') {
    const binStr = atob(base64);
    const len = binStr.length;
    const arr = new Uint8Array(len);
    
    for (let i = 0; i < len; i++) {
        arr[i] = binStr.charCodeAt(i);
    }
    
    return new Blob([arr], { type: type });
}

function restoreState(dataURL) {
    const img = new Image();
    img.src = dataURL;
    img.onload = function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
    };
}

document.getElementById("penButton").addEventListener("click", function () {
    drawingColor = "#c2a7ef";
    lineWidth = 2;
    isEraser = false;
    toggleActive(this);
});

document.getElementById("eraserButton").addEventListener("click", function () {
    isEraser = true;
    lineWidth = 30;
    toggleActive(this);
});
document.getElementById("backButton").addEventListener("click", function () {
    window.location.href = "/documents/";
});
document.getElementById("undoButton").addEventListener("click", undo);
document.getElementById("redoButton").addEventListener("click", redo);
document
    .getElementById("downloadButton")
    .addEventListener("click", downloadCanvasAsPNG);
document
    .getElementById("renderButton")
    .addEventListener("click", renderNote);

function toggleActive(button) {
    document
        .querySelectorAll(".button")
        .forEach((btn) => btn.classList.remove("active"));
    button.classList.add("active");
}

// Mouse events
canvas.addEventListener("mousedown", startDrawing);
canvas.addEventListener("mousemove", draw);
canvas.addEventListener("mouseup", stopDrawing);
canvas.addEventListener("mouseout", stopDrawing);

// Touch events
canvas.addEventListener("touchstart", startDrawing, { passive: false });
canvas.addEventListener("touchmove", draw, { passive: false });
canvas.addEventListener("touchend", stopDrawing, { passive: false });
canvas.addEventListener("touchcancel", stopDrawing, { passive: false });

function toggleViewable(id) {
    elem = document.getElementById(id);
    if (elem.style.display == "none") {
        elem.style.display = "block";
    } else {
        elem.style.display = "none";
    }

    // if (elem.classList.contains("hidden")) {
    //     elem.classList.remove("hidden");
    //     elem.classList.add("visible");
    // } else {
    //     elem.classList.remove("visible");
    //     elem.classList.add("hidden");
    // }
}

function toggleSource() {
    toggleViewable("main-source");

    main_elem = document.getElementById("main-render");
    if (
        main_elem.classList.contains("split") &&
        main_elem.classList.contains("right")
    ) {
        // If they are present, switch to "full"
        main_elem.classList.remove("split", "right");
        main_elem.classList.add("full");
    } else {
        // Otherwise, switch back to "split" and "right"
        main_elem.classList.remove("full");
        main_elem.classList.add("split", "right");
    }

    button_elem = document.getElementById("split-view");
    if (button_elem.classList.contains("active")) {
        button_elem.classList.remove("active");
    } else {
        button_elem.classList.add("active");
    }
}

document.getElementById("split-view").addEventListener("click", toggleSource);

function toggleToolbarAnim(id) {
    elem = document.getElementById(id);
    // if (elem.style.display == "none") {
    //     elem.style.display = "block";
    // } else {
    //     elem.style.display = "none";
    // }

    if (elem.classList.contains("hidden")) {
        elem.classList.remove("hidden");
        elem.classList.add("visible");
    } else {
        elem.classList.remove("visible");
        elem.classList.add("hidden");
    }
}

function toggleSwitch(element) {
    element.classList.toggle("active");
    toggle_elem = document.getElementById("preview-toggle");
    if (toggle_elem.style.backgroundColor === "rgb(255, 255, 255)") {
        toggle_elem.style.backgroundColor = "#c2a7ef";
    } else {
        toggle_elem.style.backgroundColor = "#ffffff";
    }

    toggleViewable("hidden-preview");
    toggleViewable("view-canvas");
    // toggleViewable("main-toolbox");
    // toggleViewable("hidden-tools");
    toggleToolbarAnim("main-toolbox");
    toggleToolbarAnim("hidden-tools");
    // print("Toggle View")
}

// Prevent scrolling on the entire page while touching the canvas
document.body.addEventListener(
    "touchstart",
    function (e) {
        if (e.target === canvas) {
            e.preventDefault();
        }
    },
    { passive: false }
);

document.body.addEventListener(
    "touchmove",
    function (e) {
        if (e.target === canvas) {
            e.preventDefault();
        }
    },
    { passive: false }
);

// Save initial state
// saveState();

function update(input) {
    // Use Prism to highlight the input value as LaTeX code
    const highlightedCode = Prism.highlight(
        input,
        Prism.languages.latex,
        "latex"
    );
    document.getElementById("highlighted-code").innerHTML = highlightedCode;
}

// Sync scrolling between editable and highlighted areas
function sync_scroll(element) {
    const highlightedCode = document.getElementById("highlighted-code");
    highlightedCode.scrollTop = element.scrollTop;
    highlightedCode.scrollLeft = element.scrollLeft;
}

// Tab key handling
function check_tab(element, event) {
    if (event.key === 'Tab') {
        event.preventDefault();
        const start = element.selectionStart;
        const end = element.selectionEnd;
        // Insert tab character
        element.value = element.value.substring(0, start) + "\t" + element.value.substring(end);
        // Move the cursor after the tab
        element.selectionStart = element.selectionEnd = start + 1;
        // Update the highlighted code
        update(element.value);
    }
}

function recompileLatex() {
    rerenderButton = document.getElementById("rerenderLatexBtn");
    rerenderButton.classList.add("spinner");

    const text = document.getElementById("editable-code").value;
    const formData = new FormData();
    formData.append("latex", text);

    fetch("/recompile_latex", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        return response.json();
    })
    .then(data => {
        // Convert base64 PDF back to blob
        const pdfBlob = base64ToBlob(data.pdf, 'application/pdf');
        const pdfUrl = URL.createObjectURL(pdfBlob);

        // Update the PDF viewer
        const pdfViewer = document.querySelector("#main-render object");
        pdfViewer.data = pdfUrl;

        // Update the LaTeX editor if needed
        const editableCode = document.getElementById("editable-code");
        if (editableCode && data.latex) {
            editableCode.value = data.latex;
            update(data.latex);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    })
    .finally(() => {
        rerenderButton.classList.remove("spinner");
    });
}

document.getElementById("recompile").addEventListener('click', recompileLatex);

// Add this function to restore state from server
async function loadInitialState() {
    const documentId =
        document.querySelector("[data-document-id]").dataset.documentId;
    if (!documentId) return;

    try {
        const response = await fetch(`/api/documents/${documentId}/`);
        const document = await response.json();

        if (document.img_content) {
            const img = new Image();
            img.src = document.img_content;
            img.onload = function () {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                saveState(); // Save initial state to history
            };
        } else {
            saveState(); // Save blank state to history
        }
    } catch (error) {
        console.error("Error loading initial state:", error);
        saveState(); // Save blank state to history if loading fails
    }
}

// Call loadInitialState when the page loads
loadInitialState();
