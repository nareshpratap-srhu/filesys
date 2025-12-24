console.log("✅ view_image.js has loaded correctly!");

function showFullImage(imageUrl, filename, timestamp, sizeKb, sizeMb, location, tag, imageId, userFullName) {
    document.getElementById('fullImage').src = imageUrl;
    document.getElementById('imageFilename').textContent = filename;
    document.getElementById('imageTimestamp').textContent = timestamp;
    document.getElementById('imageSize').textContent = `${sizeKb} KB (${sizeMb} MB)`;
    document.getElementById('imageUploader').textContent = userFullName;



    // Handle location
    if (location) {
        document.getElementById('imageLocation').textContent = location;
        document.getElementById('imageLocationWrapper').classList.remove('d-none');
    } else {
        document.getElementById('imageLocationWrapper').classList.add('d-none');
    }

    // Handle tag
    if (tag) {
        document.getElementById('imageTag').textContent = tag;
        document.getElementById('imageTagWrapper').classList.remove('d-none');
    } else {
        document.getElementById('imageTagWrapper').classList.add('d-none');
    }

    document.getElementById('thumbnailGrid').classList.add('d-none');
    document.getElementById('fullImageContainer').classList.remove('d-none');
}

function showThumbnails() {
    document.getElementById('fullImageContainer').classList.add('d-none');
    document.getElementById('thumbnailGrid').classList.remove('d-none');
}


// Function to get CSRF Token from cookies
function getCSRFToken() {
    let name = "csrftoken=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let cookies = decodedCookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim();
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
