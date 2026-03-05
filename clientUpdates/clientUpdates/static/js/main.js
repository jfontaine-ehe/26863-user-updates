
// ---------- phase2_landing_page -------------------

document.getElementById('pwsFormDelete').addEventListener("submit", function(elem) {
    console.log("in delete button");
    if (!confirm("Are you sure you'd like to delete this form?")) {
        elem.preventDefault();
    }
});

document.getElementById('sourceFormDelete').addEventListener("submit", function(elem) {
    if (!confirm("Are you sure you'd like to delete this form?")) {
        elem.preventDefault();
    }
});

// -------------- source form --------------------------




