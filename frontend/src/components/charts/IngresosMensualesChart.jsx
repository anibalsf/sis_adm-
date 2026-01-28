import React, { useEffect, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import PropTypes from 'prop-types';

Chart.register(...registerables);

const IngresosMensualesChart = ({ data }) => {
    const chartRef = useRef(null);
    const chartInstance = useRef(null);

    useEffect(() => {
        if (!chartRef.current || !data) return;

        // Destruir gráfico anterior si existe
        if (chartInstance.current) {
            chartInstance.current.destroy();
        }

        const ctx = chartRef.current.getContext('2d');

        chartInstance.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                datasets: [
                    {
                        label: 'Ingresos 2026',
                        data: data.currentYear || [0, 0, 0, 0, 0, 0],
                        borderColor: '#4a9d9c',
                        backgroundColor: 'rgba(74, 157, 156, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#4a9d9c',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                    },
                    {
                        label: 'Ingresos 2025',
                        data: data.previousYear || [0, 0, 0, 0, 0, 0],
                        borderColor: '#cbd5e1',
                        backgroundColor: 'rgba(203, 213, 225, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#cbd5e1',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        borderDash: [5, 5],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12,
                                weight: '600',
                            },
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold',
                        },
                        bodyFont: {
                            size: 13,
                        },
                        callbacks: {
                            label: function (context) {
                                return `${context.dataset.label}: ${context.parsed.y.toLocaleString('es-BO')} Bs`;
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString('es-BO') + ' Bs';
                            },
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                        },
                    },
                    x: {
                        grid: {
                            display: false,
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

IngresosMensualesChart.propTypes = {
    data: PropTypes.shape({
        labels: PropTypes.arrayOf(PropTypes.string),
        currentYear: PropTypes.arrayOf(PropTypes.number),
        previousYear: PropTypes.arrayOf(PropTypes.number),
    }),
};

export default IngresosMensualesChart;
