const loaderContainer = document.getElementById('loader-container');
const loader = document.getElementById('loader');
const submitButton = document.getElementById('final-submit');
const pwsForm = document.getElementById('pwsInfoForm');
const privateCodeDiv = document.getElementById('privateCodeDiv')
const stateFedSueDiv = document.getElementById('stateFedSueDiv')
const sdwisCode = document.getElementById('sdwis_owner_code')

// --------------------------------- functions -------------------------------

function showLoaderDisableEl(el){
    el.disabled = true;
    loaderContainer.style.display = 'flex';
    loader.style.display = 'block';
}

// --------------------------------do stuff ------------------------------------
pwsForm.addEventListener('submit', function(event){

    showLoaderDisableEl(submitButton)

});


document.getElementById('save_draft').addEventListener("click", function (event){

    document.querySelectorAll('[required]').
    forEach(el => el.required = false);

    document.getElementById('draft_complete').value = "draft";

    loaderContainer.style.display = 'flex';
    loader.style.display = 'block';
    pwsForm.submit();

})


document.addEventListener("DOMContentLoaded", function () {

    sdwisCode.addEventListener("change", function(){

        let code = sdwisCode.value;
        if(code === "P"){
            privateCodeDiv.hidden = false;
            privateCodeDiv.querySelector('select').required = true;

            stateFedSueDiv.hidden = true;
            stateFedSueDiv.querySelector('select').required = false;
            stateFedSueDiv.querySelector('select').value = "";
        }

        if(code === "F" || code === "S"){

            stateFedSueDiv.hidden = false;
            stateFedSueDiv.querySelector('select').required = true;

            privateCodeDiv.hidden = true;
            privateCodeDiv.querySelector('select').required = false;
            privateCodeDiv.querySelector('select').value = "";

        }
        if(code !== "P" && code !== "S" && code !== "F"){
            privateCodeDiv.hidden = true;
            privateCodeDiv.querySelector('select').required = false;
            privateCodeDiv.querySelector('select').value = "";

            stateFedSueDiv.hidden = true;
            stateFedSueDiv.querySelector('select').required = false;
            stateFedSueDiv.querySelector('select').value = "";
        }

    })

})