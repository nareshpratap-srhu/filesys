console.log("✅ upload_file.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file");
    const fileLabel = document.getElementById("file-label");
    const filePreviewList = document.getElementById("file-preview-list");
    const previewCard = document.getElementById("preview-card");
    const form = document.getElementById("upload-form");
    const successMessage = document.getElementById("success-message");
    const btnPDF = document.getElementById("btn-pdf");
    const btnImage = document.getElementById("btn-image");
    const customTagSelect = document.getElementById("custom-tag-select");

    let selectedFiles = [];
    let currentType = "pdf";

    const ACCEPTS = {
        pdf: ["application/pdf"],
        image: ["image/jpeg", "image/jpg", "image/png"]
    };

    // Debug: Print value when selection changes
    customTagSelect.addEventListener("change", () => {
        console.log("🟢 Custom Tag Changed - New Selection:", customTagSelect.options[customTagSelect.selectedIndex].text);
    });

    function isValidFileType(file, typeGroup) {
        console.log(`Checking if file ${file.name} (${file.type}) is valid for ${typeGroup} mode.`);
        return ACCEPTS[typeGroup].includes(file.type);
    }

    function updatePreview() {
        console.log("Updating file preview...");
        filePreviewList.innerHTML = "";  // Clear the previous preview items

        // Get the selected custom tag value
        const customTagValue = customTagSelect.options[customTagSelect.selectedIndex].text;  // Get the text of the selected custom tag

        selectedFiles.forEach((file, index) => {
            console.log(`Adding file to preview: ${file.name} (${file.size / 1024} KB)`);

            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";
            li.innerHTML = `
                <div>
                    <strong title="${file.name}">${file.name}</strong><br>
                    <small><strong>Tag:</strong> ${customTagValue}</small><br>
                    <small>${(file.size / 1024).toFixed(1)} KB - ${file.type}</small>
                    <span class="tooltip">${file.name}</span> <!-- Tooltip with full file name -->
                    
                </div>
                <a href="javascript:void(0);" class="delete-file" data-index="${index}" aria-label="Delete">
                    <i class="fas fa-trash-alt"></i>
                </a>
            `;
            filePreviewList.appendChild(li);
        });
        previewCard.style.display = selectedFiles.length ? "block" : "none";
        console.log(`Preview updated. Current files in preview: ${selectedFiles.length}`);
    }

    function resetFileInput() {
        console.log("Resetting file input.");
        fileInput.value = "";
    }

    function showAlert(message) {
        alert("❌ " + message);
        console.log("Alert: " + message);
    }

    // Handle PDF mode
    btnPDF.addEventListener("click", () => {
        console.log("Switching to PDF mode...");
        currentType = "pdf";
        btnPDF.classList.add("active");
        btnImage.classList.remove("active");

        fileInput.accept = ".pdf";
        fileInput.multiple = false;
        fileLabel.textContent = "Choose PDF File";

        selectedFiles = [];

        // Reset to initial/default value
         customTagSelect.selectedIndex = 0;
        // Manually trigger the change event to update the visual state
         const event = new Event('change');
         customTagSelect.dispatchEvent(event);
         // Log the selected value and selected index
         console.log("🟢 Reset Custom Tag to Initial Value:", customTagSelect.value, "Selected Index:", customTagSelect.selectedIndex);

        updatePreview();
        resetFileInput();
    });

    // Handle Image mode
    btnImage.addEventListener("click", () => {
        console.log("Switching to Image mode...");
        currentType = "image";
        btnImage.classList.add("active");
        btnPDF.classList.remove("active");

        fileInput.accept = "images/*";
        fileInput.multiple = false;
        fileLabel.textContent = "Choose Image Files";

        selectedFiles = [];


        // Reset to initial/default value
        customTagSelect.selectedIndex = 0;
        // Manually trigger the change event to update the visual state
        const event = new Event('change');
        customTagSelect.dispatchEvent(event);
        // Log the selected value and selected index
        console.log("🟢 Reset Custom Tag to Initial Value:", customTagSelect.value, "Selected Index:", customTagSelect.selectedIndex);


        updatePreview();
        resetFileInput();
    });

    // Handle file selection
    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (!file) {
            console.log("No file selected.");
            return;
        }

        console.log("Selected file:", file);

        // Check if a custom tag is selected
        if (!customTagSelect.value) {
            alert("Please select a custom tag before uploading.");
            resetFileInput();  // Reset file input to clear selection
            return;
        }

        // Validate the file type
        if (!isValidFileType(file, currentType)) {
            console.log(`Invalid file type. Expected ${currentType} file, got ${file.type}.`);
            showAlert(`Invalid file type. Please select a valid ${currentType.toUpperCase()} file.`);
            resetFileInput();
            return;
        }

        // Handle PDF file selection
        if (currentType === "pdf") {
            console.log("PDF file selected:", file.name);
            selectedFiles = [file];
        } else {
            // Handle Image file selection (prevent duplicates)
            const isDuplicate = selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (isDuplicate) {
                console.log("This image has already been added.");
                showAlert("This image has already been added.");
            } else {
                selectedFiles.push(file);
                console.log(`Added image file: ${file.name}`);
            }
        }

        updatePreview();
        resetFileInput();
    });

    // Handle deletion of files
    filePreviewList.addEventListener("click", (e) => {
        if (e.target.closest(".delete-file")) {
            const index = parseInt(e.target.closest(".delete-file").dataset.index);
            console.log(`Deleting file at index ${index}: ${selectedFiles[index].name}`);
            selectedFiles.splice(index, 1);
            updatePreview();
        }
    });

    // Handle form submission
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        if (selectedFiles.length === 0) {
            console.log("No files selected for upload.");
            showAlert("No file selected.");
            return;
        }

        console.log(`Preparing to upload ${selectedFiles.length} file(s).`);

        const formData = new FormData();
        const customTag = document.getElementById("custom-tag-select").value;
        const uhid = form.querySelector("input[name='uhid']").value;

        formData.append("uhid", uhid);
        formData.append("custom-tag-select", customTag);

        if (currentType === "pdf") {
            formData.append("file", selectedFiles[0]);
            console.log(`Appending PDF file ${selectedFiles[0].name} to form data.`);
        } else {
            try {
                console.log("Starting PDF creation from images...");

                console.log("🔍 Checking pdfLib:", window.pdfLib);  // Debug log
                console.log("🔍 Checking PDFLib:", window.PDFLib);


                const { PDFDocument } = window.PDFLib;
                console.log("pdfLib loaded:", PDFDocument);

                const pdfDoc = await PDFDocument.create();
                console.log("PDF document created.");

                for (const imageFile of selectedFiles) {
                    console.log("Processing image:", imageFile.name);

                    const imageBytes = await imageFile.arrayBuffer();
                    console.log("Image bytes:", imageBytes);

                    let pdfImage;
                    if (imageFile.type === "image/jpeg" || imageFile.type === "image/jpg") {
                        console.log("Embedding JPEG image...");
                        pdfImage = await pdfDoc.embedJpg(imageBytes);
                    } else if (imageFile.type === "image/png") {
                        console.log("Embedding PNG image...");
                        pdfImage = await pdfDoc.embedPng(imageBytes);
                    } else {
                        console.log("Unsupported image format:", imageFile.type);
                        showAlert("Unsupported image format.");
                        return;
                    }

                    console.log("Image embedded. Dimensions:", pdfImage.width, pdfImage.height);

                    const page = pdfDoc.addPage([pdfImage.width, pdfImage.height]);
                    page.drawImage(pdfImage, {
                        x: 0,
                        y: 0,
                        width: pdfImage.width,
                        height: pdfImage.height,
                    });
                }

                const pdfBytes = await pdfDoc.save();
                console.log("PDF document saved.");

                const blob = new Blob([pdfBytes], { type: "application/pdf" });
                const filename = `images_to_pdf_${Date.now()}.pdf`;
                const pdfFile = new File([blob], filename, { type: "application/pdf" });

                formData.append("file", pdfFile);
                console.log("PDF file created:", pdfFile);
            } catch (err) {
                console.error("🔥 Error creating PDF:", err);
                showAlert("Failed to generate PDF from images.");
                return;
            }
        }

        fetch("", {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                successMessage.style.display = "block";
                form.reset();
                selectedFiles = [];
                
                // Reset to initial/default value
                customTagSelect.selectedIndex = 0;
                // Manually trigger the change event to update the visual state
                const event = new Event('change');
                customTagSelect.dispatchEvent(event);
                // Log the selected value and selected index
                console.log("🟢 Reset Custom Tag to Initial Value:", customTagSelect.value, "Selected Index:", customTagSelect.selectedIndex);


                updatePreview();
                console.log("✅ Upload successful");
            } else {
                console.log("Upload failed: ", data.error || "Unknown error");
                showAlert("Upload failed: " + (data.error || "Unknown error"));
            }
        })
        .catch(err => {
            console.error("🔥 Upload error:", err);
            showAlert("Upload failed. Check console for details.");
        });
    });
});
