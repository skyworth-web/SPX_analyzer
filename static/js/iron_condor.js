// document.addEventListener('DOMContentLoaded', function() {
// Format timestamp
function formatTime(timestamp) {
  const options = {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  };
  return new Date(timestamp).toLocaleTimeString("en-US", options);
}

// Get score class based on value
function getScoreClass(score) {
  if (score >= 80) return "score-high";
  if (score >= 50) return "score-medium";
  return "score-low";
}

// Get IV class based on value
function getIvClass(iv) {
  if (iv >= 30) return "iv-high";
  if (iv >= 20) return "iv-medium";
  return "iv-low";
}

// Format currency
function formatCurrency(value) {
  return "$" + parseFloat(value).toFixed(2);
}

// Format delta balance
function formatDeltaBalance(callDelta, putDelta) {
  const balance = Math.abs(callDelta - putDelta).toFixed(2);
  return `<span class="greek-value ${balance > 0.15 ? "delta-positive" : "delta-negative"
    }">${balance}</span>`;
}

async function loadDashboard() {
  try {
    console.log("Loading dashboard...");
    const statusResponse = await fetch("/iron-condor/status");
    const status = await statusResponse.json();

    document.getElementById("status").innerHTML = `
                    <i class="fas fa-chart-line me-2"></i>SPX: <strong>${status.spx_price.toFixed(
      2
    )}</strong> 
                    | Last Analysis: <strong>${formatTime(
      status.last_analysis
    )}</strong>
                `;

    document.getElementById("refresh-time").innerHTML = `
                    <i class="fas fa-clock me-2"></i>Updated: <strong>${formatTime(
      Date.now()
    )}</strong>
                `;

    const dataResponse = await fetch("/iron-condor/analysis");
    const data = await dataResponse.json();

    const tbody = document.querySelector("#opportunities tbody");
    tbody.innerHTML = data.scored_trades
      .map(
        (trade) => `
                    <tr>
                        <td class="score-cell ${getScoreClass(trade.score)}">
                            ${trade.score.toFixed(1)}
                        </td>
                        <td class="strikes-cell">
                            ${trade.short_put}/${trade.long_put} - ${trade.short_call
          }/${trade.long_call}
                        </td>
                        <td class="text-success fw-bold">
                            ${formatCurrency(trade.premium)}
                        </td>
                        <td class="text-danger fw-bold">
                            ${formatCurrency(trade.max_loss)}
                        </td>
                        <td>
                            ${formatDeltaBalance(
            trade.short_call_delta,
            trade.short_put_delta
          )}
                        </td>
                        <td class="iv-value ${getIvClass(
            (trade.call_iv + trade.put_iv) / 2
          )}">
                            ${((trade.call_iv + trade.put_iv) / 2).toFixed(1)}%
                        </td>
                        <td>
                            <button class="action-btn btn-success" onclick='addPosition(${JSON.stringify(
            trade
          )})'>
                                <i class="fas fa-plus-circle me-1"></i>Open
                            </button>
                        </td>
                    </tr>
                `
      )
      .join("");

    const positions = document.getElementById("positions");
    positions.innerHTML = data.current_positions
      .map(
        (position) => `
                    <li class="position-item">
                        <div>
                            <span class="position-strikes">${position.short_put
          }/${position.long_put} - ${position.short_call}/${position.long_call
          }</span>
                            <div class="position-time">Opened: ${formatTime(
            position.timestamp
          )}</div>
                        </div>
                        ${position.closed
            ? `
                            <span class="badge badge-closed rounded-pill">
                                <i class="fas fa-lock me-1"></i>Closed
                            </span>
                        `
            : `
                            <button class="action-btn btn-danger" onclick="closePosition('${position.id}')">
                                <i class="fas fa-times-circle me-1"></i>Close
                            </button>
                        `
          }
                    </li>
                `
      )
      .join("");

    // Update status indicator icon
    document.querySelector("#status i").className =
      "fas fa-check-circle me-2";
  } catch (error) {
    console.error("Error loading dashboard:", error);
    document.querySelector("#status i").className =
      "fas fa-exclamation-triangle me-2";
    document.getElementById("status").innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>Error loading data
                `;
  }
}

async function analyze() {
  const analyzeBtn = document.querySelector(".analyze-btn");
  const originalText = analyzeBtn.innerHTML;

  try {
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...`;

    await fetch("/iron-condor/analyze", { method: "POST" });
    await loadDashboard();

    analyzeBtn.innerHTML = `<i class="fas fa-check-circle me-2"></i>Analysis Complete`;
    setTimeout(() => {
      analyzeBtn.innerHTML = originalText;
      analyzeBtn.disabled = false;
    }, 2000);
  } catch (error) {
    console.error("Error analyzing:", error);
    analyzeBtn.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>Error`;
    setTimeout(() => {
      analyzeBtn.innerHTML = originalText;
      analyzeBtn.disabled = false;
    }, 2000);
  }
}

async function addPosition(trade) {
  try {
    await fetch("/iron-condor/position", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(trade),
    });
    await loadDashboard();
  } catch (error) {
    console.error("Error adding position:", error);
  }
}

async function closePosition(id) {
  try {
    await fetch(`/iron-condor/position/${id}/close`, { method: "POST" });
    await loadDashboard();
  } catch (error) {
    console.error("Error closing position:", error);
  }
}

// Initial load
loadDashboard();

// Auto-refresh
setInterval(loadDashboard, 15000);

// Add animation to refresh indicator
setInterval(() => {
  const icon = document.querySelector(".refresh-indicator i");
  icon.classList.add("fa-spin");
  setTimeout(() => icon.classList.remove("fa-spin"), 1000);
}, 15000);
// Format timestamp
function formatTime(timestamp) {
  const options = {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  };
  return new Date(timestamp).toLocaleTimeString("en-US", options);
}

// Get score class based on value
function getScoreClass(score) {
  if (score >= 80) return "score-high";
  if (score >= 50) return "score-medium";
  return "score-low";
}

// Get IV class based on value
function getIvClass(iv) {
  if (iv >= 30) return "iv-high";
  if (iv >= 20) return "iv-medium";
  return "iv-low";
}

// Format currency
function formatCurrency(value) {
  return "$" + parseFloat(value).toFixed(2);
}

// Format delta balance
function formatDeltaBalance(callDelta, putDelta) {
  const balance = Math.abs(callDelta - putDelta).toFixed(2);
  return `<span class="greek-value ${balance > 0.15 ? "delta-positive" : "delta-negative"
    }">${balance}</span>`;
}

async function loadDashboard() {
  try {
    const statusResponse = await fetch("/iron-condor/status");
    const status = await statusResponse.json();

    document.getElementById("status").innerHTML = `
                    <i class="fas fa-chart-line me-2"></i>SPX: <strong>${status.spx_price.toFixed(
      2
    )}</strong> 
                    | Last Analysis: <strong>${formatTime(
      status.last_analysis
    )}</strong>
                `;

    document.getElementById("refresh-time").innerHTML = `
                    <i class="fas fa-clock me-2"></i>Updated: <strong>${formatTime(
      Date.now()
    )}</strong>
                `;

    const dataResponse = await fetch("/iron-condor/analysis");
    const data = await dataResponse.json();

    console.log("==================Data loaded:", data);

    const tbody = document.querySelector("#opportunities tbody");
    tbody.innerHTML = data.scored_trades
      .map(
        (trade) => `
                    <tr>
                        <td class="score-cell ${getScoreClass(trade.score)}">
                            ${trade.score.toFixed(1)}
                        </td>
                        <td class="strikes-cell">
                            ${trade.short_put}/${trade.long_put} - ${trade.short_call
          }/${trade.long_call}
                        </td>
                        <td class="text-success fw-bold">
                            ${formatCurrency(trade.premium)}
                        </td>
                        <td class="text-danger fw-bold">
                            ${formatCurrency(trade.max_loss)}
                        </td>
                        <td>
                            ${formatDeltaBalance(
            trade.short_call_delta,
            trade.short_put_delta
          )}
                        </td>
                        <td class="iv-value ${getIvClass(
            (trade.call_iv + trade.put_iv) / 2
          )}">
                            ${((trade.call_iv + trade.put_iv) / 2).toFixed(1)}%
                        </td>
                        <td>
                            <button class="action-btn btn-success" onclick='addPosition(${JSON.stringify(
            trade
          )})'>
                                <i class="fas fa-plus-circle me-1"></i>Open
                            </button>
                        </td>
                    </tr>
                `
      )
      .join("");

    const positions = document.getElementById("positions");
    positions.innerHTML = data.current_positions
      .map(
        (position) => `
                    <li class="position-item">
                        <div>
                            <span class="position-strikes">${position.short_put
          }/${position.long_put} - ${position.short_call}/${position.long_call
          }</span>
                            <div class="position-time">Opened: ${formatTime(
            position.timestamp
          )}</div>
                        </div>
                        ${position.closed
            ? `
                            <span class="badge badge-closed rounded-pill">
                                <i class="fas fa-lock me-1"></i>Closed
                            </span>
                        `
            : `
                            <button class="action-btn btn-danger" onclick="closePosition('${position.id}')">
                                <i class="fas fa-times-circle me-1"></i>Close
                            </button>
                        `
          }
                    </li>
                `
      )
      .join("");

    // Update status indicator icon
    document.querySelector("#status i").className =
      "fas fa-check-circle me-2";
  } catch (error) {
    console.error("Error loading dashboard:", error);
    document.querySelector("#status i").className =
      "fas fa-exclamation-triangle me-2";
    document.getElementById("status").innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>Error loading data
                `;
  }
}

async function analyze() {
  const analyzeBtn = document.querySelector(".analyze-btn");
  const originalText = analyzeBtn.innerHTML;

  try {
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...`;

    await fetch("/iron-condor/analyze", { method: "POST" });
    await loadDashboard();

    analyzeBtn.innerHTML = `<i class="fas fa-check-circle me-2"></i>Analysis Complete`;
    setTimeout(() => {
      analyzeBtn.innerHTML = originalText;
      analyzeBtn.disabled = false;
    }, 2000);
  } catch (error) {
    console.error("Error analyzing:", error);
    analyzeBtn.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>Error`;
    setTimeout(() => {
      analyzeBtn.innerHTML = originalText;
      analyzeBtn.disabled = false;
    }, 2000);
  }
}

async function addPosition(trade) {
  try {
    await fetch("/iron-condor/position", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(trade),
    });
    await loadDashboard();
  } catch (error) {
    console.error("Error adding position:", error);
  }
}

async function closePosition(id) {
  try {
    await fetch(`/iron-condor/position/${id}/close`, { method: "POST" });
    await loadDashboard();
  } catch (error) {
    console.error("Error closing position:", error);
  }
}

// Initial load
loadDashboard();

// Auto-refresh
setInterval(loadDashboard, 15000);

// Add animation to refresh indicator
setInterval(() => {
  const icon = document.querySelector(".refresh-indicator i");
  icon.classList.add("fa-spin");
  setTimeout(() => icon.classList.remove("fa-spin"), 1000);
}, 15000);
// });