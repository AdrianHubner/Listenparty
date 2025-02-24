document.addEventListener("DOMContentLoaded", function () {
    // Checkbox-Handling
    const contextMenu = document.getElementById("context-menu");

    if (contextMenu) {
        // Zeige das Menü beim Rechtsklick
        document.querySelectorAll("li").forEach(function (task) {
            task.addEventListener("contextmenu", function (event) {
                console.log("Rechtsklick auf Task:", task.dataset.taskId); // Debug-Ausgabe
                event.preventDefault(); // Standard-Rechtsklick-Menü verhindern

                contextMenu.style.top = `${event.clientY}px`;
                contextMenu.style.left = `${event.clientX}px`;
                contextMenu.style.display = "block";

                contextMenu.dataset.taskId = task.dataset.taskId; // Task-ID speichern
            });
        });

        // Menü schließen, wenn woanders geklickt wird
        document.addEventListener("click", function () {
            contextMenu.style.display = "none";
        });
    } else {
        console.warn("⚠️ `context-menu` nicht gefunden. Wird auf dieser Seite nicht benötigt.");
    }


    document.querySelectorAll("input[type='checkbox']").forEach(function (checkbox) {
        checkbox.addEventListener("change", function () {
            const taskItem = this.closest("li"); // Suche das übergeordnete <li>-Element
            const taskId = taskItem.dataset.taskId; // Hole die Task-ID vom <li>

            console.log(`Checkbox clicked: Task ID=${taskId}, Completed=${this.checked}`); // Debug-Ausgabe

            // Dynamische Container basierend auf `list.name`
            const parentCard = this.closest(".card");
            const listName = parentCard.dataset.listName || parentCard.querySelector("h2").textContent.trim();
            //const listName = parentCard ? parentCard.querySelector("h2").textContent.trim() : null;
            const incompleteTasksContainer = document.querySelector(`#incomplete-tasks-${listName}`);
            const completedTasksContainer = document.querySelector(`#completed-tasks-${listName}`);

            fetch(`/toggle_task/${taskId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ completed: this.checked }),
            })
                .then((response) => {
                    if (response.ok) {
                        if (this.checked) {
                            completedTasksContainer.appendChild(taskItem);
                            taskItem.style.textDecoration = "line-through";
                            taskItem.style.color = "gray";
                        } else {
                            incompleteTasksContainer.appendChild(taskItem);
                            taskItem.style.textDecoration = "none";
                            taskItem.style.color = "black";
                        }
                    } else {
                        alert("Error: Could not update task status.");
                    }
                })
                .catch((error) => console.error("Error:", error));
        });
    });
        // Event-Listener für Vollbildmodus-Button
        document.querySelectorAll(".fullscreen-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                const listName = this.dataset.listName;
                const card = this.closest(".card");

                console.log(`Fullscreen für Liste: ${listName}`); // Debug-Ausgabe

                // Entferne vorherige Vollbildmodi
                document.querySelectorAll(".card").forEach(function (otherCard) {
                    otherCard.classList.remove("expanded");
                    otherCard.style.pointerEvents = "auto";
                });

                // Aktiviere Vollbildmodus
                card.classList.add("expanded");
            });
        });

        // Schließen des Vollbildmodus bei Klick außerhalb
        document.body.addEventListener("click", function (event) {
            if (!event.target.closest(".card.expanded") && !event.target.classList.contains("fullscreen-btn")) {
                console.log("Klick außerhalb, Vollbildmodus schließen.");
                document.querySelectorAll(".card").forEach(function (otherCard) {
                    otherCard.classList.remove("expanded");
                    otherCard.style.pointerEvents = "auto";
                });
            }
        });

       let draggedItem = null; // Das Element, das gezogen wird

        // Event-Listener für alle Aufgaben
        document.querySelectorAll("li").forEach(function (task) {
            // Wenn Drag gestartet wird
            task.addEventListener("dragstart", function (event) {
                draggedItem = this; // Speichere das gezogene Element
                console.log(`Dragging Task ID: ${this.dataset.taskId}`);
                event.dataTransfer.effectAllowed = "move";
            });

            // Wenn Drag endet
            task.addEventListener("dragend", function () {
                draggedItem = null;
            });

            // Wenn ein Element über ein anderes gezogen wird
            task.addEventListener("dragover", function (event) {
                event.preventDefault(); // Erlaubt das Droppen
            });



            // Wenn ein Element fallen gelassen wird
            task.addEventListener("drop", function (event) {
                event.preventDefault();
                this.style.border = "none"; // Visuellen Hinweis entfernen

                if (draggedItem !== this) {
                    const parent = this.parentNode;
                    const bounding = this.getBoundingClientRect();
                    const offset = event.clientY - bounding.top; // Position des Mauszeigers relativ zur Aufgabe

                    if (offset > bounding.height / 2) {
                        // Wenn der Mauszeiger in der unteren Hälfte ist, füge nach der aktuellen Aufgabe ein
                        parent.insertBefore(draggedItem, this.nextSibling);
                    } else {
                        // Wenn der Mauszeiger in der oberen Hälfte ist, füge vor der aktuellen Aufgabe ein
                        parent.insertBefore(draggedItem, this);
                    }

                    // Neue Reihenfolge ermitteln
                    const updatedOrder = Array.from(parent.children).map(item => item.dataset.taskId);
                    console.log("New Order:", updatedOrder);

                    // Neue Reihenfolge ans Backend senden
                    fetch(`/update_task_order`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ order: updatedOrder }),
                    }).then(response => {
                        if (response.ok) {
                            console.log("Order updated successfully!");
                        } else {
                            console.error("Failed to update order.");
                        }
                    });
                }
            });

        });



    // Menü schließen, wenn man woanders klickt
    document.addEventListener("click", function () {
        console.log("Kontextmenü geschlossen."); // Debug-Ausgabe
        contextMenu.style.display = "none";
    });

    // Menü schließen, wenn man woanders klickt
    document.addEventListener("click", function () {
        contextMenu.style.display = "none";
    });


});
