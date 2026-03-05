
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


});

pfasEverTested.addEventListener("change", function (e) {

    if(pfasEverTested.value === "No"){
        pfasResultsDiv.classList.add('hidden');
        pfasCommentsDiv.classList.add('hidden');
    } else{
        pfasResultsDiv.classList.remove('hidden')
        pfasCommentsDiv.classList.remove('hidden')
    }

})

pfasDetected.addEventListener("change", function (e) {

    if(pfasDetected.value === "No"){
        pfasResultsDiv.classList.add('hidden');
        pfasCommentsDiv.classList.add('hidden');
    } else{
        pfasResultsDiv.classList.remove('hidden')
        pfasCommentsDiv.classList.remove('hidden')
    }

})

// function that acts on each pfas result input.
// if zero is entered, all other inputs in that row are rendered disabled
pfasResults.forEach(elem => {

    elem.addEventListener("change", function (e) {

        let row = elem.closest('tr')
        let inputsSelects =
            Array.
            from(row.querySelectorAll('input, select')).
            filter(elem => !elem.name.endsWith("result") && !elem.name.endsWith("analyte"))

        if (Number(elem.value) === 0){
            inputsSelects.forEach(e => e.disabled = true);
        } else {
            inputsSelects.forEach(e => e.disabled = false);
        }

    });

});
