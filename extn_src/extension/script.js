// Function to create and insert a new div element
function insertDiv() {
    // Create a new div element
    var newDiv = document.createElement('div');

    // Set the content and attributes of the new div
    newDiv.textContent = 'This is a new div!';
    newDiv.id = 'newDiv';
    newDiv.style.backgroundColor = 'lightblue';
    newDiv.style.padding = '10px';
    newDiv.style.marginTop = '10px';

    // Get the container element where the new div will be inserted
    var container = document.body;

    // Insert the new div as the last child of the container
    container.appendChild(newDiv);
}

// Call the function to insert the new div
insertDiv();
