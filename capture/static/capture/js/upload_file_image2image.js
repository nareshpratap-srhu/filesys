console.log("✅ upload_file_image2image.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("file");
  const filePreviewList = document.getElementById("file-preview-list");
  const previewCard = document.getElementById("preview-card");
  const form = document.getElementById("upload-form");
  const successMessage = document.getElementById("success-message");
  const customTagSelect = document.getElementById("custom-tag-select");
  const uploadButton = document.getElementById("upload-button");
  const compressionMsgEl = document.getElementById("compression-message");
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  // Access hideSpinner from the global window object
  const hideSpinner = window.hideSpinner;

  let selectedFile = null;

  // Restrict file input to image files only
  fileInput.setAttribute("accept", "image/*");
  fileInput.removeAttribute("capture"); // Prevent camera from being triggered

  /**
   * Displays an alert with the provided message.
   * @param {string} message - The message to display.
   */
  function showAlert(message) {
    alert("❌ " + message);
  }

  /**
   * Resets the file input field.
   */
  function resetFileInput() {
    fileInput.value = "";
  }

  /**
   * Updates the file preview section with the selected file's details.
   * @param {File} file - The file to preview.
   * @param {number|null} originalSize - The original size of the file before compression.
   */
  function updatePreview(file, originalSize = null) {
    filePreviewList.innerHTML = "";

    const customTagText = customTagSelect.options[customTagSelect.selectedIndex]?.text || "";

    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";
    li.innerHTML = `
      <div>
        <strong title="${file.name}">${file.name}</strong><br>
        <small><strong>Tag:</strong> ${customTagText}</small><br>
        <small>${(file.size / 1024).toFixed(1)} KB - ${file.type}</small>
      </div>
      <a href="javascript:void(0);" class="delete-file" aria-label="Delete">
        <i class="fas fa-trash-alt"></i>
      </a>
    `;
    filePreviewList.appendChild(li);
    previewCard.style.display = "block";

    if (originalSize && originalSize > file.size) {
      compressionMsgEl.innerText = `Compressed from ${(originalSize / 1024).toFixed(1)} KB to ${(file.size / 1024).toFixed(1)} KB successfully.`;
      compressionMsgEl.style.display = "block";
    } else {
      compressionMsgEl.innerText = "";
      compressionMsgEl.style.display = "none";
    }

    uploadButton.disabled = false;
  }

  /**
   * Handles the selected file, compressing it if necessary.
   * @param {File} file - The selected file.
   */
  function handleFileSelection(file) {
    if (!file) return;

    console.log(`📁 File selected: ${file.name}`);
    console.log(`🔍 Type: ${file.type}`);
    console.log(`📦 Size: ${(file.size / 1024).toFixed(2)} KB`);

    if (!customTagSelect.value) {
      showAlert("Please select a custom tag before uploading.");
      resetFileInput();
      return;
    }

    // Allowed image types
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      showAlert("Unsupported file type! Allowed types: JPG, JPEG, PNG.");
      resetFileInput();
      return;
    }

    const processFile = (finalFile, originalSize = null) => {
      selectedFile = finalFile;
      updatePreview(finalFile, originalSize);
      resetFileInput();
    };

    // Compress if file size > 1MB
    if (file.size > 1024 * 1024) {
      new Compressor(file, {
        quality: 0.5,
        success(compressedFile) {
          console.log("✅ Image compressed successfully");
          console.log(`Compressed size: ${(compressedFile.size / 1024).toFixed(2)} KB`);
          processFile(compressedFile, file.size);
        },
        error(err) {
          console.warn("⚠️ Compression failed, using original file:", err.message);
          processFile(file);
        }
      });
    } else {
      processFile(file);
    }
  }

  /**
   * Handles the form submission, sending the selected file via AJAX.
   * @param {Event} e - The form submission event.
   */
  function handleFormSubmission(e) {
    e.preventDefault();

    if (!selectedFile) {
      showAlert("No file selected.");
      return;
    }

    const formData = new FormData();
    formData.append("uhid", form.querySelector("input[name='uhid']").value);
    formData.append("custom-tag-select", customTagSelect.value);
    formData.append("file", selectedFile);

    fetch("", {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken
      },
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          $('#success-message').fadeIn();
          form.reset();
          selectedFile = null;
          filePreviewList.innerHTML = "";
          previewCard.style.display = "none";
          uploadButton.disabled = true;

          customTagSelect.selectedIndex = 0;
          customTagSelect.dispatchEvent(new Event('change'));

          setTimeout(() => $('#success-message').fadeOut(), 2000);
        } else {
          showAlert("Upload failed: " + (data.error || "Unknown error"));
        }
      })
      .catch(err => {
        console.error("Upload error:", err);
        showAlert("Upload failed. Check console for details.");
      })
      .finally(() => {
        if (typeof hideSpinner === "function") hideSpinner();
        $('body').css('pointer-events', 'auto');
      });
  }

  // Event Listeners
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    handleFileSelection(file);
  });

  filePreviewList.addEventListener("click", (e) => {
    const deleteBtn = e.target.closest(".delete-file");
    if (deleteBtn) {
      selectedFile = null;
      filePreviewList.innerHTML = "";
      previewCard.style.display = "none";
      uploadButton.disabled = true;
    }
  });

  form.addEventListener("submit", handleFormSubmission);
});
