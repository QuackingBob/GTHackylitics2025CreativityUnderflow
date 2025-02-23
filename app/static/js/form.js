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
   
    if (!documentId) {
        console.error("No document ID found");
        false;
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
        console.log("Text state saved successfully:", data['success']);
        
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
    document.getElementById("saveButton").addEventListener("click", () => {
        updateButtonState(saveTextState());
    });
    document.getElementById("backButton").addEventListener("click", () => {
        saveTextState();
        window.location.href = "/documents/";
    });
    document.getElementById("renderButton").addEventListener("click", renderLatex);
});

// Function to handle button state change based on success or failure
function updateButtonState(isSaveSuccess) {
    const saveButton = document.getElementById("saveButton");
    const saveIcon = document.getElementById("saveIcon");

    // Clear previous state
    saveButton.classList.remove("green-background", "red-background");
    saveIcon.style.animation = '';  // Remove shake animation

    if (isSaveSuccess) {
        // If save is successful, change the icon and background
        saveButton.classList.add("green-background");
        saveIcon.src = window.iconPaths.checkmark;  // Checkmark icon
    } else {
        // If save fails, change the icon and background
        saveButton.classList.add("red-background");
        saveIcon.src = window.iconPaths.error;  // Error icon
        saveIcon.style.animation = 'shake 0.5s ease ';  // Apply shake animation
    }

    setTimeout(() => {
        saveButton.classList.remove("green-background", "red-background");
        saveIcon.style.animation = '';  // Clear shake animation
        saveIcon.src = window.iconPaths.save;  // Restore the original save icon
    }, 600); 
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