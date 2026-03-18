
// ---------- phase2_landing_page -------------------

const deleteButtons = Array.from(document.querySelectorAll('form'))
    .filter(form => form.querySelector('button.btn.btn-danger'));
const addPWSForm = document.getElementById('addPWSForm');
const addSourceForm = document.getElementById('addSourceForm')
const loaderContainer = document.getElementById('loader-container');
const loader = document.getElementById('loader');

const addFormButtons = Array(addPWSForm, addSourceForm)
console.log(addFormButtons)

deleteButtons.forEach(node =>node.addEventListener("click", function (elem) {
        if (!confirm("Are you sure you'd like to delete this form?")) {
            elem.preventDefault();
        }
    })
);

addFormButtons.forEach(el => el.addEventListener("click", function (el){

    console.log("true")
    el.disabled = true;
    loaderContainer.style.display = 'flex';
    loader.style.display = 'block';

}))


