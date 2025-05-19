document.addEventListener("DOMContentLoaded", function () {
    const runButton = document.getElementById("run-analysis");
    const loadingIndicator = document.getElementById("loading-indicator");
    const lastRun = document.getElementById("last-run");

    runButton.addEventListener("click", async function () {
        loadingIndicator.classList.remove("d-none");

        try {
            const response = await fetch("/analyze_spreads");  // Adjust this if your endpoint differs
            if (!response.ok) throw new Error("Network response was not ok");

            const data = await response.json();
            renderTables(data);

            const now = new Date();
            lastRun.textContent = `Last run: ${now.toLocaleString()}`;
        } catch (err) {
            console.error("Error running analysis:", err);
            alert("Failed to run analysis.");
        } finally {
            loadingIndicator.classList.add("d-none");
        }
    });

    function renderTables(data) {
        const container = document.querySelector("#content"); // Replace with a better selector if needed

        // Remove old tables
        const oldTables = container.querySelectorAll("table");
        oldTables.forEach((table) => table.remove());

        ["Call", "Put"].forEach((type) => {
            const typeHeader = document.createElement("h3");
            typeHeader.textContent = `${type} Credit Spreads`;
            container.appendChild(typeHeader);

            const spreads = data[type];
            for (const spread in spreads) {
                const buckets = spreads[spread];

                const spreadHeader = document.createElement("h4");
                spreadHeader.textContent = spread;
                container.appendChild(spreadHeader);

                const table = document.createElement("table");
                table.className = "table table-bordered table-sm text-center";

                const thead = document.createElement("thead");
                thead.className = "thead-dark";

                const trHead = document.createElement("tr");
                trHead.innerHTML = `<th>Time Bucket</th>`;

                const deltas = Object.keys(buckets[Object.keys(buckets)[0]]["Ave"]);
                deltas.forEach((delta) => {
                    const th = document.createElement("th");
                    th.textContent = delta;
                    trHead.appendChild(th);
                });
                thead.appendChild(trHead);
                table.appendChild(thead);

                const tbody = document.createElement("tbody");

                for (const bucket in buckets) {
                    ["Ave", "High", "Low"].forEach((stat) => {
                        const row = document.createElement("tr");
                        const labelCell = document.createElement("th");
                        labelCell.textContent = `${bucket} ${stat}:`;
                        row.appendChild(labelCell);

                        deltas.forEach((delta) => {
                            const td = document.createElement("td");
                            td.textContent = buckets[bucket][stat][delta].toFixed(2);
                            row.appendChild(td);
                        });

                        tbody.appendChild(row);
                    });
                }

                table.appendChild(tbody);
                const wrapper = document.createElement("div");
                wrapper.className = "table-responsive mb-5";
                wrapper.appendChild(table);
                container.appendChild(wrapper);
            }
        });
    }
});
