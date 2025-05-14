
function round(value, decimals = 2) {
    return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
}

function createRow(row) {
    return `
    <tr>
      <td>${row.strike}</td>
      <td>${round(row.IV, 3)}</td>
      <td>${round(row.BS_Price)}</td>
      <td>${round(row.market_price)}</td>
      <td>${round(row.Deviation)}</td>
      <td>${round(row.Percent_Deviation)}%</td>
    </tr>
  `;
}

function loadData() {
    fetch('/bs-deviation/data')
        .then(res => res.json())
        .then(data => {
            const callBody = document.querySelector('#call-table tbody');
            const putBody = document.querySelector('#put-table tbody');

            callBody.innerHTML = data.calls.map(createRow).join('');
            putBody.innerHTML = data.puts.map(createRow).join('');
        })
        .catch(err => {
            console.error('Failed to fetch data:', err);
            alert('Error loading data. See console for details.');
        });
}

// Initial load
document.addEventListener('DOMContentLoaded', loadData);