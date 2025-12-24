console.log("✅ upload_file_pdf2pdf.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file");
    const filePreviewList = document.getElementById("file-preview-list");
    const previewCard = document.getElementById("preview-card");
    const form = document.getElementById("upload-form");
    const successMessage = document.getElementById("success-message");
    const customTagSelect = document.getElementById("custom-tag-select");
    const processingMessage = document.getElementById("processing-message");
    const uploadButton = document.getElementById("upload-button");

    // Store File objects directly (no longer storing originalSize)
    let selectedFiles = [];

    /**
     * updatePreview()
     *
     * Renders a list of selected PDFs:
     * - Filename
     * - Tag
     * - Displayed Size (in KB)
     */
    function updatePreview() {
        console.log("Updating file preview...");
        filePreviewList.innerHTML = "";  // Clear existing

        const customTagText = customTagSelect.options[customTagSelect.selectedIndex]?.text || "";

        selectedFiles.forEach((file, index) => {
            console.log(`Adding file to preview: ${file.name} (${(file.size/1024).toFixed(1)} KB)`);
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";  // Bootstrap styling :contentReference[oaicite:8]{index=8}
            li.innerHTML = `
                <div>
                    <strong title="${file.name}">${file.name}</strong><br>
                    <small><strong>Tag:</strong> ${customTagText}</small><br>
                    <small>${(file.size / 1024).toFixed(1)} KB - ${file.type}</small>
                </div>
                <a href="javascript:void(0);" class="delete-file" data-index="${index}" aria-label="Delete">
                    <i class="fas fa-trash-alt"></i>
                </a>
            `;
            filePreviewList.appendChild(li);
        });

        previewCard.style.display = selectedFiles.length ? "block" : "none";  // Show/hide preview card 
        console.log(`Preview updated. Current files in preview: ${selectedFiles.length}`);

        // Enable upload button only if there's ≥1 file selected
        uploadButton.disabled = selectedFiles.length === 0;  // 
    }

    function resetFileInput() {
        fileInput.value = "";  // Clear so user can reselect same files if needed 
    }

    function showAlert(message) {
        alert("❌ " + message);  // All validation alerts prefixed with ❌ 
    }

    // Handle selection of multiple PDFs
    fileInput.addEventListener("change", () => {
        const files = Array.from(fileInput.files);  // Convert FileList to array 
        if (files.length === 0) return;

        processingMessage.style.display = "block";  // Show "Processing..." indicator 

        files.forEach((file) => {
            console.log(`📁 File selected: ${file.name}`);
            console.log(`🔍 Type: ${file.type}`);
            console.log(`📦 Size: ${(file.size / 1024).toFixed(2)} KB`);

            // Validate custom tag
            if (!customTagSelect.value) {
                showAlert("Please select a custom tag before uploading.");  // 
                resetFileInput();
                processingMessage.style.display = "none";
                return;
            }

            // Validate MIME type is PDF
            if (file.type !== "application/pdf") {
                showAlert(`Unsupported file type: ${file.name}. Only PDFs are allowed.`);  // :contentReference[oaicite:16]{index=16}
                return;
            }

            // Prevent duplicates by matching both name and size
            const isDuplicate = selectedFiles.some(
                (f) => f.name === file.name && f.size === file.size
            );  // 
            if (isDuplicate) {
                showAlert(`PDF already added: ${file.name}`);  // 
            } else {
                selectedFiles.push(file);  // Add raw File object
            }
        });

        updatePreview();
        resetFileInput();
        processingMessage.style.display = "none";
    });

    // Handle deletion of individual PDFs from preview
    filePreviewList.addEventListener("click", (e) => {
        const deleteBtn = e.target.closest(".delete-file");
        if (deleteBtn) {
            const index = parseInt(deleteBtn.dataset.index, 10);
            selectedFiles.splice(index, 1);  // Remove one File from array
            updatePreview();
        }
    });

    // Form submission: upload each PDF individually
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        if (!selectedFiles.length) {
            showAlert("No file selected.");
            return;
        }

        processingMessage.style.display = "block";

        const formData = new FormData();
        const customTag = customTagSelect.value;
        const uhid = form.querySelector("input[name='uhid']").value;
        formData.append("uhid", uhid);
        formData.append("custom-tag-select", customTag);

        // Append each PDF under "files"
        selectedFiles.forEach((file) => {
            formData.append("files", file);  // Key "files" matches view.getlist("files") :contentReference[oaicite:19]{index=19}
        });

        fetch("", {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            },
            body: formData
        })
        .then((res) => res.json())
        .then((data) => {
            processingMessage.style.display = "none";
            $('body').css('pointer-events', 'auto');

            if (data.success) {
                $('#success-message').fadeIn();
                form.reset();
                selectedFiles = [];

                customTagSelect.selectedIndex = 0;
                const event = new Event('change');
                customTagSelect.dispatchEvent(event);  // Reset Select2 visually :contentReference[oaicite:20]{index=20}
                console.log(
                    "🟢 Reset Custom Tag to Initial Value:",
                    customTagSelect.value,
                    "Selected Index:",
                    customTagSelect.selectedIndex
                );

                updatePreview();
                setTimeout(() => {
                    $('#success-message').fadeOut();
                }, 2000);
            } else {
                showAlert("Upload failed: " + (data.error || "Unknown error"));
            }
        })
        .catch((err) => {
            console.error("Upload error:", err);
            showAlert("Upload failed. Check console for details.");
            processingMessage.style.display = "none";
            $('body').css('pointer-events', 'auto');
        });
    });
});
