document.addEventListener('DOMContentLoaded', function() {
    const putChartCtx = document.getElementById('put-spread-chart').getContext('2d');
    let putChart;
    
    function initChart(data) {
        putChart = new Chart(putChartCtx, {
            type: 'bar',
            data: {
                labels: data.put_spreads.map(s => `${s.short_strike}/${s.long_strike}`),
                datasets: [
                    {
                        label: 'Credit Received',
                        data: data.put_spreads.map(s => s.credit),
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Risk/Reward Ratio',
                        data: data.put_spreads.map(s => s.risk_reward),
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        type: 'line',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Put Spread Analysis'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.datasetIndex === 0) {
                                    label += '$' + context.raw.toFixed(2);
                                } else {
                                    label += context.raw.toFixed(2) + ':1';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Credit ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Risk/Reward'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    function refreshData() {
        fetch('/spread/data')
            .then(response => response.json())
            .then(data => {
                if (data.put_spreads && data.put_spreads.length > 0) {
                    if (putChart) {
                        updateChart(data);
                    } else {
                        initChart(data);
                    }
                    
                    // Update last updated time
                    document.querySelector('.last-updated').textContent = 
                        `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
                    
                    if (data.spot_price) {
                        document.querySelector('.spot-price').textContent = 
                            `Current SPX: ${data.spot_price.toFixed(2)}`;
                    }
                }
            })
            .catch(error => {
                console.error('Error refreshing data:', error);
            });
    }
    
    function updateChart(data) {
        putChart.data.labels = data.put_spreads.map(s => `${s.short_strike}/${s.long_strike}`);
        putChart.data.datasets[0].data = data.put_spreads.map(s => s.credit);
        putChart.data.datasets[1].data = data.put_spreads.map(s => s.risk_reward);
        putChart.update();
    }
    
    // Event listeners
    document.getElementById('refresh-btn').addEventListener('click', refreshData);
    
    // Initial load
    refreshData();
    
    // Auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});