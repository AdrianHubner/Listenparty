document.addEventListener("DOMContentLoaded", function() {
  // Hole die Habit-Daten vom Server (über den API-Endpunkt)
  fetch("/habits/api/habits")
    .then(response => response.json())
    .then(data => {
      // Render die Kalender für jeden Habit
      renderHabitCalendar(data, "alcohol", "calendar-grid-alcohol", "#ff9999");  // Alkohol: Rotton
      renderHabitCalendar(data, "smoke", "calendar-grid-smoke", "#cccccc");        // Rauchen: Grauton
      renderHabitCalendar(data, "sport", "calendar-grid-sport", "#99ff99");          // Sport: Grünton
    })
    .catch(error => console.error("Fehler beim Laden der Habit-Daten:", error));

  function renderHabitCalendar(habitData, habitKey, containerId, color) {
    const container = document.getElementById(containerId);
    container.innerHTML = ""; // Clear container

    // Render einen Kalender für den aktuellen Monat
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth(); // 0-basiert
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    // Erstelle eine Tabelle für den Kalender
    let html = "<table class='calendar-table'><tr>";
    // Wochentage
    const weekdays = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
    weekdays.forEach(day => {
      html += `<th>${day}</th>`;
    });
    html += "</tr><tr>";
    // Füge leere Zellen hinzu, falls der Monat nicht am Sonntag beginnt
    const startingDay = firstDay.getDay();
    for(let i = 0; i < startingDay; i++){
      html += "<td></td>";
    }
    // Fülle den Kalender mit Tagen
    for(let d = 1; d <= lastDay.getDate(); d++){
      const currentDate = new Date(year, month, d);
      const dateStr = currentDate.toISOString().split("T")[0]; // Format YYYY-MM-DD
      // Finde den Eintrag für diesen Tag
      const entry = habitData.find(item => item.habit_date === dateStr);
      let cellClass = "";
      if (entry && entry[habitKey] == 1) {
        cellClass = habitKey + "-yes"; // z.B. "alcohol-yes"
      }
      html += `<td class="${cellClass}">${d}</td>`;
      // Neue Zeile am Ende der Woche
      if (currentDate.getDay() === 6 && d !== lastDay.getDate()){
        html += "</tr><tr>";
      }
    }
    html += "</tr></table>";
    container.innerHTML = html;
  }
});
