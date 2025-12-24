console.log("✅ base.js has loaded correctly!");

// JavaScript to handle button clicks and change dynamic content

// Example of handling button clicks dynamically
document.querySelectorAll('footer button').forEach(button => {
    button.addEventListener('click', function(event) {
        // You can handle dynamic content loading here
        // For now, it simply redirects to the corresponding page
        window.location.href = event.target.getAttribute('onclick').match(/'([^']+)'/)[1];
    });
});
