document.getElementById('analyzeBtn').addEventListener('click', async () => {
    const inputText = document.getElementById('jsonInput').value;
    let optionsData;

    try {
        optionsData = JSON.parse(inputText);
    } catch (err) {
        alert("Invalid JSON format");
        return;
    }

    try {
        const response = await axios.post('/bs-deviation/api', {
            options_data: optionsData
        });

        if (response.data.status === 'success') {
            displayResults(response.data.results);
        } else {
            alert("Error: " + response.data.message);
        }
    } catch (err) {
        console.error(err);
        alert("Request failed");
    }
});

function displayResults(data) {
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';

    if (!data || data.length === 0) {
        container.innerHTML = '<p>No results found.</p>';
        return;
    }

    const table = document.createElement('table');
    const headers = Object.keys(data[0]);
    const headerRow = table.insertRow();
    headers.forEach(h => {
        const cell = headerRow.insertCell();
        cell.textContent = h;
    });

    data.forEach(row => {
        const tr = table.insertRow();
        headers.forEach(h => {
            const cell = tr.insertCell();
            cell.textContent = typeof row[h] === 'number' ? row[h].toFixed(2) : row[h];
        });
    });

    container.appendChild(table);
}
