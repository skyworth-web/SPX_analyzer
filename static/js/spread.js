document.getElementById('run-analysis').addEventListener('click', () => {
    document.getElementById('loading-indicator').classList.remove('d-none');

    fetch('/spread/analyze', { method: 'POST' })
        .then(res => res.json())
        .then(() => loadSpreadData())
        .catch(err => console.error(err))
        .finally(() => document.getElementById('loading-indicator').classList.add('d-none'));
});

function loadSpreadData() {
    fetch('/spread/data')
        .then(res => res.json())
        .then(data => {
            const grouped = {
                call: {},
                put: {}
            };

            const deltaBuckets = new Set();

            for (const row of data) {
                const { option_type, delta_bucket, point_spread, avg_credit, high_credit, low_credit } = row;
                deltaBuckets.add(delta_bucket);

                const key = `${point_spread}`;
                if (!grouped[option_type][key]) {
                    grouped[option_type][key] = {};
                }

                grouped[option_type][key][delta_bucket] = {
                    avg: avg_credit,
                    high: high_credit,
                    low: low_credit
                };
            }

            const sortedDeltas = Array.from(deltaBuckets).sort((a, b) => a - b);
            renderPricingTable('call', grouped.call, sortedDeltas);
            renderPricingTable('put', grouped.put, sortedDeltas);
        });
}

function renderPricingTable(type, data, deltas) {
    const table = document.getElementById(`${type}-pricing-table`);
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');

    // Clear existing
    thead.innerHTML = '<th>*Adjustable Spread</th>';
    tbody.innerHTML = '';

    // Header
    deltas.forEach(delta => {
        thead.innerHTML += `<th>${delta.toFixed(2)} Δ</th>`;
    });

    // Rows: Low, Average, High
    ['low', 'avg', 'high'].forEach(metric => {
        for (const point_spread of Object.keys(data).sort((a, b) => a - b)) {
            const row = document.createElement('tr');
            row.innerHTML = `<td>${metric.charAt(0).toUpperCase() + metric.slice(1)} (${point_spread}pt)</td>`;
            deltas.forEach(delta => {
                const value = data[point_spread]?.[delta]?.[metric];
                row.innerHTML += `<td>${value?.toFixed(2) ?? '-'}</td>`;
            });
            tbody.appendChild(row);
        }
    });
}

// Load once on page load
loadSpreadData();
