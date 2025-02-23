// Wait for DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize form handling
    const form = document.getElementById("createDocumentForm");
    if (form) {
        form.addEventListener("submit", handleFormSubmit);
    }

    // Initialize modal outside click handling
    const modalOverlay = document.querySelector('.modal-overlay');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                closeModal();
            }
        });
    }

    // Initialize file input display
    const fileInput = document.getElementById("txt_content");
    if (fileInput) {
        fileInput.addEventListener('change', displayFileName);
    }

    // Initialize card hover effects
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mousemove', handleCardHover);
    });

    // Initialize animations
    initializeAnimations();
});

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData();
    const titleInput = document.getElementById("title");
    const txtfile = document.getElementById("txt_content").files[0];

    if (titleInput) {
        formData.append("title", titleInput.value);
    }

    if (txtfile) {
        formData.append("txt_content", txtfile);
    }

    try {
        const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");
        if (!csrfToken) {
            throw new Error("CSRF token not found");
        }

        const response = await fetch("/api/documents/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken.value,
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Error:", errorData);
            throw new Error("Network response was not ok");
        }

        window.location.reload();
    } catch (error) {
        console.error("Error:", error);
        alert("Failed to create document");
    }
}

// Modal functions
function openModal() {
    const modal = document.getElementById('createDocumentModal');
    if (!modal) return;

    modal.style.display = "block";
    modal.classList.add('active');
    
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        gsap.to(modalContent, {
            y: 0,
            opacity: 1,
            duration: 0.5,
            ease: 'power3.out'
        });
    }
}

function closeModal() {
    const modal = document.getElementById('createDocumentModal');
    if (!modal) return;

    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        gsap.to(modalContent, {
            y: -50,
            opacity: 0,
            duration: 0.3,
            ease: 'power3.in',
            onComplete: () => {
                modal.style.display = "none";
                modal.classList.remove('active');
            }
        });
    } else {
        modal.style.display = "none";
        modal.classList.remove('active');
    }
}

// File name display function
function displayFileName() {
    const fileInput = document.getElementById("txt_content");
    const fileName = document.getElementById("file-name");
    
    if (fileInput && fileName) {
        fileName.textContent = fileInput.files.length > 0 
            ? fileInput.files[0].name 
            : "No file chosen";
    }
}

// Card hover handler
function handleCardHover(e) {
    const rect = this.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    this.style.setProperty('--mouse-x', `${x}px`);
    this.style.setProperty('--mouse-y', `${y}px`);
}

// Animation initialization
function initializeAnimations() {
    // Welcome header animation
    gsap.to('.welcome-header', {
        opacity: 1,
        y: 0,
        duration: 1,
        ease: 'power3.out'
    });

    // Cards animation
    gsap.to('.card', {
        opacity: 1,
        y: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'power3.out'
    });

    // Sidebar items animation
    gsap.to('.note-list li', {
        opacity: 1,
        x: 0,
        duration: 0.5,
        stagger: 0.05,
        ease: 'power3.out'
    });
}

async function saveTextContent() {
    const textArea = document.getElementById("large-text-box");
    if (!textArea) return;

    const textContent = textArea.value;
    const docId = document.querySelector(".container").dataset.documentId;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");

    if (!csrfToken) {
        console.error("CSRF token not found.");
        alert("CSRF token missing. Unable to save.");
        return;
    }

    try {
        const response = await fetch(`/save_text/${docId}/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": csrfToken.value,
            },
            body: `txt_content=${encodeURIComponent(textContent)}`,
        });

        if (!response.ok) {
            throw new Error("Failed to save document.");
        }

        const data = await response.json();
        alert(data.message);
    } catch (error) {
        console.error("Error saving:", error);
        alert("Error saving document.");
    }
}
