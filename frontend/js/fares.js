/**
 * Fare Information & Calculator JavaScript
 */

document.addEventListener("DOMContentLoaded", async () => {
  await loadStopsForFareCalc();
  await loadFareMatrix();
  setupFareCalculator();
});

async function loadStopsForFareCalc() {
  try {
    const stops = await apiRequest("/api/stops");
    const fromSelect = document.getElementById("fare_from_stop");
    const toSelect = document.getElementById("fare_to_stop");

    if (fromSelect && toSelect) {
      stops.forEach(s => {
        const opt1 = document.createElement("option");
        opt1.value = s.id;
        opt1.textContent = `${s.stop_name} (${s.stop_code})`;
        fromSelect.appendChild(opt1);

        const opt2 = document.createElement("option");
        opt2.value = s.id;
        opt2.textContent = `${s.stop_name} (${s.stop_code})`;
        toSelect.appendChild(opt2);
      });

      // Select default stops if available
      if (stops.length >= 4) {
        fromSelect.selectedIndex = 1;
        toSelect.selectedIndex = 4;
      }
    }
  } catch (err) {
    console.error("Failed to load stops for calculator:", err);
  }
}

async function loadFareMatrix() {
  showLoading();
  try {
    const fares = await apiRequest("/api/fares");
    const tbody = document.getElementById("fares-table-body");
    if (tbody) {
      if (!fares || fares.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No fare tariffs found.</td></tr>`;
      } else {
        tbody.innerHTML = fares.map(f => `
          <tr>
            <td><span class="badge bg-dark fs-6">${f.route_number}</span></td>
            <td class="fw-bold">${f.route_name}</td>
            <td>${f.distance || 10} km</td>
            <td class="fw-bold text-primary">₹${f.base_fare}</td>
            <td class="text-success">₹${f.student_fare} <small class="badge bg-success-subtle text-success">50% Off</small></td>
            <td class="text-info">₹${f.senior_fare} <small class="badge bg-info-subtle text-info">Concession</small></td>
            <td><span class="badge bg-light text-dark border">Eff. ${f.effective_date}</span></td>
          </tr>
        `).join("");
      }
    }
  } catch (err) {
    showToast("Failed to load fare tariffs: " + err.message, "error");
  } finally {
    hideLoading();
  }
}

function setupFareCalculator() {
  const form = document.getElementById("fare-calculator-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fromId = parseInt(document.getElementById("fare_from_stop").value);
    const toId = parseInt(document.getElementById("fare_to_stop").value);
    const passType = document.getElementById("fare_passenger_type").value;

    if (!fromId || !toId) {
      showToast("Please choose both starting and destination stops.", "warning");
      return;
    }

    if (fromId === toId) {
      showToast("Starting stop and destination cannot be the same.", "warning");
      return;
    }

    showLoading();
    try {
      const calcResult = await apiRequest("/api/fares/calculate", {
        method: "POST",
        body: JSON.stringify({
          from_stop_id: fromId,
          to_stop_id: toId,
          passenger_type: passType
        })
      });

      const resCard = document.getElementById("fare-calc-result-card");
      if (resCard) {
        resCard.classList.remove("d-none");
        document.getElementById("calc-est-fare").textContent = `₹${calcResult.estimated_fare}`;
        document.getElementById("calc-route-name").textContent = `${calcResult.route_number} - ${calcResult.route_name}`;
        document.getElementById("calc-path").textContent = `${calcResult.from_stop} → ${calcResult.to_stop}`;
        document.getElementById("calc-details").textContent = `Stops: ${calcResult.stops_count} | Est. Distance: ${calcResult.distance_km} km | Category: ${calcResult.passenger_type}`;
        document.getElementById("calc-pass-info").textContent = calcResult.pass_info;
      }
      showToast("Fare calculated successfully!", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      hideLoading();
    }
  });
}
