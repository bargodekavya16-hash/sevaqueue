document.addEventListener("DOMContentLoaded", function () {
  const palette = ["#9d8bff", "#4ad6b0", "#ffb86b", "#69a9ff", "#f17f9a"];
  const gridColor = "rgba(164, 176, 202, .10)";
  const tickColor = "#8e9ab1";
  function baseOptions() {
    return {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { backgroundColor: "#171c2d", titleColor: "#fff", bodyColor: "#d9dfef", padding: 12, cornerRadius: 10 } },
      scales: {
        x: { grid: { display: false }, ticks: { color: tickColor, font: { family: "DM Sans", size: 11 } , maxRotation: 0, autoSkip: true} },
        y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: tickColor, precision: 0, font: { family: "DM Sans", size: 11 } } }
      }
    };
  }
  if (window.Chart && window.sevaQueueCharts) {
    const d = window.sevaQueueCharts;
    const activity = document.getElementById("activityChart");
    if (activity) new Chart(activity, { type: "line", data: { labels: d.labels, datasets: [{ data: d.counts, borderColor: "#9d8bff", backgroundColor: "rgba(157,139,255,.12)", fill: true, tension: .38, borderWidth: 2.5, pointRadius: 3, pointHoverRadius: 5, pointBackgroundColor: "#9d8bff" }] }, options: baseOptions() });
    const service = document.getElementById("serviceChart");
    if (service) {
      new Chart(service, { type: "doughnut", data: { labels: d.serviceLabels, datasets: [{ data: d.serviceCounts, backgroundColor: palette, borderColor: "#171b2a", borderWidth: 4, hoverOffset: 5 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: "76%", plugins: { legend: { display: false }, tooltip: { backgroundColor: "#171c2d", padding: 12 } } } });
      const legend = document.getElementById("serviceLegend");
      if (legend) legend.innerHTML = d.serviceLabels.map((label, i) => `<div><span><i style="background:${palette[i % palette.length]}"></i>${escapeHtml(label)}</span><b>${d.serviceCounts[i]}</b></div>`).join("");
    }
  }
  if (window.Chart && window.sevaQueueReports) {
    const d = window.sevaQueueReports;
    const daily = document.getElementById("dailyChart");
    if (daily) new Chart(daily, { type: "bar", data: { labels: d.dailyLabels, datasets: [{ data: d.dailyCounts, backgroundColor: "rgba(157,139,255,.8)", hoverBackgroundColor: "#b0a3ff", borderRadius: 5, maxBarThickness: 22 }] }, options: baseOptions() });
    const svc = document.getElementById("reportServiceChart");
    if (svc) new Chart(svc, { type: "bar", data: { labels: d.serviceLabels, datasets: [{ data: d.serviceCounts, backgroundColor: palette, borderRadius: 5, maxBarThickness: 35 }] }, options: { ...baseOptions(), indexAxis: "y" } });
    const status = document.getElementById("statusChart");
    if (status) new Chart(status, { type: "doughnut", data: { labels: d.statusLabels, datasets: [{ data: d.statusCounts, backgroundColor: palette, borderColor: "#171b2a", borderWidth: 4 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: "66%", plugins: { legend: { position: "bottom", labels: { color: tickColor, padding: 15, usePointStyle: true, pointStyle: "circle" } } } } });
  }
  document.querySelectorAll("input[type=date]").forEach(el => { if (!el.min) el.min = new Date().toISOString().slice(0,10); });
});
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch])); }
