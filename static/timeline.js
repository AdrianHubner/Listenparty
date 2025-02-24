document.addEventListener("DOMContentLoaded", function () {
  // Modal-Elemente
  const modal = document.getElementById("milestone-modal");
  const modalClose = document.getElementById("modal-close");
  const modalTitle = document.getElementById("modal-title");
  const modalDetail = document.getElementById("modal-detail");

  // Modal schließen
  modalClose.addEventListener("click", function () {
    modal.style.display = "none";
  });
  window.addEventListener("click", function (e) {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });

  // Hole die Timeline-Daten vom Server
  fetch("/timeline/api/timeline_data")
    .then(response => response.json())
    .then(data => {
      renderTimeline(data);
    })
    .catch(error => console.error("Fehler beim Laden der Timeline-Daten:", error));

  function showMilestoneDetail(title, milestoneId) {
    modalTitle.textContent = title;
    // Rufe den API-Endpunkt auf, um die Milestone-Aufgaben zu holen:
    fetch(`/timeline/api/milestone_tasks/${milestoneId}`)
      .then(response => response.json())
      .then(tasks => {
        let tasksHtml = "";
        if (tasks.length === 0) {
          tasksHtml = "<p>Keine Aufgaben für diesen Milestone.</p>";
        } else {
          tasksHtml = "<ul>";
          tasks.forEach(task => {
            tasksHtml += `<li>${task.title} ${task.completed ? "(Erledigt)" : ""}</li>`;
          });
          tasksHtml += "</ul>";
        }
        modalDetail.innerHTML = tasksHtml;
        modal.style.display = "block";
      })
      .catch(error => {
        console.error("Fehler beim Laden der Milestone-Aufgaben:", error);
        modalDetail.innerHTML = "<p>Fehler beim Laden der Aufgaben.</p>";
        modal.style.display = "block";
      });
  }

  function computeGlobalTimeRange(goals) {
    let earliest = Infinity;
    let latest = -Infinity;
    goals.forEach(goal => {
      const start = new Date(goal.start_date).getTime();
      const end = new Date(goal.due_date).getTime();
      if (start < earliest) earliest = start;
      if (end > latest) latest = end;
    });
    return { earliest, latest };
  }

  function renderXAxis(earliest, latest) {
    const xAxis = document.createElement("div");
    xAxis.className = "x-axis";
    let current = new Date(earliest);
    const endDate = new Date(latest);
    while (current <= endDate) {
      const marker = document.createElement("div");
      marker.className = "marker";
      const markerTime = current.getTime();
      const leftPercent = ((markerTime - earliest) / (latest - earliest)) * 100;
      marker.style.left = leftPercent + "%";
      const label = document.createElement("span");
      label.textContent = current.toLocaleString('de-DE', { month: 'short', year: 'numeric' });
      marker.appendChild(label);
      xAxis.appendChild(marker);
      current.setMonth(current.getMonth() + 1);
    }
    return xAxis;
  }

  function renderTimeline(goals) {
    const diagram = document.getElementById("timeline-diagram");
    diagram.innerHTML = "";

    // Verwende einen fixen Zeitbereich: heute bis heute + 1 Jahr
    const today = new Date();
    const oneYearLater = new Date();
    oneYearLater.setFullYear(oneYearLater.getFullYear() + 1);
    const earliest = today.getTime();
    const latest = oneYearLater.getTime();
    const totalSpan = latest - earliest;

    // Füge die X-Achse hinzu
    const xAxis = renderXAxis(earliest, latest);
    diagram.appendChild(xAxis);

    // Vertikaler Platzbedarf
    const goalHeight = 60;
    const topOffset = 50;

    goals.forEach((goal, index) => {
      const goalStart = new Date(goal.start_date).getTime();
      const goalEnd = new Date(goal.due_date).getTime();
      const leftPercent = ((goalStart - earliest) / totalSpan) * 100;
      const widthPercent = ((goalEnd - goalStart) / totalSpan) * 100;
      const lineTop = topOffset + index * goalHeight;

      // Erstelle die Zielzeile
      const goalLine = document.createElement("div");
      goalLine.className = "goal-line";
      goalLine.style.top = lineTop + "px";
      goalLine.style.left = leftPercent + "%";
      goalLine.style.width = widthPercent + "%";
      goalLine.style.backgroundColor = goal.color || "#007bff";
      // Beim Klick auf die Zielzeile das Goal-Detail-Modal anzeigen (wenn gewünscht)
      goalLine.addEventListener("click", function () {
        // Hier kannst du eine Funktion implementieren, die Goal-Details anzeigt
        console.log("Goal clicked:", goal.title);
      });
      diagram.appendChild(goalLine);

      // Ziel-Label
      const goalLabel = document.createElement("div");
      goalLabel.className = "goal-label";
      goalLabel.style.top = (lineTop - 20) + "px";
      goalLabel.style.left = leftPercent + "%";
      goalLabel.textContent = goal.title;
      diagram.appendChild(goalLabel);

      // Milestone-Punkte positionieren
      goal.milestones.forEach(milestone => {
        const msDate = new Date(milestone.due_date).getTime();
        const msLeftPercent = ((msDate - earliest) / totalSpan) * 100;
        const point = document.createElement("div");
        point.className = "milestone-point";
        point.style.top = lineTop + "px";
        point.style.left = msLeftPercent + "%";
        point.setAttribute("data-milestone-id", milestone.id);
        point.setAttribute("data-title", milestone.title);
        // Wir laden die Aufgaben per Fetch, also kein data-detail setzen
        point.addEventListener("click", function (event) {
          event.stopPropagation();
          const milestoneId = this.getAttribute("data-milestone-id");
          const title = this.getAttribute("data-title") || "Milestone";
          showMilestoneDetail(title, milestoneId);
        });
        diagram.appendChild(point);
      });
    });
  }
});
