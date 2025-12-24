console.log("✅ upload_file_image2pdf.js loaded");

document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file");
    const filePreviewList = document.getElementById("file-preview-list");
    const previewCard = document.getElementById("preview-card");
    const form = document.getElementById("upload-form");
    const successMessage = document.getElementById("success-message");
    const customTagSelect = document.getElementById("custom-tag-select");
    const processingMessage = document.getElementById("processing-message");
    const uploadButton = document.getElementById("upload-button");

    // Now store objects: { file: File, originalSize: number }
    let selectedFiles = [];

    // Allow only images and force camera capture
    fileInput.setAttribute("accept", "image/*");
    fileInput.setAttribute("capture", "camera");

    function updatePreview() {
        console.log("Updating file preview...");
        filePreviewList.innerHTML = "";

        const customTagText = customTagSelect.options[customTagSelect.selectedIndex]?.text || "";

        selectedFiles.forEach((entry, index) => {
            const file = entry.file;
            const origSize = entry.originalSize;
            console.log(`Adding file to preview: ${file.name} (${file.size / 1024} KB)`);

            // Build per-file compression message
            let compressionLine = "";
            if (origSize && origSize > file.size) {
                const origKB = (origSize / 1024).toFixed(1);
                const finalKB = (file.size / 1024).toFixed(1);
                compressionLine = `
                    <br>
                    <small class="text-muted text-wrap">
                        • "Compressed from ${origKB} to ${finalKB} KB.
                    </small>
                `;
            }

            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";
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
            filePreviewList.appendChild(li);
        });

        previewCard.style.display = selectedFiles.length ? "block" : "none";
        console.log(`Preview updated. Current files in preview: ${selectedFiles.length}`);
        uploadButton.disabled = selectedFiles.length === 0;
    }

    function resetFileInput() {
        fileInput.value = "";
    }

    function showAlert(message) {
        alert("❌ " + message);
    }

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (!file) return;

        console.log(`📁 File selected: ${file.name}`);
        console.log(`🔍 Type: ${file.type}`);
        console.log(`📦 Size: ${(file.size / 1024).toFixed(2)} KB`);

        processingMessage.style.display = "block";

        // Handle processed (compressed or original) file
        const handleFile = (processedFile, originalSize) => {
            const reader = new FileReader();
            reader.onload = function (event) {
                const img = new Image();
                img.onload = function () {
                    console.log(`📐 Dimensions: ${img.width} x ${img.height}`);
                };
                img.onerror = function () {
                    console.warn("⚠️ Failed to read image dimensions.");
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(processedFile);

            if (!customTagSelect.value) {
                alert("Please select a custom tag before uploading.");
                resetFileInput();
                processingMessage.style.display = "none";
                return;
            }

            const isDuplicate = selectedFiles.some(
                (e) => e.file.name === processedFile.name && e.file.size === processedFile.size
            );
            if (isDuplicate) {
                showAlert("This image has already been added.");
            } else {
                selectedFiles.push({ file: processedFile, originalSize });
            }

            updatePreview();
            resetFileInput();
            processingMessage.style.display = "none";
        };

        // Compress before adding
        new Compressor(file, {
            quality: 0.6,
            success(compressedFile) {
                console.log("✅ Image compressed successfully");
                console.log(`Compressed size: ${(compressedFile.size / 1024).toFixed(2)} KB`);
                handleFile(compressedFile, file.size);
            },
            error(err) {
                console.warn("⚠️ Compression failed, using original file:", err.message);
                handleFile(file, file.size);
            }
        });
    });

    filePreviewList.addEventListener("click", (e) => {
        const deleteBtn = e.target.closest(".delete-file");
        if (deleteBtn) {
            const index = parseInt(deleteBtn.dataset.index, 10);
            selectedFiles.splice(index, 1);
            updatePreview();
        }
    });

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

        try {
            const { PDFDocument } = window.PDFLib;
            const pdfDoc = await PDFDocument.create();

            for (const entry of selectedFiles) {
                const imageFile = entry.file;
                const imageBytes = await imageFile.arrayBuffer();
                let pdfImage;

                if (imageFile.type === "image/jpeg" || imageFile.type === "image/jpg") {
                    pdfImage = await pdfDoc.embedJpg(imageBytes);
                } else if (imageFile.type === "image/png") {
                    pdfImage = await pdfDoc.embedPng(imageBytes);
                } else {
                    showAlert("Unsupported image format.");
                    return;
                }

                const page = pdfDoc.addPage([pdfImage.width, pdfImage.height]);
                page.drawImage(pdfImage, {
                    x: 0,
                    y: 0,
                    width: pdfImage.width,
                    height: pdfImage.height,
                });
            }

            const pdfBytes = await pdfDoc.save();
            const blob = new Blob([pdfBytes], { type: "application/pdf" });
            const pdfFile = new File(
                [blob],
                `images_to_pdf_${Date.now()}.pdf`,
                { type: "application/pdf" }
            );

            formData.append("file", pdfFile);
        } catch (err) {
            console.error("PDF creation error:", err);
            showAlert("Failed to generate PDF from images.");
            return;
        }

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
                    customTagSelect.dispatchEvent(event);
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
