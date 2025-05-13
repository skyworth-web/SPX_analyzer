document.addEventListener("DOMContentLoaded", function () {
    fetchData();

    document.getElementById("run-analysis").addEventListener("click", function () {
        this.disabled = true;
        this.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Running...`;
        fetch("/spread/analyze", {
            method: "POST"
        })
            .then(res => res.json())
            .then(data => {
                fetchData();
                document.getElementById("run-analysis").innerHTML = `<i class="fas fa-sync-alt"></i> Run Analysis`;
                document.getElementById("run-analysis").disabled = false;
                document.getElementById("last-run").textContent = `Last run: ${new Date(data.timestamp).toLocaleString()}`;
            })
            .catch(err => {
                alert("Error running analysis.");
                console.error(err);
            });
    });
});

function fetchData() {
    fetch("/spread/data")
        .then(res => res.json())
        .then(data => {
            const tbody = document.querySelector("#spread-table tbody");
            tbody.innerHTML = "";

            data.forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
            <td>${new Date(row.timestamp).toLocaleString()}</td>
            <td>${row.option_type.toUpperCase()}</td>
            <td>${row.delta_bucket}</td>
            <td>${row.point_spread}</td>
            <td>${row.avg_credit.toFixed(4)}</td>
            <td>${row.high_credit.toFixed(4)}</td>
            <td>${row.low_credit.toFixed(4)}</td>
          `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => console.error("Failed to fetch spread data:", err));
}
