document.addEventListener("DOMContentLoaded", function () {
    fetchData();

    document.getElementById("run-analysis").addEventListener("click", function () {
        this.disabled = true;
        this.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Running...`;
        fetch(`/shortvertical/${OPTION_TYPE}/analyze`, { method: "POST" })
            .then(res => res.json())
            .then(data => {
                fetchData();
                this.disabled = false;
                this.innerHTML = `<i class="fas fa-sync-alt"></i> Run Analysis`;
                document.getElementById("last-run").textContent = `Last run: ${new Date(data.timestamp).toLocaleString()}`;
            })
            .catch(err => {
                alert("Error running analysis");
                console.error(err);
            });
    });
});

function fetchData() {
    fetch(`/shortvertical/${OPTION_TYPE}/data`)
        .then(res => res.json())
        .then(data => {
            const tableBody = document.querySelector("#results-table tbody");
            tableBody.innerHTML = "";

            const tradeData = data.trade_opportunities;
            for (let strategy of ["aggressive", "moderate", "conservative"]) {
                const t = tradeData[strategy];
                if (!t) continue;

                const row = document.createElement("tr");
                row.innerHTML = `
            <td>${strategy}</td>
            <td>${t.short_leg}</td>
            <td>${t.long_leg}</td>
            <td>${t.premium}</td>
            <td>${t.max_loss}</td>
            <td>${t.reward_to_risk}</td>
            <td>${t.short_leg_delta}</td>
            <td>${t.iv}</td>
            <td>${t.gamma}</td>
            <td>${t.theta}</td>
          `;
                tableBody.appendChild(row);
            }
        });
}
