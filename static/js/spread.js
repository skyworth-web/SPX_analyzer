document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('spread-chart').getContext('2d');
    let chart;
    let currentData = JSON.parse('{{ results | tojson | safe }}');
    
    // Initialize chart
    function initChart() {
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: currentData.put_spreads.map(s => s.strike),
                datasets: [{
                    label: 'Credit Received',
                    data: currentData.put_spreads.map(s => s.credit),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Put Spread Credits by Strike'
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Credit ($)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Strike Price'
                        }
                    }
                }
            }
        });
    }
    
    // Refresh data from server
    async function refreshData() {
        try {
            const response = await fetch('/spread/data');
            currentData = await response.json();
            
            if (chart) {
                updateChart();
            } else {
                initChart();
            }
            
            // Update last updated time
            document.querySelector('.last-updated').textContent = 
                `Last updated: ${new Date(currentData.timestamp).toLocaleString()}`;
                
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }
    
    // Update existing chart with new data
    function updateChart() {
        chart.data.labels = currentData.put_spreads.map(s => s.strike);
        chart.data.datasets[0].data = currentData.put_spreads.map(s => s.credit);
        chart.update();
    }
    
    // Event listeners
    document.getElementById('refresh-btn').addEventListener('click', refreshData);
    
    // Initial setup
    initChart();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});