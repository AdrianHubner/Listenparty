document.addEventListener("DOMContentLoaded", function () {

    const calendarGrid = document.querySelector(".calendar-grid");

    const currentMonth = document.getElementById("current-month");
    const prevMonthButton = document.getElementById("prev-month");
    const nextMonthButton = document.getElementById("next-month");

    let date = new Date(initialYear, initialMonth - 1);


    // Navigiere zur gleichen Route, aber mit Query-Parametern für Jahr und Monat

    prevMonthButton.addEventListener("click", function () {
        date.setMonth(date.getMonth() - 1);
        window.location.href = `/calendar?year=${date.getFullYear()}&month=${date.getMonth() + 1}`;
    });

    nextMonthButton.addEventListener("click", function () {
        date.setMonth(date.getMonth() + 1);
        window.location.href = `/calendar?year=${date.getFullYear()}&month=${date.getMonth() + 1}`;
    });


    // Optional: Aktualisiere den Header (falls nötig) – oder das übernimmt dein Server.
    currentMonth.textContent = new Intl.DateTimeFormat('en-US', {
        month: 'long',
        year: 'numeric'
    }).format(date);





    function handleDrop(event) {
        event.preventDefault();
        const taskId = event.dataTransfer.getData("text");
        const targetDate = event.target.dataset.date;

        fetch(`/update_task_date/${taskId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ due_date: targetDate }),
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                console.error("Failed to update task date.");
            }
        });
    }


    let draggedTask = null;

    // Draggable tasks
    document.querySelectorAll(".day-task").forEach(task => {
        task.addEventListener("dragstart", function (event) {
            draggedTask = this;
            console.log(`Task dragged: ${this.dataset.taskId}`);
        });
    });

    document.getElementById("show-recurring-tasks").addEventListener("change", function () {
        const includeRecurring = this.checked; // Prüfe, ob das Kontrollkästchen aktiviert ist
        fetch(`/calendar?include_recurring=${includeRecurring ? '1' : '0'}`)
            .then(response => response.json())
            .then(data => {
                // Aktualisiere den Kalender mit den neuen Aufgaben (inkl. wiederkehrender Aufgaben)
                updateCalendar(data.tasks);
            });
    });

    // Drop targets (days in the calendar)
    document.querySelectorAll(".day").forEach(day => {
        day.addEventListener("dragover", function (event) {
            event.preventDefault(); // Allow drop
        });

        day.addEventListener("drop", function (event) {
            event.preventDefault();
            if (draggedTask) {
                const newDate = this.dataset.date;
                const taskId = draggedTask.dataset.taskId;

                console.log(`Task dropped on ${newDate}`);

                // Update task visually
                this.querySelector(".task-container").appendChild(draggedTask);

                // Update task date in the backend
                fetch(`/update_task_date/${taskId}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ newDate }),
                })
                    .then(response => {
                        if (response.ok) {
                            console.log(`Task ${taskId} updated to ${newDate}`);
                        } else {
                            console.error("Failed to update task date.");
                        }
                    })
                    .catch(error => console.error("Error:", error));
            }
        });
    });
});
