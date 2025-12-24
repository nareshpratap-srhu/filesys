document.addEventListener('DOMContentLoaded', () => {


    console.log("✅ Capture_image.js has loaded correctly!");

    // 🔗 Element references
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const captureBtn = document.getElementById("capture-btn");
    const retakeBtn = document.getElementById("retake-btn");
    const uploadBtn = document.getElementById("upload-btn");
    const cancelBtn = document.getElementById("cancel-btn");
    const uhidInput = document.getElementById("uhid-input");
    const newButtonsContainer = document.getElementById("new-buttons-container");
    const morePhotosBtn = document.getElementById("more-photos-btn");
    const homeBtn = document.getElementById("home-btn");
    const cameraMessage = document.getElementById("camera-message-container");
    const retryButton = document.getElementById("retry-camera-btn");
    const toggleCameraBtn = document.getElementById("toggle-camera-btn");

    //Start Camera Button
    const startCameraBtn = document.getElementById("start-camera-btn");

    // 📦 Variables
    let stream;
    let currentCameraIndex = 0;
    let videoDevices = [];
    let preferredCameraId = null;
    let storedImageBlob = null;
    let storedImageSize = 0;
    let storedLatitude = 0;
    let storedLongitude = 0;

    // 🔒 Disable capture button initially
    captureBtn.disabled = true;
    captureBtn.style.opacity = "0.5";
    captureBtn.style.pointerEvents = "none";
    retakeBtn.style.display = "none";
    uploadBtn.style.display = "none";
    retryButton.style.display = "none";

    // 📩 Message helpe
    function showMessage(message, showRetry = false) {
        cameraMessage.innerText = message;
        cameraMessage.style.display = "block";
        retryButton.style.display = showRetry ? "block" : "none";
    }

    function hideMessage() {
        cameraMessage.style.display = "none";
        retryButton.style.display = "none";
    }
    
    // 🔍 Get UHID
    function getUHIDFromURL() {
        const params = new URLSearchParams(window.location.search);
        const uhid = params.get("uhid");
        return uhid;
    }

    const uhid = getUHIDFromURL();
    if (uhid) {
        uhidInput.value = uhid;
        console.log("✅ UHID set in form:", uhid);
    } else {
        console.warn("❌ No UHID found in URL!");
    }

    // 📷 Detect cameras
    navigator.mediaDevices.enumerateDevices()
    .then(devices => {

        // Filter video devices
        videoDevices = devices.filter(device => device.kind === "videoinput");
        console.log('🎥 Video devices:', videoDevices);  // Logs only video devices (cameras)

        if (videoDevices.length === 0) {
            console.error("❌ No cameras found.");
            showMessage("No camera found. Please connect a camera.", false);
        } else {
            console.log(`📷 Found ${videoDevices.length} video device(s).`);

            // Try to prefer back/environment-facing camera
            const preferredCamera = videoDevices.find(device =>
                /back|environment/i.test(device.label)
            );
            if (preferredCamera) {
                console.log("🎯 Preferred camera selected:", preferredCamera.label);
                currentCameraIndex = videoDevices.indexOf(preferredCamera);
                preferredCameraId=preferredCamera.deviceId;
                console.log('🔹 Preferred Camera ID set as by IF block: ', preferredCameraId);
            } else {
                console.log("🔁 No environment-facing camera detected, using first available.");
                preferredCameraId= videoDevices[0].deviceId;
                console.log('🔹 Preferred Camera ID set as by ELSE BLOCK : ', preferredCameraId);
            }
            
            // Show camera selection button if more than one video device
            if (videoDevices.length > 1) {
                console.log("🔲 Multiple cameras detected, showing the camera switch button.");
                toggleCameraBtn.style.display = "inline-block";
            } else {
                console.log("🔲 Only one camera detected.");
                toggleCameraBtn.style.display = "none";
            }

        }
    })
    .catch(error => {
        console.error("❌ Error in enumerateDevices():", error);
        showMessage("Unable to enumerate devices. Please check permissions.", false);
    });


    // ▶️ Manual camera start
    startCameraBtn.addEventListener("click", () => {
        console.log("▶️ Start Camera clicked");

        // 🔥 Custom Tag check before starting the camera
        const customTagValue = document.getElementById("custom-tag-select").value;
        if (!customTagValue) {
            alert("❌ Please select a Tag before starting the Camera!");
            console.error("❌ Tag is required but not selected. Camera won't start.");
            return; // ⛔️ Stop camera start if no tag selected
        }

        console.log("📨 Passing deviceId to startCamera:", preferredCameraId);
        startCamera(preferredCameraId);
        startCameraBtn.style.display = "none";
    });

    function startCamera(deviceId = null) {
        
        console.log("🔍 Start Camera function triggered");
        console.log("📦 Received deviceId:", deviceId);  // Log the received deviceId

        hideMessage();
        
        // Create constraints for the media stream
        let constraints = {
            video: {}
        };

        if (deviceId) {
            constraints.video.deviceId = { exact: deviceId };
            console.log("🎯 Starting camera with deviceId:", deviceId);
        } else {
            constraints.video.facingMode = { exact: "environment" };
            console.log("🎯 Starting camera with environment facingMode");
        }
        console.log("🛠 Constraints for getUserMedia:", constraints);  // Log the constraints object

        // Call getUserMedia with the constraints
        navigator.mediaDevices.getUserMedia(constraints)
            .then(mediaStream => {
                console.log("✅ getUserMedia success");

                // Log the received mediaStream details
                console.log("📡 MediaStream received:", mediaStream);

                // Assign the stream to the video element
                stream = mediaStream;
                video.srcObject = stream;
                // Ensure video playback starts — works across iOS/Android/desktop
                video.play().then(() => {
                    console.log("🎬 video.play() success: video is playing");

                    // 📍 Geolocation
                    if (navigator.geolocation) {
                        console.log("📍 Attempting to retrieve geolocation...");
                        navigator.geolocation.getCurrentPosition(
                            position => {
                                storedLatitude = position.coords.latitude;
                                storedLongitude = position.coords.longitude;
                                console.log(`📍 Location captured: Latitude - ${storedLatitude}, Longitude - ${storedLongitude}`);
                                document.getElementById("latitude").textContent = storedLatitude.toFixed(6);
                                document.getElementById("longitude").textContent = storedLongitude.toFixed(6);
                                document.getElementById("image-details").style.display = "block";
                            },
                            error => {
                                console.error("❌ Geolocation error:", error);
                                document.getElementById("latitude").textContent = "N/A";
                                document.getElementById("longitude").textContent = "N/A";
                                document.getElementById("image-details").style.display = "block";
                            },
                            { timeout: 5000 }
                        );
                    } else {
                        console.error("❌ Geolocation is not supported by this browser.");
                        document.getElementById("latitude").textContent = "N/A";
                        document.getElementById("longitude").textContent = "N/A";
                        document.getElementById("image-details").style.display = "block";
                    }


                }).catch(err => {
                    console.warn("⚠️ video.play() failed. Reason:", err);
                    // Optionally: show a "Tap to play video" UI or retry button
                });

                // Log video element details before it starts playing
                console.log("📷 Camera started successfully.");

                // Adding an event listener for when the video metadata is loaded (like video resolution)
                video.addEventListener('loadedmetadata', () => {
                    console.log("🎯 Video metadata loaded");
                    console.log("🎯 Video feed is ready!");

                    // Log video width and height after the video metadata is loaded
                    console.log("🔑 Video Dimensions: ", video.videoWidth, "x", video.videoHeight);

                    // Enable the capture button once camera starts
                    captureBtn.disabled = false;
                    captureBtn.style.opacity = "1";
                    captureBtn.style.pointerEvents = "auto"; 

                    // Log capture button status
                    console.log("✅ Capture button enabled:", !captureBtn.disabled);
                });
            })
            .catch(error => {
                console.warn("⚠️ Camera access error:", error);

                // Log error details
                console.error("🔴 Error details:", error);
                
                // Handle different error cases based on the error name
                if (deviceId || error.name !== "OverconstrainedError") {
                    const msg = error.name === "NotAllowedError"
                        ? "Camera access denied. Click below to retry."
                        : error.name === "NotFoundError"
                            ? "No camera found. Please connect a camera."
                            : "Unable to access the camera. Check permissions.";
                    showMessage(msg, error.name === "NotAllowedError");
                    console.log("📢 Error message shown:", msg);
                } else {
                    // Attempt a fallback if the initial getUserMedia call failed
                    console.log("🔄 Attempting fallback camera access...");
                    navigator.mediaDevices.getUserMedia({ video: true })
                        .then(mediaStream => {
                            console.log("✅ Camera fallback success");

                            // Log the fallback stream
                            console.log("📡 Fallback MediaStream:", mediaStream);

                            stream = mediaStream;
                            video.srcObject = stream;
                            // Ensure video playback starts — works across iOS/Android/desktop
                            video.play().then(() => {
                                console.log("🎬 video.play() success: video is playing");
                            }).catch(err => {
                                console.warn("⚠️ video.play() failed. Reason:", err);
                                // Optionally: show a "Tap to play video" UI or retry button
                            });

                            video.addEventListener('loadedmetadata', () => {
                                console.log("🎯 Video metadata loaded (fallback)");

                                // Log fallback video width and height
                                console.log("🔑 Fallback Video Dimensions: ", video.videoWidth, "x", video.videoHeight);

                                captureBtn.disabled = false;
                                captureBtn.style.opacity = "1";
                                captureBtn.style.pointerEvents = "auto";

                                console.log("✅ Fallback capture button enabled:", captureBtn.disabled);
                            });
                        })
                        .catch(fallbackError => {
                            console.error("❌ Final camera failure:", fallbackError);
                            showMessage("Camera failed to load", true);
                            console.log("📢 Final failure message shown.");
                        });
                }
            });
    }

    // 🔄 Toggle camera
    toggleCameraBtn.addEventListener("click", () => {
        console.log("🔄 Toggle camera clicked!");
        if (videoDevices.length > 1) {
            currentCameraIndex = (currentCameraIndex + 1) % videoDevices.length;

            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }

            startCamera(videoDevices[currentCameraIndex].deviceId);
        }
    });


    // 🔁 Retry camera with permission check
    retryButton.addEventListener("click", () => {
        console.log("🔄 Retry button clicked. Checking camera permission...");

        // Try to check permission state (works in Chrome/Edge)
        if (navigator.permissions && navigator.permissions.query) {
            navigator.permissions.query({ name: 'camera' })
                .then(permissionStatus => {
                    console.log("🔐 Camera permission state:", permissionStatus.state);

                    if (permissionStatus.state === "denied") {
                        // Permission is denied — show user-friendly guide
                        alert("Camera access is currently blocked. Please enable camera permission in your browser settings and then click Retry.");

                        // Optionally show browser help link in UI
                        document.getElementById("camera-message-container").innerHTML = `
                            <p>⚠️ Camera access is blocked. 
                            <a href="https://support.google.com/chrome/answer/2693767" target="_blank">How to enable camera in Chrome</a>.</p>`;
                        retryButton.style.display = "block";
                    } else {
                        // Not explicitly denied — try restarting the camera
                        console.log("📷 Retrying startCamera...");
                        startCamera();
                    }
                })
                .catch(error => {
                    console.warn("❌ Permissions API not supported or error occurred:", error);
                    // Fallback to reloading
                    location.reload();
                });
        } else {
            // Older browsers: fallback to reload
            console.log("📦 Permissions API not available. Reloading page...");
            location.reload();
        }
    });


    // ❌ Cancel
    cancelBtn.addEventListener("click", function() {
        const url = cancelBtn.getAttribute("data-url");
        window.location.href = url;
    });

    // 📸 Capture
    captureBtn.addEventListener("click", () => {
        console.log("📸 Capturing image...");

        // 👉 Show Loading Overlay
        document.getElementById("loading-overlay").style.display = "block";

        // 👉 Disable all important buttons temporarily
        captureBtn.disabled = true;
        retakeBtn.disabled = true;
        uploadBtn.disabled = true;

        const context = canvas.getContext("2d");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Fill white background
        context.fillStyle = "#ffffff";
        context.fillRect(0, 0, canvas.width, canvas.height);

	// Pause the video to freeze the current frame
        video.pause();

        // Draw video frame
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Function to finalize UI & Blob after rendering
        const finalizeCapture = () => {
            video.style.display = "none";
            captureBtn.style.display = "none";
            canvas.style.display = "block";
            canvas.offsetHeight;

            retakeBtn.style.display = "block";
            uploadBtn.style.display = "block";

            stream.getTracks().forEach(track => track.stop());
            console.log("✅ Image captured.");

            // 👉 Hide Loading Overlay when done
            document.getElementById("loading-overlay").style.display = "none";

            // 👉 Re-enable buttons for next actions
            retakeBtn.disabled = false;
            uploadBtn.disabled = false;

            const customTagInput = document.getElementById("custom-tag-select");
            const customTagValue = customTagInput.value;
            localStorage.setItem("customTag", customTagValue);
            console.log("✅ Tag Value:", customTagValue);

            canvas.toBlob(blob => {
                storedImageBlob = blob;
                storedImageSize = blob.size;
                console.log(`📏 Image Size: ${storedImageSize} bytes`);
                document.getElementById("image-size").textContent = `${(storedImageSize / 1024).toFixed(2)} KB`;

                const reader = new FileReader();
                reader.onloadend = () => {
                    const arr = new Uint8Array(reader.result).subarray(0, 4);
                    let header = "";
                    for (let i = 0; i < arr.length; i++) {
                        header += arr[i].toString(16);
                    }

                    switch (header) {
                        case "ffd8ffe0":
                        case "ffd8ffe1":
                        case "ffd8ffe2":
                            console.log("✅ Verified: JPEG file format based on magic number.");
                            break;
                        case "89504e47":
                            console.warn("⚠️ Warning: Image is still in PNG format (magic number matches PNG).");
                            break;
                        default:
                            console.warn("❓ Unknown file format. Magic header:", header);
                    }
                };
                reader.readAsArrayBuffer(blob);
            }, "image/jpeg", 1.0); // can use 0.8 for lower quality
        };
        // GPS Overall if available
        if (storedLatitude && storedLongitude) {
            const lat = storedLatitude.toFixed(6);
            const lng = storedLongitude.toFixed(6);
            const dateStr = new Date().toLocaleString();
        
            const boxWidth = canvas.width - 20; // Full width minus 20px margins
            const padding = 10;
            const mapSize = 90; // Mini-map square size
            const initialBoxHeight = 120; // Adjust based on content
            const startX = 10;
            const startY = canvas.height - initialBoxHeight - 10;
        
            // Draw overlay box
            context.fillStyle = "rgba(0, 0, 0, 0.65)";
            context.fillRect(startX, startY, boxWidth, initialBoxHeight);
        
            console.log("🛠️ Overlay box drawn at bottom of image.");
        
            // Fetch address from OpenStreetMap
            const nominatimUrl = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`;
        
            fetch(nominatimUrl)
                .then(response => response.json())
                .then(data => {
                    const address = data.display_name || "Address not available";
                    console.log("📍 Reverse Geocoded Address:", address);
        
                    // Try loading minimap
                    const mapImg = new Image();
                    mapImg.crossOrigin = "anonymous";
        
                    // Updated Static Map URL (still staticmap.openstreetmap.de)
                    mapImg.src = `https://staticmap.openstreetmap.de/staticmap.php?center=${lat},${lng}&zoom=15&size=${mapSize}x${mapSize}&markers=${lat},${lng},red`;
        
                    mapImg.onload = function () {
                        console.log("🗺️ Mini-map image loaded successfully!");
        
                        // Draw minimap
                        context.drawImage(mapImg, startX + padding, startY + padding, mapSize, mapSize);
        
                        drawText(context, address, startX, startY, boxWidth, padding, mapSize);
                        finalizeCapture();
                    };
        
                    mapImg.onerror = function () {
                        console.warn("⚠️ Mini-map image failed to load, drawing placeholder.");
        
                        // Draw a fallback grey placeholder box
                        context.fillStyle = "grey";
                        context.fillRect(startX + padding, startY + padding, mapSize, mapSize);
        
                        context.fillStyle = "white";
                        context.font = "10px Arial";
                        context.fillText("No Map", startX + padding + 10, startY + padding + 40);
        
                        drawText(context, address, startX, startY, boxWidth, padding, mapSize);
                        finalizeCapture();
                    };
                })
                .catch(error => {
                    console.error("❌ Error fetching address:", error);
                    finalizeCapture();
                });
        
        } else {
            finalizeCapture();
        }
        
        // 📜 Helper function to draw text parts
        function drawText(context, address, startX, startY, boxWidth, padding, mapSize) {
            const textStartX = startX + padding + mapSize + 10; // Text after map or placeholder
            let textY = startY + padding + 20; // Align with top
        
            context.fillStyle = "white";
            context.font = "16px Arial";
            context.fillText("📍 Location Tag", textStartX, textY);
        
            context.font = "12px Arial"; // Address font
            const maxTextWidth = boxWidth - (mapSize + 3 * padding);
            let words = address.split(' ');
            let line = '';
            let lineHeight = 14;
            textY += lineHeight; // Start address after Location Tag
        
            for (let i = 0; i < words.length; i++) {
                let testLine = line + words[i] + ' ';
                let metrics = context.measureText(testLine);
                let testWidth = metrics.width;
                if (testWidth > maxTextWidth && i > 0) {
                    context.fillText(line, textStartX, textY);
                    line = words[i] + ' ';
                    textY += lineHeight;
                } else {
                    line = testLine;
                }
            }
            context.fillText(line, textStartX, textY);
        
            textY += lineHeight + 5;
        
            context.font = "13px Arial";
            context.fillText(`Lat: ${storedLatitude}`, textStartX, textY);
            textY += lineHeight;
            context.fillText(`Lng: ${storedLongitude}`, textStartX, textY);
            textY += lineHeight;
            context.fillText(`📅 ${new Date().toLocaleString()}`, textStartX, textY);
        }
        
        

        
    });


    // 🔄 Retake
    retakeBtn.addEventListener("click", () => {
        console.log("🔄 Retaking image...");
        storedImageBlob = null;
        storedImageSize = 0;
        storedLatitude = 0;
        storedLongitude = 0;

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            console.log("📷 Previous camera stream stopped.");
        }

        canvas.style.display = "none";
        video.style.display = "block";
        captureBtn.style.display = "block";
        retakeBtn.style.display = "none";
        uploadBtn.style.display = "none";

        const uhid = getUHIDFromURL();
        if (uhid) {
            window.location.href = `/cap_pic/?uhid=${uhid}`;
        } else {
            console.error("❌ UHID not found!");
        }
        
    });

    // 🚀 Upload
    uploadBtn.addEventListener("click", () => {
        console.log("🚀 Uploading image...");

        const uhidValue = uhidInput.value.trim();
        if (!uhidValue || isNaN(uhidValue)) {
            alert("❌ UHID is required and must be a valid number!");
            console.error("❌ UHID is invalid:", uhidValue);
            return;
        }

        // Get the Custom Tag value and validate it
        const customTagValue = document.getElementById("custom-tag-select").value;
        if (!customTagValue) {
            alert("❌ Please select a Tag before uploading!");
            console.error("❌ Tag is required but not selected.");
            return; // Prevent upload if no tag is selected
        }

        const reader = new FileReader();
        reader.readAsDataURL(storedImageBlob);
        reader.onloadend = () => {
            const imageData = reader.result;
            console.log("🟡 Custom Tag Value:", customTagValue);
            uploadImage(imageData, uhidValue, customTagValue, storedImageSize, storedLatitude, storedLongitude);
        };
    });

    function uploadImage(imageData, uhidValue, customTagValue, imageSize, latitude, longitude) {
        console.log("📤 JS Helper Function Sending image to server...");
        fetch(window.location.href, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            },
            body: new URLSearchParams({
                image_data: imageData,
                uhid: uhidValue,
                custom_tag: customTagValue,
                image_size: imageSize,
                latitude: latitude,
                longitude: longitude
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log("✅ Image successfully uploaded.");
                document.getElementById("success-message").style.display = "block";
                retakeBtn.style.display = "none";
                uploadBtn.style.display = "none";
                cancelBtn.style.display = "none";
                newButtonsContainer.style.display = "block";
                document.getElementById("custom-tag-select").setAttribute("readonly", true);
                document.getElementById("custom-tag-select").classList.add("disabled-input");
            } else {
                console.error("❌ Upload failed:", data.error);
            }
        })
        .catch(error => console.error("⚠️ AJAX error:", error));
    }

    morePhotosBtn.addEventListener("click", () => {
        const uhid = getUHIDFromURL();
        if (uhid) {
            window.location.href = `/cap_pic/?uhid=${uhid}`;
        } else {
            console.error("❌ UHID not found!");
        }
    });

    homeBtn.addEventListener("click", () => {
        window.location.href = "/";
    });
});
