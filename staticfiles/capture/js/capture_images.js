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
    const toggleCameraBtn = document.getElementById("toggle-camera-btn");``
    const startCameraBtn = document.getElementById("start-camera-btn");
    const customTagInput = document.getElementById("custom-tag-select");

    //Spinner
    const spinnerIcon = document.getElementById('loading-overlay');

    // 📦 Variables
    let stream;
    let currentCameraIndex = 0;
    let videoDevices = [];
    let preferredCameraId = null;
    let storedImageBlob = null;
    let storedImageSize = 0;
    let storedLatitude = 0;
    let storedLongitude = 0;

    let cameraStartTime = 0; //For time taken by camera to open
    let captureStartTime = 0;  // For total capture workflow timing
    let osmStartTime     = 0;  // For OpenStreetMap fetch timing

    let pendingAddressPromise = null;  // Holds the active OSM fetch
    let resolvedAddress = null;        // Holds resolved display_name (or null on failure)


    // 🔒 Disable capture button initially
    captureBtn.disabled = true;
    captureBtn.style.opacity = "0.5";
    captureBtn.style.pointerEvents = "none";

    // 🔒 Disable startCameraButton button initially
    startCameraBtn.disabled = true;
    startCameraBtn.style.opacity = "0.5";
    startCameraBtn.style.pointerEvents = "none";

    // 🔒 Disable toggleCameraBtn button initially
    toggleCameraBtn.disabled = true;
    toggleCameraBtn.style.opacity = "0.5";
    toggleCameraBtn.style.pointerEvents = "none";

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

    //Functions for Showing and Stopping Spinner...
    function showSpinner() {
        if (spinnerIcon) {
            spinnerIcon.style.display = 'flex';
        } else {
            console.warn('#loading-overlay not found, skipping showSpinner');
        }
    }

    function stopSpinner() {
        if (spinnerIcon) {
            spinnerIcon.style.display = 'none';
        } else {
            console.warn('#loading-overlay not found, skipping stopSpinner');
        }
    }
    //...............spinner.............

    // 🧠 Use jQuery event for Select2
    $('#custom-tag-select').on('select2:select', function (e) {
        const selectedValue = e.params.data.id;
        console.log("📤 Select2 tag selected:", selectedValue);

        if (selectedValue) {
            console.log("✅ Valid tag selected. Enabling Start Camera button.");
            startCameraBtn.disabled = false;
            startCameraBtn.style.opacity = "1";
            startCameraBtn.style.pointerEvents = "auto";
        } else {
            console.log("❌ No tag selected. Disabling Start Camera button.");
            startCameraBtn.disabled = true;
            startCameraBtn.style.opacity = "0.5";
            startCameraBtn.style.pointerEvents = "none";
        }
    });

    // 🔄 Disable Start Camera button when dropdown is cleared
    $('#custom-tag-select').on('select2:clear', function () {
        console.log("🧼 Select2 cleared. Disabling Start Camera button.");
        startCameraBtn.disabled = true;
        startCameraBtn.style.opacity = "0.5";
        startCameraBtn.style.pointerEvents = "none";
    });

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
        }
    })
    .catch(error => {
        console.error("❌ Error in enumerateDevices():", error);
        showMessage("Unable to enumerate devices. Please check permissions.", false);
    });

    // ▶️ Manual camera start
    startCameraBtn.addEventListener("click", () => {
        // 🔄 Reset previous OSM lookup state
        pendingAddressPromise = null;
        resolvedAddress = null;

        console.log("▶️ Start Camera clicked");
        showSpinner(); //Show Spinner

        // 🔥 Custom Tag check before starting the camera
        const customTagValue = customTagInput.value;
        if (!customTagValue) {
            stopSpinner();  //Stop Spinner
            alert("❌ Please select a Tag before starting the Camera!");
            console.error("❌ Tag is required but not selected. Camera won't start.");
            return; // ⛔️ Stop camera start if no tag selected
        }

        console.log("📨 Passing deviceId to startCamera:", preferredCameraId);
        // 📍 Request location within same user gesture
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    storedLatitude  = position.coords.latitude;
                    storedLongitude = position.coords.longitude;

                    // 🗺️ Start background reverse-geocode
                    const lat = storedLatitude.toFixed(6);
                    const lng = storedLongitude.toFixed(6);
                    const nominatimUrl =
                    `https://nominatim.openstreetmap.org/reverse?` +
                    `format=json&lat=${lat}&lon=${lng}` +
                    `&addressdetails=0&namedetails=0&extratags=0&zoom=14`;

                    console.log("⏳ Prefetching address from OSM...");

                    osmStartTime = performance.now(); // ✅ Proper timer stamp
                    pendingAddressPromise = fetch(nominatimUrl)
                    .then(res => res.json())
                    .then(data => {
                        resolvedAddress = data.display_name || "Address not available";
                        console.log(`✅ Prefetched address in ${(performance.now() - osmStartTime).toFixed(1)} ms:`, resolvedAddress);
                    })
                    .catch(err => {
                        console.warn("❌ Failed to prefetch address:", err);
                        resolvedAddress = "Address unavailable";
                    });
                    //background reverse code end

                    // 🔍 Inspect precise DNS/TCP/TLS timing for OSM (Dev only)
                    if (location.hostname === "127.0.0.1") {
                        setTimeout(() => {
                            const entries = performance.getEntriesByType("resource");

                            const osmEntry = entries.find(entry =>
                                entry.initiatorType === "fetch" &&
                                entry.name.includes("nominatim.openstreetmap.org/reverse")
                            );

                            if (osmEntry) {
                                console.log("🧠 OSM Network Timing Breakdown:");
                                const dns = osmEntry.domainLookupEnd - osmEntry.domainLookupStart;
                                const tcp = osmEntry.connectEnd - osmEntry.connectStart;
                                const tls = osmEntry.secureConnectionStart > 0
                                    ? (osmEntry.connectEnd - osmEntry.secureConnectionStart)
                                    : 0;

                                console.log(`→ DNS Lookup      : ${dns.toFixed(2)} ms`);
                                console.log(`→ TCP Connect     : ${tcp.toFixed(2)} ms`);
                                console.log(`→ TLS Handshake   : ${osmEntry.secureConnectionStart > 0 ? tls.toFixed(2) + " ms" : "Reused or HTTP/2"}`);
                                console.log(`→ Total Fetch Time: ${osmEntry.duration.toFixed(2)} ms`);
                            } else {
                                console.warn("⚠️ OSM reverse entry not found in performance logs.");
                            }
                        }, 1000); // Allow enough time for fetch to complete
                    }
                    
                    console.log(`📍 Location granted: Lat ${storedLatitude}, Lng ${storedLongitude}`);
                    document.getElementById("latitude").textContent  = storedLatitude.toFixed(6);
                    document.getElementById("longitude").textContent = storedLongitude.toFixed(6);
                    document.getElementById("image-details").style.display = "block";

                    // Now start the camera
                    startCamera(preferredCameraId);
                    startCameraBtn.style.display = "none";
                },
                error => {
                    console.warn("❌ Location access denied or failed:", error);
                    stopSpinner();  //Stop Spinner
                    alert("Location data is required to start the camera.\nPlease allow location access and try again.");

                    // Hide any “image-details” panel you may have shown
                    document.getElementById("image-details").style.display = "none";

                    // Put the user back at tag selection **and** restore Start‑Camera button
                    startCameraBtn.disabled      = false;
                    startCameraBtn.style.opacity = "1";
                    startCameraBtn.style.pointerEvents = "auto";
                    startCameraBtn.style.display = "inline-block";  // ← **NEW** restore visibility
                    return;  // ⛔️ do not start camera
                },
                { timeout: 5000 }
            );
        } else {
            console.error("❌ Geolocation is not supported by this browser.");
            stopSpinner();  //Stop Spinner
            alert("Your browser does not support location services.\nCannot start camera without location.");

            document.getElementById("image-details").style.display = "none";
            startCameraBtn.disabled      = false;
            startCameraBtn.style.opacity = "1";
            startCameraBtn.style.pointerEvents = "auto";
            startCameraBtn.style.display = "inline-block";  // ← **NEW** restore visibility
            return;
        }
    });

    function startCamera(deviceId = null) {
        // ⏱️ DBG: mark start
        const dbg_t0 = performance.now();

        cameraStartTime = dbg_t0;
        console.log("🔍 Start Camera function triggered");
        console.log("📦 Received deviceId:", deviceId);

        hideMessage();  // clear any prior inline messages

        // build constraints
        let constraints = { video: {} };
        if (deviceId) {
            constraints.video.deviceId = { ideal: deviceId };
            console.log("🎯 Starting camera with deviceId:", deviceId);
        } else {
            constraints.video.facingMode = { ideal: "environment" };
            console.log("🎯 Starting camera with environment facingMode");
        }
        constraints.video.width = { ideal: 640 };
        constraints.video.height = { ideal: 480 };
        constraints.video.frameRate = { ideal: 15, max: 30 };

        console.log("🛠 Constraints for getUserMedia:", constraints);

        // helper to reset UI → go back to tag selection
        function resetUI() {
            // stop any partial stream
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
                video.srcObject = null;
            }
            hideMessage();

            // re-enable Start Camera button
            startCameraBtn.disabled      = false;
            startCameraBtn.style.opacity = "1";
            startCameraBtn.style.pointerEvents = "auto";
            startCameraBtn.style.display = "inline-block";  // ← ensure it's visible
        }

        // primary getUserMedia call
        navigator.mediaDevices.getUserMedia(constraints)
            .then(mediaStream => {
                // ⏱️ DBG: log getUserMedia resolution time
                const dbg_t1 = performance.now();
                console.log(`⏱️ DBG: getUserMedia resolved in ${(dbg_t1 - dbg_t0).toFixed(1)} ms`);

                console.log("✅ getUserMedia success");
                console.log("📡 MediaStream received:", mediaStream);

                stream = mediaStream;
                video.srcObject = stream;
                video.play()
                    .then(() => console.log("🎬 video.play() success"))
                    .catch(err => console.warn("⚠️ video.play() failed:", err));

                console.log("📷 Camera started successfully.");
                video.addEventListener('loadedmetadata', () => {
                    // ⏱️ DBG: log loadedmetadata time
                    const dbg_t4 = performance.now();
                    console.log(`⏱️ DBG: loadedmetadata fired in ${(dbg_t4 - dbg_t0).toFixed(1)} ms`);

                    // Compute and log elapsed time
                    const elapsed = performance.now() - cameraStartTime;
                    console.log(`📷 Camera init completed in ${elapsed.toFixed(1)} ms`);

                    console.log("🎯 Video metadata loaded");

                    const track = stream.getVideoTracks()[0];
                    const actual = track.getSettings();
                    console.log("📸 Actual camera settings:", JSON.stringify(track.getSettings(), null, 2));


                    console.log("🔑 Video Dimensions:", video.videoWidth, "x", video.videoHeight);

                    // enable capture & toggle
                    captureBtn.disabled      = false;
                    captureBtn.style.opacity = "1";
                    captureBtn.style.pointerEvents = "auto";
                    if (videoDevices.length > 1) {
                        console.log("🔲 Multiple cameras detected");
                        toggleCameraBtn.disabled      = false;
                        toggleCameraBtn.style.opacity = "1";
                        toggleCameraBtn.style.pointerEvents = "auto";
                    }
                    console.log("✅ Capture button enabled");
                    stopSpinner();  //Stop Spinner
                });
            })
            .catch(error => {
                console.warn("⚠️ Camera access error:", error);
                console.error("🔴 Error details:", error);

                // if facingMode constraint failed → fallback
                if (!deviceId && error.name === "OverconstrainedError") {
                    console.log("🔄 Attempting fallback camera access...");
                    return navigator.mediaDevices.getUserMedia({ video: true })
                        .then(fbStream => {
                            console.log("✅ Fallback success", fbStream);
                            stream = fbStream;
                            video.srcObject = fbStream;
                            video.play()
                                .then(() => console.log("🎬 video.play() success"))
                                .catch(err => console.warn("⚠️ video.play() failed:", err));

                            video.addEventListener('loadedmetadata', () => {
                                // Compute and log elapsed time for fallback
                                const elapsedFb = performance.now() - cameraStartTime;
                                console.log(`📷 Fallback camera init in ${elapsedFb.toFixed(1)} ms`);

                                console.log("🎯 Fallback metadata loaded");
                                console.log("🔑 Fallback Dimensions:", video.videoWidth, "x", video.videoHeight);

                                captureBtn.disabled      = false;
                                captureBtn.style.opacity = "1";
                                captureBtn.style.pointerEvents = "auto";
                                if (videoDevices.length > 1) {
                                    console.log("🔲 Multiple cameras detected (fallback)");
                                    toggleCameraBtn.disabled      = false;
                                    toggleCameraBtn.style.opacity = "1";
                                    toggleCameraBtn.style.pointerEvents = "auto";
                                }
                                console.log("✅ Fallback capture enabled");
                                stopSpinner();  //Stop Spinner
                            });
                        })
                        .catch(fallbackError => {
                            console.error("❌ Fallback failure:", fallbackError);
                            stopSpinner();  //Stop Spinner
                            alert("Unable to access camera. Please check your device and permissions.");
                            resetUI();  // ← unified reset on fallback failure
                        });
                }

                // all other errors (permission denied, no device, etc.)
                const userMsg =
                    error.name === "NotAllowedError" ? "Camera access denied. Please allow permissions and try again." :
                    error.name === "NotFoundError"    ? "No camera found. Please connect a camera." :
                                                        "Unable to access camera. Please check permissions.";
                
                stopSpinner();  //Stop Spinner
                alert(userMsg);
                resetUI();  // ← unified reset on any other failure
            });
    }

    // 🔄 Toggle camera
    toggleCameraBtn.addEventListener("click", () => {
        showSpinner();
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
        // 1️⃣ Stamp the overall capture start
        captureStartTime = performance.now();
        
        console.log("📸 Capturing image...");
        showSpinner();  // Show loading spinner

        // 👉 Disable all important buttons temporarily
        captureBtn.disabled = true;
        retakeBtn.disabled = true;
        uploadBtn.disabled = true;
        toggleCameraBtn.disabled = true;
        toggleCameraBtn.style.opacity = "0.5";
        toggleCameraBtn.style.pointerEvents = "none";

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

            // 👉 Re-enable buttons for next actions
            retakeBtn.disabled = false;
            uploadBtn.disabled = false;

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
                stopSpinner(); // ⏹️ Stop spinner 
                const totalCaptureTime = performance.now() - captureStartTime;
                console.log(`🤳 Capture workflow completed in ${totalCaptureTime.toFixed(1)} ms`);
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

            // ✅ Smart handling of pre-fetched address
            const drawAddressAndFinalize = (text) => {
                drawText(context, text, startX, startY, boxWidth, padding, 0);
                finalizeCapture();
            };

            if (resolvedAddress) {
                // ✅ Address already available
                console.log("📍 Using prefetched address:", resolvedAddress);
                drawAddressAndFinalize(resolvedAddress);
            } else if (pendingAddressPromise) {
                // ⏳ Still waiting on prefetch — wait before finalizing
                console.log("⏳ Waiting for OSM address before finalizing...");
                pendingAddressPromise.then(() => {
                    const finalAddress = resolvedAddress || "Address unavailable";
                    console.log("📍 Address resolved after capture:", finalAddress);
                    drawAddressAndFinalize(finalAddress);
                });
            } else {
                // 🚫 Prefetch never happened (edge case)
                console.warn("⚠️ No OSM request available. Drawing fallback.");
                drawAddressAndFinalize("Address unavailable");
            }

        } else {
            finalizeCapture();
        }
    });


    // 🔄 Retake
    retakeBtn.addEventListener("click", () => {
        console.log("🔄 Retaking image...");
        showSpinner();
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
            stopSpinner();
        } else {
            console.error("❌ UHID not found! Retake button couldnot work");
            stopSpinner();
        }
        
    });

    // 🚀 Upload
    uploadBtn.addEventListener("click", () => {
        console.log("🚀 Uploading image...");
        showSpinner();  //Show Spinner

        const uhidValue = uhidInput.value.trim();
        if (!uhidValue || isNaN(uhidValue)) {
            stopSpinner();
            alert("❌ UHID is required and must be a valid number!");
            console.error("❌ UHID is invalid:", uhidValue);
            return;
        }

        // Get the Custom Tag value and validate it
        const customTagValue = customTagInput.value;
        if (!customTagValue) {
            stopSpinner();
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
            stopSpinner(); // ⏹️ Hiding spinner as soon as we get json response

            if (data.success) {
                console.log("✅ Image successfully uploaded.");
                document.getElementById("success-message").style.display = "block";
                retakeBtn.style.display = "none";
                uploadBtn.style.display = "none";
                cancelBtn.style.display = "none";
                newButtonsContainer.style.display = "block";
                customTagInput.setAttribute("readonly", true);
                customTagInput.classList.add("disabled-input");
            } else {
                console.error("❌ Upload failed:", data.error);
            }
        })
        .catch(error => {
            stopSpinner();  //iding Spinner on network or Json Errors
            console.error("⚠️ AJAX error:", error);
            alert("An network or json error occurred while uploading. Please try again.");
            });
    }

    // 📜 Helper function to draw text parts
    function drawText(context, address, startX, startY, boxWidth, padding) {
        const textStartX = startX + padding; // Text after map or placeholder
        let textY = startY + padding + 20; // Align with top
    
        context.fillStyle = "white";
        context.font = "16px Arial";
        context.fillText("📍 Location Tag", textStartX, textY);
    
        context.font = "12px Arial"; // Address font
        const maxTextWidth = boxWidth - (2 * padding);
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
