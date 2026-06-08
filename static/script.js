/**
 * Smart City Parking Dashboard - JavaScript
 * 
 * Fetches data from FastAPI endpoints and renders:
 *   - Summary cards (total, occupied, available, violations)
 *   - Lot status bars
 *   - Chart.js charts (daily entries, peak hours, lot comparison)
 *   - Key metrics
 *   - Recent events table
 */

// ─── Chart instances (for updating without duplicates) ──────────
let dailyChart = null;
let hourlyChart = null;
let lotChart = null;
let currentEventPage = 1;
let eventPageSize = 10;

// ─── Chart.js global config (dark theme) ────────────────────────
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";

// ─── Load all data on page load ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadSummary();
    loadAnalytics();
    loadEvents();
    updateTimestamp();
});

// ─── Update timestamp ───────────────────────────────────────────
function updateTimestamp() {
    const now = new Date().toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short'
    });
    document.getElementById('last-updated').textContent = `Last updated: ${now}`;
}

// ─── Endpoint 1: Load Summary ───────────────────────────────────
async function loadSummary() {
    try {
        const response = await fetch('/api/dashboard/summary');
        const data = await response.json();

        // Update summary cards
        animateValue('total-spaces', data.total_spaces);
        animateValue('occupied-spaces', data.occupied);
        animateValue('available-spaces', data.available);

        // Render lot cards
        renderLots(data.lots);
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

// ─── Endpoint 2: Load Analytics ─────────────────────────────────
async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics/weekly');
        const data = await response.json();

        // Update overstay card
        animateValue('overstay-count', data.overstay_count);

        // Update key metrics
        document.getElementById('stat-total-events').textContent = data.total_events;
        document.getElementById('stat-avg-duration').textContent = data.avg_duration_hours + ' hrs';
        document.getElementById('stat-overstays').textContent = data.overstay_count;

        // Find busiest lot
        if (data.lot_comparison && data.lot_comparison.length > 0) {
            const busiest = data.lot_comparison.reduce((a, b) =>
                a.total_entries > b.total_entries ? a : b
            );
            document.getElementById('stat-busiest-lot').textContent = busiest.lot_name;
        }

        // Render charts
        renderDailyChart(data.daily_entries);
        renderHourlyChart(data.peak_hours);
        renderLotChart(data.lot_comparison);
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

// ─── Endpoint 3: Load Events ────────────────────────────────────
async function loadEvents(page = 1) {
    try {
        const response = await fetch(`/api/events?page=${page}&per_page=${eventPageSize}`);
        const data = await response.json();

        const tbody = document.getElementById('events-body');
        tbody.innerHTML = '';

        data.items.forEach(event => {
            const isOverstay = event.duration_hours && event.duration_hours > event.allowed_duration_hours;
            const isParked = !event.exit_time;

            const entryDate = new Date(event.entry_time);
            const entryStr = entryDate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) + 
                             ' (' + entryDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) + ')';
            
            let exitStr = '—';
            if (event.exit_time) {
                const exitDate = new Date(event.exit_time);
                exitStr = exitDate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) + 
                          ' (' + exitDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) + ')';
            } else {
                exitStr = 'Still Parked';
            }

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${event.vehicle_number}</td>
                <td>${event.lot_name}</td>
                <td>${event.space_number}</td>
                <td>${entryStr}</td>
                <td class="${isParked ? 'status-parked' : ''}">${exitStr}</td>
                <td class="${isOverstay ? 'overstay' : ''}">${
                    event.duration_hours ? event.duration_hours.toFixed(1) + ' hrs' + (isOverstay ? ' ⚠️' : '') : '—'
                }</td>
            `;
            tbody.appendChild(row);
        });

        // Add pagination info and controls
        addPaginationControls(data, page);
        currentEventPage = page;
    } catch (error) {
        console.error('Error loading events:', error);
    }
}

// ─── Add pagination controls ────────────────────────────────────
function addPaginationControls(data, currentPage) {
    const paginationDiv = document.getElementById('events-pagination');
    
    // Create pagination if it doesn't exist
    if (!paginationDiv) {
        const tableContainer = document.querySelector('.table-container');
        const newPaginationDiv = document.createElement('div');
        newPaginationDiv.id = 'events-pagination';
        newPaginationDiv.style.marginTop = '1rem';
        tableContainer.appendChild(newPaginationDiv);
    }

    const paginationDiv2 = document.getElementById('events-pagination');
    paginationDiv2.innerHTML = '';

    // Pagination info
    const info = document.createElement('div');
    info.style.textAlign = 'center';
    info.style.color = '#94a3b8';
    info.style.marginBottom = '1rem';
    info.style.fontSize = '0.9rem';
    const start = (currentPage - 1) * eventPageSize + 1;
    const end = Math.min(currentPage * eventPageSize, data.total);
    info.textContent = `Showing ${start}-${end} of ${data.total} events`;
    paginationDiv2.appendChild(info);

    // Pagination buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'center';
    buttonContainer.style.gap = '0.5rem';
    buttonContainer.style.flexWrap = 'wrap';

    // Previous button
    if (currentPage > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '← Previous';
        prevBtn.style.padding = '0.5rem 1rem';
        prevBtn.style.borderRadius = '6px';
        prevBtn.style.border = '1px solid rgba(148, 163, 184, 0.2)';
        prevBtn.style.background = 'rgba(30, 41, 59, 0.5)';
        prevBtn.style.color = '#e2e8f0';
        prevBtn.style.cursor = 'pointer';
        prevBtn.style.fontSize = '0.9rem';
        prevBtn.onclick = () => loadEvents(currentPage - 1);
        buttonContainer.appendChild(prevBtn);
    }

    // Page numbers
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(data.total_pages, startPage + maxButtons - 1);

    if (endPage - startPage + 1 < maxButtons) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    // First page
    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.textContent = '1';
        firstBtn.style.padding = '0.5rem 0.75rem';
        firstBtn.style.borderRadius = '6px';
        firstBtn.style.border = '1px solid rgba(148, 163, 184, 0.2)';
        firstBtn.style.background = 'rgba(30, 41, 59, 0.5)';
        firstBtn.style.color = '#e2e8f0';
        firstBtn.style.cursor = 'pointer';
        firstBtn.style.fontSize = '0.9rem';
        firstBtn.onclick = () => loadEvents(1);
        buttonContainer.appendChild(firstBtn);

        if (startPage > 2) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.style.padding = '0.5rem';
            dots.style.color = '#94a3b8';
            buttonContainer.appendChild(dots);
        }
    }

    // Page number buttons
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        pageBtn.style.padding = '0.5rem 0.75rem';
        pageBtn.style.borderRadius = '6px';
        pageBtn.style.border = '1px solid rgba(148, 163, 184, 0.2)';
        pageBtn.style.color = '#e2e8f0';
        pageBtn.style.cursor = 'pointer';
        pageBtn.style.fontSize = '0.9rem';

        if (i === currentPage) {
            pageBtn.style.background = '#3b82f6';
            pageBtn.style.borderColor = '#3b82f6';
            pageBtn.style.fontWeight = '600';
            pageBtn.disabled = true;
        } else {
            pageBtn.style.background = 'rgba(30, 41, 59, 0.5)';
            pageBtn.onclick = () => loadEvents(i);
        }
        buttonContainer.appendChild(pageBtn);
    }

    // Last page
    if (endPage < data.total_pages) {
        if (endPage < data.total_pages - 1) {
            const dots = document.createElement('span');
            dots.textContent = '...';
            dots.style.padding = '0.5rem';
            dots.style.color = '#94a3b8';
            buttonContainer.appendChild(dots);
        }

        const lastBtn = document.createElement('button');
        lastBtn.textContent = data.total_pages;
        lastBtn.style.padding = '0.5rem 0.75rem';
        lastBtn.style.borderRadius = '6px';
        lastBtn.style.border = '1px solid rgba(148, 163, 184, 0.2)';
        lastBtn.style.background = 'rgba(30, 41, 59, 0.5)';
        lastBtn.style.color = '#e2e8f0';
        lastBtn.style.cursor = 'pointer';
        lastBtn.style.fontSize = '0.9rem';
        lastBtn.onclick = () => loadEvents(data.total_pages);
        buttonContainer.appendChild(lastBtn);
    }

    // Next button
    if (currentPage < data.total_pages) {
        const nextBtn = document.createElement('button');
        nextBtn.textContent = 'Next →';
        nextBtn.style.padding = '0.5rem 1rem';
        nextBtn.style.borderRadius = '6px';
        nextBtn.style.border = '1px solid rgba(148, 163, 184, 0.2)';
        nextBtn.style.background = 'rgba(30, 41, 59, 0.5)';
        nextBtn.style.color = '#e2e8f0';
        nextBtn.style.cursor = 'pointer';
        nextBtn.style.fontSize = '0.9rem';
        nextBtn.onclick = () => loadEvents(currentPage + 1);
        buttonContainer.appendChild(nextBtn);
    }

    paginationDiv2.appendChild(buttonContainer);
}

// ─── Render Lot Cards ───────────────────────────────────────────
function renderLots(lots) {
    const grid = document.getElementById('lots-grid');
    grid.innerHTML = '';

    lots.forEach(lot => {
        const occupancyPct = Math.round((lot.occupied / lot.total) * 100);
        let badgeClass, badgeText, barColor;

        if (occupancyPct < 50) {
            badgeClass = 'good';
            badgeText = 'Available';
            barColor = '#10b981';
        } else if (occupancyPct < 80) {
            badgeClass = 'moderate';
            badgeText = 'Filling Up';
            barColor = '#f59e0b';
        } else {
            badgeClass = 'full';
            badgeText = 'Almost Full';
            barColor = '#ef4444';
        }

        const card = document.createElement('div');
        card.className = 'lot-card';
        card.innerHTML = `
            <div class="lot-header">
                <div>
                    <div class="lot-name">${lot.name}</div>
                    <div class="lot-location">${lot.location}</div>
                </div>
                <span class="lot-badge ${badgeClass}">${badgeText}</span>
            </div>
            <div class="lot-bar-container">
                <div class="lot-bar" style="width: ${occupancyPct}%; background: ${barColor};"></div>
            </div>
            <div class="lot-stats">
                <span>Occupied: <strong>${lot.occupied}</strong></span>
                <span>Available: <strong>${lot.available}</strong></span>
                <span>Total: <strong>${lot.total}</strong></span>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ─── Chart: Daily Entries (Bar) ─────────────────────────────────
function renderDailyChart(dailyEntries) {
    const ctx = document.getElementById('daily-chart').getContext('2d');

    if (dailyChart) dailyChart.destroy();

    const labels = dailyEntries.map(d => {
        const date = new Date(d.date);
        return date.toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' });
    });
    const values = dailyEntries.map(d => d.entries);

    dailyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Parking Entries',
                data: values,
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: '#3b82f6',
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.04)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// ─── Chart: Peak Hours (Line) ───────────────────────────────────
function renderHourlyChart(peakHours) {
    const ctx = document.getElementById('hourly-chart').getContext('2d');

    if (hourlyChart) hourlyChart.destroy();

    // Fill all 24 hours
    const hourData = new Array(24).fill(0);
    peakHours.forEach(h => { hourData[h.hour] = h.entries; });

    const labels = Array.from({ length: 24 }, (_, i) => {
        const ampm = i < 12 ? 'AM' : 'PM';
        const hour = i === 0 ? 12 : i > 12 ? i - 12 : i;
        return `${hour}${ampm}`;
    });

    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Entries',
                data: hourData,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#8b5cf6',
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.04)' }
                },
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 12 }
                }
            }
        }
    });
}

// ─── Chart: Lot Comparison (Doughnut) ───────────────────────────
function renderLotChart(lotComparison) {
    const ctx = document.getElementById('lot-chart').getContext('2d');

    if (lotChart) lotChart.destroy();

    const labels = lotComparison.map(l => l.lot_name);
    const values = lotComparison.map(l => l.total_entries);
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

    lotChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: '#0a0e1a',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// ─── Animate number counting up ─────────────────────────────────
function animateValue(elementId, endValue) {
    const element = document.getElementById(elementId);
    const duration = 800;
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out quad
        const eased = 1 - (1 - progress) * (1 - progress);
        const current = Math.round(start + (endValue - start) * eased);

        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}
