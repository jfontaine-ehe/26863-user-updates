
// ---------- phase2_landing_page -------------------

let deleteButtons = Array.from(document.querySelectorAll('form'))
    .filter(form => form.querySelector('button.btn.btn-danger'));
console.log(deleteButtons)

deleteButtons.forEach(node =>node.addEventListener("click", function (elem) {
        if (!confirm("Are you sure you'd like to delete this form?")) {
            elem.preventDefault();
        }
    })
);
