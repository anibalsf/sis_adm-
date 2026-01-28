import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import PropTypes from 'prop-types';

Chart.register(...registerables);

const DistribucionPagosChart = ({ data }) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        if (!chartRef.current || !data) return;

        if (chartInstance.current) {
            chartInstance.current.destroy();
        }

        const ctx = chartRef.current.getContext('2d');

        chartInstance.current = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || ['Cuotas', 'Sanciones', 'Hojas de Ruta'],
                datasets: [
                    {
                        data: data.values || [0, 0, 0],
                        backgroundColor: [
                            '#4a9d9c',
                            '#edb44d',
                            '#3b82f6',
                        ],
                        borderColor: '#fff',
                        borderWidth: 3,
                        hoverOffset: 10,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12,
                                weight: '600',
                            },
                            usePointStyle: true,
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value.toLocaleString('es-BO')} Bs (${percentage}%)`;
                            },
                        },
                    },
                },
            },
        });

        return () => {
            if (chartInstance.current) {
                chartInstance.current.destroy();
            }
        };
    }, [data]);

    return (
        <div style={{ position: 'relative', height: '300px' }}>
            <canvas ref={chartRef}></canvas>
        </div>
    );
};

DistribucionPagosChart.propTypes = {
    data: PropTypes.shape({
        labels: PropTypes.arrayOf(PropTypes.string),
        values: PropTypes.arrayOf(PropTypes.number),
    }),
};

export default DistribucionPagosChart;
