console.log("✅ capture_uhid_camera.js has loaded correctly!");

// Initial Setup
let uhidValue = "";
let confirmUhidValue = "";
let activeField = "uhid";

// Grab initial yearPrefix from HTML data attribute
const container = document.getElementById("uhid-container");
let yearPrefix = parseInt(container.dataset.yearPrefix); // e.g., 25

console.log("📅 Initial Year Prefix Loaded:", yearPrefix);

// DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    const uhidField = document.getElementById("uhid");
    const confirmField = document.getElementById("confirm-uhid");

    uhidField.value = `${yearPrefix}/`;
    confirmField.value = `${yearPrefix}/`;
    confirmField.disabled = true;

    setActiveField("uhid");

    uhidField.addEventListener("click", () => setActiveField("uhid"));
    confirmField.addEventListener("click", () => setActiveField("confirm"));
});

// Update active input highlight
function setActiveField(field) {
    activeField = field;
    document.getElementById("uhid-group").classList.remove("active-group");
    document.getElementById("confirm-group").classList.remove("active-group");

    if (field === "uhid") {
        document.getElementById("uhid-group").classList.add("active-group");
    } else {
        document.getElementById("confirm-group").classList.add("active-group");
    }

    console.log("✍️ Active Field Set:", activeField);
}

// Adjust the year prefix (via up/down buttons)
function adjustYearPrefix(delta) {
    yearPrefix += delta;

    // Ensure year prefix stays within sensible range (e.g., 10 to 99)
    if (yearPrefix < 10) yearPrefix = 10;
    if (yearPrefix > 99) yearPrefix = 99;

    console.log("🔄 Year Prefix Updated To:", yearPrefix);

    // Re-render fields with updated year prefix
    updateFields();
}

// Update the values of both input fields
function updateFields() {
    document.getElementById("uhid").value = `${yearPrefix}/` + uhidValue;
    document.getElementById("confirm-uhid").value = `${yearPrefix}/` + confirmUhidValue;
    toggleCaptureButton();
    validateMatch();
}

// Handle keypad input
function handleKeypad(input) {
    console.log("🔘 Keypad Pressed:", input);

    if (input === "⌫" || input.charCodeAt(0) === 9003) {
        backspace();
    } else if (input === "✔" || input.charCodeAt(0) === 10004) {
        submitUHID();
    } else {
        appendDigit(input);
    }
}

// Add digit to current field
function appendDigit(digit) {
    if (activeField === "uhid") {
        uhidValue += digit;
        console.log("🆕 UHID Updated:", uhidValue);
    } else if (activeField === "confirm") {
        if (!uhidValue) {
            console.warn("❗ Confirm field blocked — original UHID required.");
            return;
        }
        if (confirmUhidValue.length >= uhidValue.length) {
            console.warn("❗ Confirm input length reached.");
            return;
        }
        confirmUhidValue += digit;
        console.log("🆕 Confirm UHID Updated:", confirmUhidValue);
    }

    updateFields();
}

// Handle backspace
function backspace() {
    if (activeField === "uhid") {
        uhidValue = uhidValue.slice(0, -1);
        console.log("⌫ UHID After Backspace:", uhidValue);
    } else if (activeField === "confirm") {
        confirmUhidValue = confirmUhidValue.slice(0, -1);
        console.log("⌫ Confirm UHID After Backspace:", confirmUhidValue);
    }

    updateFields();
}

// Enable confirm field and validate match
function toggleCaptureButton() {
    const confirmField = document.getElementById("confirm-uhid");

    if (uhidValue.trim() !== "") {
        confirmField.disabled = false;
        confirmField.placeholder = "Confirm UHID";
    } else {
        confirmField.disabled = true;
        confirmField.placeholder = "Enter UHID first";
        confirmUhidValue = "";
        confirmField.value = `${yearPrefix}/`;
    }
}

// Validate if both UHIDs match
function validateMatch() {
    const tickButton = document.querySelector("button[onclick*='✔']");
    const confirmInput = document.getElementById("confirm-uhid");

    // Reset styles
    tickButton.style.border = "";
    tickButton.style.fontWeight = "";
    tickButton.style.backgroundColor = "";
    confirmInput.style.border = "";

    if (uhidValue && confirmUhidValue.length === uhidValue.length) {
        if (uhidValue === confirmUhidValue) {
            tickButton.disabled = false;
            tickButton.classList.remove("btn-secondary");
            tickButton.classList.add("btn-success");

            tickButton.style.border = "2px solid #198754";
            tickButton.style.fontWeight = "bold";
            tickButton.style.backgroundColor = "#198754";

            console.log("✅ UHIDs match!");
        } else {
            tickButton.disabled = true;
            tickButton.classList.remove("btn-success");
            tickButton.classList.add("btn-secondary");
            confirmInput.style.border = "2px solid red";
            console.warn("❌ UHIDs do not match.");
        }
    } else {
        tickButton.disabled = true;
        tickButton.classList.remove("btn-success");
        tickButton.classList.add("btn-secondary");
    }
}

// Submit final UHID
function submitUHID() {
    if (!uhidValue || !confirmUhidValue || uhidValue !== confirmUhidValue) {
        console.warn("⚠️ Submission blocked: Incomplete or mismatched UHID.");
        return;
    }

    const finalUhid = `${yearPrefix}${uhidValue}`; // remove slash
    console.log("🚀 Submitting UHID:", finalUhid);

    window.location.href = `/uhid_options/?uhid=${finalUhid}`;
}

// Allow physical keyboard interaction
document.addEventListener("keydown", function (event) {
    const key = event.key;

    // Switch field with Tab
    if (key === "Tab") {
        event.preventDefault();
        setActiveField(activeField === "uhid" ? "confirm" : "uhid");
        return;
    }

    if (!["uhid", "confirm"].includes(activeField)) return;

    if (key >= "0" && key <= "9") {
        appendDigit(key);
    } else if (key === "Backspace") {
        backspace();
        event.preventDefault();
    } else if (key === "Enter") {
        submitUHID();
    }
});
