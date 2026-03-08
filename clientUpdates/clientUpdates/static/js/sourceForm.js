
// -------------- source form --------------------------
const annualFileSelectors = document.querySelectorAll('[id^="annualflow-"][id$="-file_name"]');
const annualDeleteButtons = document.querySelectorAll('[data-target^="annualFile"]');
const annualFileDivs = document.querySelectorAll('[id^="div_annualFile"]');
const annualFiles = document.querySelectorAll('[id^="annualFile"]');
const annualAddFileButton = document.getElementById('annualAddFileButton');
let annualFileNameList = [];

const pfasFileSelectors = document.querySelectorAll('[id^="pfas-"][id$="-file_name"]');
const pfasDeleteButtons = document.querySelectorAll('[data-target^="pfasFile"]');
const pfasFiles = document.querySelectorAll('[id^="pfasFile"]');
const pfasFileDivs = document.querySelectorAll('[id^="div_pfasFile"]');
const pfasAddFileButton = document.getElementById('pfasAddFileButton');
let pfasFileNameList = [];

const pfasResultsDiv = document.getElementById('pfasResultsDiv')
const pfasEverTested = document.getElementById('pfas_ever_tested')
const pfasCommentsDiv = document.getElementById('pfasCommentsDiv')
const pfasDetected = document.getElementById('pfas_detected')

const pfasResults = document.querySelectorAll('[id^="pfas-"][id$="-result"]');
const maxFlowFile = document.getElementById('maxflow-file_name');

const submitButton = document.getElementById('submit');
const loaderContainer = document.getElementById('loader-container');
const loader = document.getElementById('loader');
const pfasFormElem = Array.from(document.getElementById('pfasResultsDiv').querySelectorAll('[id$="analyte"], [id$="units"], [id$="result"], [id$="units"], [id$="sample_date"], [id$="file_name"]')).filter(el => !el.id.startsWith("pfas-6") && !el.id.startsWith("pfas-7"));

function renderFileNames(selectorList, fileNameList) {
   selectorList.forEach(elem => {

        // save previous value, if any
        let selected = elem.value
        // clear list of options
        elem.options.length = 0;

        // re-implement default option
        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "Select a file";
        defaultOption.disabled = true;
        // set default option only if there is no pre-selected value
        defaultOption.selected = !selected;
        elem.appendChild(defaultOption);

        fileNameList.forEach(file => {
            const option = document.createElement("option");
            option.value = file;
            option.textContent = file;
            if (selected === file){
                option.selected = true;
            };
            elem.appendChild(option);
        });

   });
};


function addFiles(button, nodeList) {
    button.addEventListener("click", function () {
        let nearest = Array.from(nodeList).find(elem => elem.classList.contains('hidden'));
        console.log(nearest);
        nearest.classList.remove("hidden");
        nearest.classList.add("d-flex");
        nearest.classList.add("justify-content-between");
    });
}

addFiles(annualAddFileButton, annualFileDivs);
addFiles(pfasAddFileButton, pfasFileDivs);


function deleteButtons(deleteButtonList, fileNameList, selectorList){
    deleteButtonList.forEach(elem => {
        elem.addEventListener("click", function () {
            // get associated fileInput
            const fileInput = document.getElementById(this.dataset.target);
            let parentDiv = elem.parentElement;

            // remove value from fileNameList
            if (fileInput.files.length > 0) {

                // get index of where value is found in array
                const index = fileNameList.indexOf(fileInput.files[0].name);

                // remove value
                if (index !== -1) {
                    fileNameList.splice(index, 1);
                }
            }

            // remove file value and hide
            fileInput.value = "";
            //fileInput.classList.add('hidden');

            // hide the delete button as well
            //elem.classList.add('hidden');
            parentDiv.classList.add('hidden');
            parentDiv.classList.remove('d-flex')

            // re-render filenames
            renderFileNames(selectorList, fileNameList);

        });
    });
};

deleteButtons(annualDeleteButtons, annualFileNameList, annualFileSelectors);
deleteButtons(pfasDeleteButtons, pfasFileNameList, pfasFileSelectors);


function updateFilesOnChange(inputList, fileNameList, selectorList) {

    inputList.forEach(file => {
        file.addEventListener("change", function () {
            // clear the array
            fileNameList.length = 0;
            inputList.forEach(elem => {
                // if the input is visible and has a file loaded
                if (elem.checkVisibility() && elem.files.length > 0) {
                    fileNameList.push(elem.files[0].name);
                };
            });
            renderFileNames(selectorList, fileNameList);
        });
    });
};

updateFilesOnChange(annualFiles, annualFileNameList, annualFileSelectors);
updateFilesOnChange(pfasFiles, pfasFileNameList, pfasFileSelectors);

// function that acts on each pfas result input.
// if zero is entered, all other inputs in that row are rendered disabled
function zeroPfasResults(elem){

    let row = elem.closest('tr')
    let inputsSelects =
        Array.
        from(row.querySelectorAll('input, select')).
        filter(elem => !elem.name.endsWith("result") && !/pfas-[0-5]-analyte$/.test(elem.id));

    if (elem.value !== "" && Number(elem.value) === 0){
        inputsSelects.forEach(e => e.disabled = true)
    } else {
        inputsSelects.forEach(e => e.disabled = false)
    }
}

// functions to run when page is loaded
document.addEventListener("DOMContentLoaded", function () {
    const sourceTypeSelect = document.getElementById('source_type');
    const sourceTypeOtherDiv = document.getElementById('sourceTypeOther');
    const sourceTypeOther = document.getElementById('source_type_other');
    const sourceCoOwned = document.getElementById('source_co_owned');
    const coOwnerInfoDiv = document.getElementById('coOwnerInfo');
    const coOwnerPWSID = document.getElementById('co_owner_pwsid')
    const coOwnerExplained = document.getElementById('co_owner_explained')
    const isPartOfIDWS = document.getElementById('is_part_of_idws')
    const idwsExplanationDiv = document.getElementById('idwsExplanation')
    const idwsExplanation = document.getElementById('idws_explanation')


    // create function that toggles whether the 'hidden' class is applied
    function toggleHiddenRequired() {
        console.log("here");

        // True/False Statements
        tf1 = sourceTypeSelect.value === "Other";
        tf2 = sourceCoOwned.value === "Yes"
        tf3 = isPartOfIDWS.value === "Yes"

        // toggle whether the elements are hidden or not
        sourceTypeOtherDiv.classList.toggle("hidden", !tf1);
        coOwnerInfoDiv.classList.toggle("hidden", !tf2);
        idwsExplanationDiv.classList.toggle("hidden", !tf3);

        // toggle whether they are required.
        sourceTypeOther.required = tf1;
        coOwnerPWSID.required = tf2;
        coOwnerExplained.required = tf2;
        idwsExplanation.required = tf3;

    };

    // once the page is loaded, trigger the function to hide/show based on value
    toggleHiddenRequired();

    // apply function any time there are changes
    sourceTypeSelect.addEventListener("change", toggleHiddenRequired);
    sourceCoOwned.addEventListener("change", toggleHiddenRequired);
    isPartOfIDWS.addEventListener("change", toggleHiddenRequired);

    // when page is first loaded, hide pfas section if necessary based on results
    if (pfasEverTested.value === "No" || pfasDetected.value === "No") {
        pfasResultsDiv.classList.add('hidden');
        pfasCommentsDiv.classList.add('hidden');
        pfasFormElem.forEach(elem => elem.required = false);
    }

    pfasFormElem.forEach(elem => zeroPfasResults(elem));


});

// conditionally hide pfas section, and whether the pfas section is required, based on
// the pfas detection question
pfasEverTested.addEventListener("change", function (e) {

    if(pfasEverTested.value === "No"){
        pfasResultsDiv.classList.add('hidden');
        pfasCommentsDiv.classList.add('hidden');
        pfasFormElem.forEach(elem => elem.required = false);
    } else{
        pfasResultsDiv.classList.remove('hidden');
        pfasCommentsDiv.classList.remove('hidden');
        pfasFormElem.forEach(elem => elem.required = true);
    }

})

// conditionally hide pfas section, and whether the pfas section is required, based on
// the pfas detection question
pfasDetected.addEventListener("change", function (e) {

    if(pfasDetected.value === "No"){
        pfasResultsDiv.classList.add('hidden');
        pfasCommentsDiv.classList.add('hidden');
        pfasFormElem.forEach(elem => elem.required = false)
    } else{
        pfasResultsDiv.classList.remove('hidden');
        pfasCommentsDiv.classList.remove('hidden');
        pfasFormElem.forEach(elem => elem.required = true);
    }

})

// attach zeroPfasResults function to pfasResults on change
pfasResults.forEach(elem => addEventListener("change", function () {
    zeroPfasResults(elem);
}))


// --------- file validation --------------------------

let annualErrorDiv = document.getElementById('annualErrorDiv');
let pfasErrorDiv = document.getElementById('pfasErrorDiv');
let maxFlowErrorDiv = document.getElementById('maxFlowErrorDiv');

document.getElementById('sourceForm').addEventListener('submit', function(event) {

    const clearValidationErrors = () => {
        annualErrorDiv.classList.add('hidden');
        annualFiles.forEach(el => el.classList.remove('is-invalid'));

        pfasErrorDiv.classList.add('hidden');
        pfasFiles.forEach(el => el.classList.remove('is-invalid'));

        maxFlowErrorDiv.classList.add('hidden');
        maxFlowFile.classList.remove('is-invalid');
    };

    const showValidationError = (inputElement, errorElement) => {
        if (errorElement) {
            errorElement.classList.remove('hidden')
        }
        inputElement.classList.add('is-invalid');
    };

    const validateFile = (type, fileInput) => {
        const maxFileSizeBytes = 25 * 1024 * 1024; // Max file size: 25 MB
        let allowedExtensions = []
        if (type === "annual" || type === "maxflow"){
            allowedExtensions = ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png']
        } else if (type === "pfas") {
            allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png']
        }
        const fileName = fileInput.value;
        const fileExtension = fileName.split('.').pop().toLowerCase();
        const file = fileInput.files[0];
        const errorElement = fileInput.closest('div.form-group').nextElementSibling;

        if (!allowedExtensions.includes(fileExtension) || (file && file.size > maxFileSizeBytes)) {
            showValidationError(fileInput, errorElement);
            return false;
        } else {
            return true;
        }

    };

    clearValidationErrors();

    let annualValid = true;
    annualFiles.forEach(elem => {
        if (elem.checkVisibility() && elem.files.length > 0){
            if(!validateFile("annual", elem)){
                annualValid = false;
            }
        }
    })

    let pfasValid = true;
    pfasFiles.forEach(elem => {
        if (elem.checkVisibility() && elem.files.length > 0){
            if(!validateFile("pfas", elem)){
                pfasValid = false;
            }
        }
    })

    let maxFlowValid = true;
    if (maxFlowFile.checkVisibility() && maxFlowFile.files.length > 0) {
    if (!validateFile("maxflow", maxFlowFile)) {
        maxFlowValid = false;
    }
}

    if (!annualValid || !pfasValid || !maxFlowValid) {
        event.preventDefault();
        alert("Please fix validation errors that exist in the form.")
    } else {

        submitButton.disabled = true;
        loaderContainer.style.display = 'flex';
        loader.style.display = 'block';

    }


});

// ------ conditionally require pfas data based on questions ------------------------











