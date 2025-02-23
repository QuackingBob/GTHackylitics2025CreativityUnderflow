// Text history management
const textArea = document.getElementById("large-text-box")
let history = [];
let historyIndex = -1;
const MAX_HISTORY = 100;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function saveTextState() {
    const textContent = textArea.value;
    const documentId = document.querySelector("[data-document-id]").dataset.documentId;
    console.log(textContent)
    if (!documentId) {
        console.error("No document ID found");
        return;
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
        console.log("Text state saved successfully:", data);
    })
    .catch((error) => {
        console.error("Error saving text state:", error);
    });
}

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

function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        
        textArea.value = history[historyIndex];
        saveTextState();
    }
}

function redo() {
    if (historyIndex < history.length - 1) {
        historyIndex++;
     
        textArea.value = history[historyIndex];
        saveTextState();
    }
}

function downloadText() {
    const text = textArea.value;
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

function clearText() {
    
    textArea.value = "";
    addToHistory("");
    saveTextState();
}

async function loadInitialState() {
    const documentId = document.querySelector("[data-document-id]").dataset.documentId;
     
    if (!documentId) return;

    try {
        const response = await fetch(`/api/documents/${documentId}/`);
        const document = await response.json();
        

        if (document.txt_field) {
             
            console.log(document.txt_field)
            textArea.value = document.txt_field;
            addToHistory(document.txt_content);
        } else {
            addToHistory(""); // Initialize history with empty state
        }
    } catch (error) {
        console.error("Error loading initial state:", error);
        addToHistory(""); // Initialize history with empty state on error
    }
}

function renderLatex() {
    const text = textArea.value;
    const formData = new FormData();
    formData.append("latex", text);

    const renderButton = document.getElementById("renderButton");
    const renderButtonIcon = renderButton.querySelector("img");
    renderButtonIcon.classList.add("spinner");

    fetch("/render", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
    })
    .then(response => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.json();
    })
    .then(data => {
        // Handle the response - this depends on your application's needs
        console.log("Render successful:", data);
    })
    .catch(error => {
        console.error("Error rendering:", error);
    })
    .finally(() => {
        renderButtonIcon.classList.remove("spinner");
    });
}

// Initialize text area change tracking
textArea.addEventListener("input", (e) => {
    clearTimeout(autoSaveTimeout);
    addToHistory(e.target.value);
    autoSaveTimeout = setTimeout(saveTextState, 1000);
});

// Button bindings
document.addEventListener("DOMContentLoaded", () => {
    // Load initial state
    loadInitialState();

    // Bind buttons
    document.getElementById("penButton").addEventListener("click", () => {
        /* Can be used for formatting or other features */
    });
    
    document.getElementById("eraserButton").addEventListener("click", clearText);
    document.getElementById("undoButton").addEventListener("click", undo);
    document.getElementById("redoButton").addEventListener("click", redo);
    document.getElementById("downloadButton").addEventListener("click", downloadText);
    document.getElementById("saveButton").addEventListener("click", saveTextState);
    document.getElementById("backButton").addEventListener("click", () => {
        saveTextState();
        window.location.href = "/documents/";
    });
    document.getElementById("renderButton").addEventListener("click", renderLatex);
});


function updateButtonState(isSaveSuccess) {
    const saveButton = document.getElementById("saveButton");

    // Clear previous state
    saveButton.classList.remove("green-background", "red-background");
    document.querySelector(".checkmark")?.style.display = "none";
    document.querySelector(".xmark")?.style.display = "none";
    document.querySelector(".xmark")?.classList.remove("shake");

    if (isSaveSuccess) {
        // If save is successful
        saveButton.classList.add("green-background");
        const checkmark = document.createElement('div');
        checkmark.classList.add('checkmark');
        saveButton.appendChild(checkmark);
        checkmark.style.display = 'block';
    } else {
        // If save fails
        saveButton.classList.add("red-background");
        const xmark = document.createElement('div');
        xmark.classList.add('xmark', 'shake');
        saveButton.appendChild(xmark);
        xmark.style.display = 'block';
    }
}


// Add keyboard shortcuts




document.addEventListener("keydown", (e) => {
    if (e.ctrlKey || e.metaKey) { // Support for both Windows/Linux and Mac
        switch(e.key.toLowerCase()) {
            case 'z':
                if (e.shiftKey) {
                    e.preventDefault();
                    redo();
                } else {
                    e.preventDefault();
                    undo();
                }
                break;
            case 'y':
                e.preventDefault();
                redo();
                break;
            case 's':
                e.preventDefault();
                saveTextState();
                break;
        }
    }
});