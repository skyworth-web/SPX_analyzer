document.addEventListener("DOMContentLoaded", function () {
    fetchData();

    document.getElementById("run-analysis").addEventListener("click", async function () {
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';

        const types = ["call", "put"];
        try {
            for (let type of types) {
                await fetch(`/shortvertical/${type}/analyze`, { method: "POST" });
            }
            fetchData();
            this.innerHTML = '<i class="fas fa-sync-alt"></i> Run Analysis';
            this.disabled = false;
            document.getElementById("last-run").textContent =
                `Last run: ${new Date().toLocaleString()}`;
        } catch (err) {
            alert("Error running analysis");
            console.error(err);
        }
    });
});

function fetchData() {
    const types = ["call", "put"];
    const strategies = ["aggressive", "moderate", "conservative"];
    const tableBody = document.querySelector("#results-table tbody");
    tableBody.innerHTML = "";

    types.forEach(type => {
        fetch(`/shortvertical/${type}/data`)
            .then(res => res.json())
            .then(data => {
                for (let strategy of strategies) {
                    const t = data?.trade_opportunities?.[strategy];
                    if (!t) continue;

                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${type.toUpperCase()}</td>
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
    });
}
