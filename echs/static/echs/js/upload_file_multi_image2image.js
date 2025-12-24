console.log("✅ Upload_file_image2image.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    // Grab all relevant DOM elements
    const fileInput = document.getElementById("file");
    const filePreviewList = document.getElementById("file-preview-list");
    const previewCard = document.getElementById("preview-card");
    const form = document.getElementById("upload-form");
    const successMessage = document.getElementById("success-message");
    const customTagSelect = document.getElementById("custom-tag-select");
    const processingMessage = document.getElementById("processing-message");
    const uploadButton = document.getElementById("upload-button");
    // We no longer need a top‐level compressionMsgEl; each <li> will include its own message
    // const compressionMsgEl = document.getElementById("compression-message");

    // Array to hold all selected (and possibly compressed) File objects
    let selectedFiles = [];
    // Parallel array to track each file's original size for compression messaging
    let originalSizes = [];

    // Ensure only images are selectable and camera capture is disabled
    fileInput.setAttribute("accept", "image/*");  // :contentReference[oaicite:0]{index=0}
    fileInput.removeAttribute("capture");          // :contentReference[oaicite:1]{index=1}

    /**
     * updatePreviewAll()
     *
     * Renders the preview list for all files in selectedFiles[],
     * shows/hides the preview card, and injects each file’s compression message
     * directly inside its own <li> (beneath filename, tag, size/type).
     */
    function updatePreviewAll() {
        // Clear existing preview list
        filePreviewList.innerHTML = "";  // 

        // If no files remain, hide preview and disable Upload button
        if (selectedFiles.length === 0) {
            previewCard.style.display = "none";       // 
            uploadButton.disabled = true;             // 
            return;
        }

        // Otherwise, show the preview card
        previewCard.style.display = "block";         // 

        // Build list items for each selected file
        selectedFiles.forEach((file, index) => {
            const customTagText = customTagSelect.options[customTagSelect.selectedIndex]?.text || "";  // 

            // Determine if this file was compressed (origSize > file.size)
            const origSize = originalSizes[index];
            let compressionLine = "";
            if (origSize && origSize > file.size) {
                const origKB = (origSize / 1024).toFixed(1);
                const finalKB = (file.size / 1024).toFixed(1);
                compressionLine = `<em><br><small class="text-muted text-wrap">• Compressed from ${origKB} to ${finalKB} KB.</small></em>`;  // 
            }

            // Create <li> with file info and compression message inside
            const li = document.createElement("li");
            li.className = "list-group-item";  // keep consistent with Bootstrap styling :contentReference[oaicite:8]{index=8}
            li.innerHTML = `
                <div>
                    <strong title="${file.name}">${file.name}</strong><br>
                    <small><strong>Tag:</strong> ${customTagText}</small><br>
                    <small>${(file.size / 1024).toFixed(1)} KB - ${file.type}</small>
                    ${compressionLine}
                </div>
                <a href="javascript:void(0);" class="delete-file" data-index="${index}" aria-label="Delete">
                    <i class="fas fa-trash-alt"></i>
                </a>
            `;
            filePreviewList.appendChild(li);  // 
        });

        // Enable the Upload button because we have ≥1 file
        uploadButton.disabled = false;  // 
    }

    /**
     * resetFileInput()
     *
     * Clears the file input’s value to allow re-selection of the same files if needed.
     */
    function resetFileInput() {
        fileInput.value = "";  // 
    }

    /**
     * showAlert(message)
     *
     * Utility to alert the user with a ❌ prefix.
     */
    function showAlert(message) {
        alert("❌ " + message);  // 
    }

    /**
     * onFileSelection(evt)
     *
     * Handles the 'change' event when user selects one or more files.
     * Loops through each newly picked File, validates type & tag, checks for duplicates,
     * compresses if >1MB, then appends to selectedFiles[].
     */
    fileInput.addEventListener("change", (evt) => {
        const files = Array.from(evt.target.files);  // 
        if (files.length === 0) return;

        processingMessage.style.display = "block";  // 

        // Validate custom tag is chosen
        if (!customTagSelect.value) {
            showAlert("Please select a custom tag before adding files.");  // 
            resetFileInput();
            processingMessage.style.display = "none";
            return;
        }

        // Allowed MIME types
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];  // :contentReference[oaicite:16]{index=16}

        // Process each newly picked file
        let pendingPromises = files.map((file) => {
            return new Promise((resolve) => {
                console.log(`📁 File selected: ${file.name}`);              // :contentReference[oaicite:17]{index=17}
                console.log(`🔍 Type: ${file.type}`);                       // :contentReference[oaicite:18]{index=18}
                console.log(`📦 Size: ${(file.size / 1024).toFixed(2)} KB`);  // :contentReference[oaicite:19]{index=19}

                // Skip duplicate files (same name & size)
                const isDuplicate = selectedFiles.some(
                    (existing) => existing.name === file.name && existing.size === file.size
                );  // 
                if (isDuplicate) {
                    console.warn(`⚠️ Skipping duplicate: ${file.name}`);  // 
                    return resolve(null);
                }

                // Validate MIME type
                if (!allowedTypes.includes(file.type)) {
                    showAlert(`Unsupported file type for "${file.name}"! Allowed: JPG, JPEG, PNG.`);  // :contentReference[oaicite:22]{index=22}
                    return resolve(null);
                }

                // If >1MB, compress; else, keep original
                if (file.size > 1024 * 1024) {
                    new Compressor(file, {
                        quality: 0.6,
                        success(compressedFile) {
                            console.log(`✅ "${file.name}" compressed successfully`);  // :contentReference[oaicite:23]{index=23}
                            console.log(
                                `🔄 Original: ${(file.size / 1024).toFixed(2)} KB, ` +
                                `Compressed: ${(compressedFile.size / 1024).toFixed(2)} KB`
                            );  // :contentReference[oaicite:24]{index=24}
                            selectedFiles.push(compressedFile);
                            originalSizes.push(file.size);
                            resolve(true);
                        },
                        error(err) {
                            console.warn(
                                `⚠️ Compression failed for "${file.name}", using original.`, 
                                err.message
                            );  // :contentReference[oaicite:25]{index=25}
                            selectedFiles.push(file);
                            originalSizes.push(null);
                            resolve(true);
                        }
                    });
                } else {
                    // No compression needed
                    selectedFiles.push(file);
                    originalSizes.push(null);
                    resolve(true);
                }
            });
        });

        // Once all files have been processed (compressed or not), update the preview
        Promise.all(pendingPromises).then(() => {
            resetFileInput();
            processingMessage.style.display = "none";
            updatePreviewAll();  // 
        });
    });

    /**
     * onPreviewDelete(e)
     *
     * Handles click on the delete icon next to each previewed file.
     * Removes that file (by index) from selectedFiles[], updates preview.
     */
    filePreviewList.addEventListener("click", (e) => {
        const deleteBtn = e.target.closest(".delete-file");
        if (deleteBtn) {
            const idx = parseInt(deleteBtn.getAttribute("data-index"), 10);
            if (!isNaN(idx)) {
                selectedFiles.splice(idx, 1);
                originalSizes.splice(idx, 1);
                updatePreviewAll();  // 
            }
        }
    });

    /**
     * onFormSubmit(e)
     *
     * Intercepts the form submission, packages all selectedFiles[] into FormData,
     * then sends via fetch() to the same URL (relative) with CSRF token.
     */
    form.addEventListener("submit", (e) => {
        e.preventDefault();

        if (selectedFiles.length === 0) {
            showAlert("No files selected.");  // 
            return;
        }

        processingMessage.style.display = "block";  // 

        const formData = new FormData();
        formData.append("uhid", form.querySelector("input[name='uhid']").value);
        formData.append("custom-tag-select", customTagSelect.value);

        // Append each file under "files" (backend should use request.FILES.getlist("files"))
        selectedFiles.forEach((file) => {
            formData.append("files", file);
        });  // 

        fetch("", {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            processingMessage.style.display = "none";
            $('body').css('pointer-events', 'auto');

            if (data.success) {
                $('#success-message').fadeIn();
                form.reset();

                // Reset our JS state
                selectedFiles = [];
                originalSizes = [];
                updatePreviewAll();  // 

                // Reset tag dropdown
                customTagSelect.selectedIndex = 0;
                customTagSelect.dispatchEvent(new Event('change'));

                setTimeout(() => $('#success-message').fadeOut(), 2000);
            } else {
                showAlert("Upload failed: " + (data.error || "Unknown error"));  // 
            }
        })
        .catch(err => {
            console.error("Upload error:", err);
            showAlert("Upload failed. Check console for details.");  // 
            processingMessage.style.display = "none";
            $('body').css('pointer-events', 'auto');
        });
    });
});
