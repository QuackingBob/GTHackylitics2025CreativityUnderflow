// Text history management
const textArea = document.getElementById("large-text-box");
let history = [];
let historyIndex = -1;
const MAX_HISTORY = 100;
let autoSaveTimeout; // For debouncing autosave

// Utility function to get cookie value
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

// Save current text state to the server
function saveTextState(button = false) {
    const textContent = textArea.value;
    const documentIdElem = document.querySelector("[data-document-id]");
    if (!documentIdElem) {
        console.error("No document ID element found");
        return;
    }
    const documentId = documentIdElem.dataset.documentId;
    if (!documentId) {
        console.error("No document ID found");
        if (button) {
            updateButtonState(false);
        }
    }

    const formData = new FormData();
    formData.append("txt_content", textContent);

    fetch(`/api/documents/${documentId}/update-state/`, {
        method: "PATCH",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then((data) => {
            console.log("Text state saved successfully:", data["success"]);
            if (button) {
                updateButtonState(data["success"]);
            }
            //  return data['success']
        })
        .catch((error) => {
            console.error("Error saving text state:", error);
            if (button) {
                updateButtonState(false);
            }
        });
}

// Add current content to history
function addToHistory(content) {
    // Remove any forward history if we're not at the latest state
    if (historyIndex < history.length - 1) {
        history = history.slice(0, historyIndex + 1);
    }

    // Add new state to history
    history.push(content);

    // Keep history within maximum size
    if (history.length > MAX_HISTORY) {
        history.shift();
    }

    historyIndex = history.length - 1;
}

// Download current text content as a text file
function downloadText() {
    const text = textArea.textContent;
    console.log(text);
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "document.txt";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Clear the text area and update state
function clearText() {
    textArea.value = "";
    addToHistory("");
    saveTextState();
}

// Load the initial text state from the server
async function loadInitialState() {
    const documentIdElem = document.querySelector("[data-document-id]");
    if (!documentIdElem) {
        console.error("No document ID element found");
        addToHistory("");
        return;
    }
    const documentId = documentIdElem.dataset.documentId;
    if (!documentId) {
        console.error("No document ID found");
        addToHistory("");
        return;
    }

    try {
        const response = await fetch(`/api/documents/${documentId}/`);
        const docData = await response.json();
        if (docData.txt_field) {
            console.log(docData.txt_field);
            textArea.value = docData.txt_field;
            addToHistory(docData.txt_field);
        } else {
            addToHistory(""); // Initialize history with empty state
        }
    } catch (error) {
        console.error("Error loading initial state:", error);
        addToHistory(""); // Initialize history with empty state on error
    }
}

// Render LaTeX content
function renderLatex() {
    const text = textArea.value;
    const formData = new FormData();
    formData.append("latex", text);

    const renderButton = document.getElementById("renderButton");
    const renderButtonIcon = renderButton.querySelector("img");
    renderButtonIcon.classList.add("spinner");

    fetch("/render_presentation/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
    })
        .then((response) => {
            if (!response.ok) throw new Error("Network response was not ok");
            return response.json();
        })
        .then((data) => {
            console.log("Render successful:", data);
        })
        .catch((error) => {
            console.error("Error rendering:", error);
        })
        .finally(() => {
            renderButtonIcon.classList.remove("spinner");
        });
}

// Simple undo/redo functions using execCommand
function undo() {
    document.execCommand("undo", false, null);
}

function redo() {
    document.execCommand("redo", false, null);
}

// Track text area changes and autosave
textArea.addEventListener("input", (e) => {
    clearTimeout(autoSaveTimeout);
    addToHistory(e.target.value);
    autoSaveTimeout = setTimeout(saveTextState, 1000);
});

// Button bindings and initialization on DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
    // Load initial state
    loadInitialState();

    // Bind buttons if they exist
    document.getElementById("penButton")?.addEventListener("click", () => {
        // Additional formatting or features can be added here
    });

    document
        .getElementById("eraserButton")
        .addEventListener("click", clearText);
    document.getElementById("undoButton").addEventListener("click", undo);
    document.getElementById("redoButton").addEventListener("click", redo);
    document
        .getElementById("downloadButton")
        .addEventListener("click", downloadText);
    document.getElementById("saveButton").addEventListener("click", () => {
        saveTextState(true);
        //  console.log(out)
        //  updateButtonState(out);
    });
    document.getElementById("backButton").addEventListener("click", () => {
        saveTextState();
        window.location.href = "/documents/";
    });
    document
        .getElementById("renderButton")
        ?.addEventListener("click", renderLatex);
});

// Function to handle button state change based on success or failure
function updateButtonState(isSaveSuccess) {
    const saveButton = document.getElementById("saveButton");
    const saveIcon = document.getElementById("saveIcon");

    // Clear previous state
    saveButton.classList.remove("green-background", "red-background");
    saveIcon.style.animation = ""; // Remove shake animation

    if (isSaveSuccess) {
        // If save is successful, change the icon and background
        saveButton.classList.add("green-background");
        saveIcon.src = window.iconPaths.checkmark; // Checkmark icon
        saveIcon.style.animation = "shake 0.5s ease ";
    } else {
        // If save fails, change the icon and background
        saveButton.classList.add("red-background");
        saveIcon.src = window.iconPaths.error; // Error icon
        saveIcon.style.animation = "shake 0.5s ease "; // Apply shake animation
    }

    setTimeout(() => {
        saveButton.classList.remove("green-background", "red-background");
        saveIcon.style.animation = ""; // Clear shake animation
        saveIcon.src = window.iconPaths.save; // Restore the original save icon
    }, 600);
}

// Add keyboard shortcuts

document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey) {
        // For Windows/Linux and Mac support
        switch (e.key.toLowerCase()) {
            case "z":
                e.preventDefault();
                if (e.shiftKey) {
                    redo();
                } else {
                    undo();
                }
                break;
            case "y":
                e.preventDefault();
                redo();
                break;
            case "s":
                e.preventDefault();
                saveTextState();
                break;
        }
    }
});
