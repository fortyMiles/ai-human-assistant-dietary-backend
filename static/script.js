document.addEventListener("DOMContentLoaded", function() {
    fetchData();
});

async function fetchData() {
    try {
        const response = await fetch('http://107.23.162.117:8080/survey/'); // Make sure to include http://
        const data = await response.json();

        // Display the number of items collected
        displayTotalCount(data.num);

        // Generate tables for 'rate' and 'rank' data
        displayTable(data.rate, 'rateTable', ['Type', 'Mean', 'std']);
        displayTable(data.rank, 'rankTable', ['Type', 'top1 %', 'top2 %']);
    } catch (error) {
        console.error('Error fetching data: ', error);
        document.getElementById('rateTable').innerHTML = '<p>Error loading data.</p>';
        document.getElementById('rankTable').innerHTML = '<p>Error loading data.</p>';
    }
}

function displayTotalCount(num) {
    const totalCountElement = document.createElement('p');
    totalCountElement.textContent = `Total Data Collected: ${num}`;
    document.body.insertBefore(totalCountElement, document.body.firstChild);
}

function displayTable(data, elementId, headers) {
    const table = document.createElement('table');
    let headerRow = document.createElement('tr');
    headers.forEach(header => {
        let headerCell = document.createElement('th');
        headerCell.textContent = header;
        headerRow.appendChild(headerCell);
    });
    table.appendChild(headerRow);

    data.forEach(item => {
        let row = document.createElement('tr');
        headers.forEach(header => {
            let cell = document.createElement('td');
            // Using the original header to access the property correctly
            let key = header; // Keep the original header format
            if (key.includes("%")) { // If the key has a % symbol, access using bracket notation
                key = key.replace(/\s+/g, ' ').trim(); // Ensure no extra spaces
            } else {
                key = key.toLowerCase().replace(/\s+/g, ''); // For other keys without %, process normally
            }
            let value = item[key];
            if (typeof value === 'number') {
                value = value.toFixed(2); // Format the number with two decimal places
            }
            cell.textContent = value;
            row.appendChild(cell);
        });
        table.appendChild(row);
    });

    document.getElementById(elementId).innerHTML = '';
    document.getElementById(elementId).appendChild(table);
}

