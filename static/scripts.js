document.addEventListener("DOMContentLoaded", function () {
    const contextMenu = document.getElementById("context-menu");
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    let draggedItem = null; // Das Element, das gerade gezogen wird

    // =======================
    // Kontextmenü
    // =======================
    document.body.addEventListener("contextmenu", function (event) {
        const task = event.target.closest("li[data-task-id]");
        if (!task) return;

        event.preventDefault();
        if (contextMenu) {
            contextMenu.style.top = `${event.pageY}px`;
            contextMenu.style.left = `${event.pageX}px`;

            contextMenu.style.display = "block";
            contextMenu.dataset.taskId = task.dataset.taskId;
        }
    });

   // Kontextmenü Aktionen

    let popup = null; // global scope

    contextMenu.addEventListener("click", function(event) {
        const action = event.target.dataset.action;
        const taskId = contextMenu.dataset.taskId;
        if (!action || !taskId) return;

           // ✅ Menü sofort schließen
        contextMenu.style.display = "none";


        //const csrfToken = document.querySelector('input[name="csrf_token"]').value;

        if (action === "delete") {
            fetch(`/delete_task/${taskId}`, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken }
            })
            .then(res => {
                if (res.ok) {
                    const taskItem = document.querySelector(`li[data-task-id='${taskId}']`);
                    if (taskItem) taskItem.remove();
                } else alert("Could not delete task.");
            });

        } else if (action === "rename") {
            const newName = prompt("Enter new task name:");
            if (!newName) return;

            fetch(`/rename_task/${taskId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify({ newName })
            }).then(res => {
                if (res.ok) {
                    const taskItem = document.querySelector(`li[data-task-id='${taskId}']`);
                    if (taskItem) taskItem.querySelector("strong").textContent = newName;
                } else alert("Could not rename task.");
            });

        } else if (action === "move") {
            // 1️⃣ Listen sammeln
            const listElements = document.querySelectorAll(".card[data-list-name]");
            const lists = Array.from(listElements).map(card => card.dataset.listName);

            // 2️⃣ Popup erstellen
            if (popup) popup.remove(); // vorheriges Popup entfernen
            popup = document.createElement("div");
            popup.style.position = "absolute";
            popup.style.top = `${event.clientY}px`;
            popup.style.left = `${event.clientX}px`;
            popup.style.backgroundColor = "#fff";
            popup.style.border = "1px solid #ccc";
            popup.style.padding = "5px";
            popup.style.borderRadius = "5px";
            popup.style.zIndex = 10000;
            popup.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";

            const select = document.createElement("select");
            lists.forEach(listName => {
                const option = document.createElement("option");
                option.value = listName;
                option.textContent = listName;
                select.appendChild(option);
            });
            popup.appendChild(select);

            const confirmBtn = document.createElement("button");
            confirmBtn.type = "button";
            confirmBtn.textContent = "Move";
            confirmBtn.style.marginLeft = "5px";
            popup.appendChild(confirmBtn);

            document.body.appendChild(popup);
            select.focus();

            // ❌ Verhindert, dass Popup durch globale Listener sofort verschwindet
            popup.addEventListener("click", e => e.stopPropagation());

            // Move ausführen
            confirmBtn.addEventListener("click", e => {
                e.stopPropagation();
                const newList = select.value;
                if (!newList) return;

                fetch(`/move_task/${taskId}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({ newList })
                }).then(res => {
                    if (res.ok) {
                        const taskItem = document.querySelector(`li[data-task-id='${taskId}']`);
                        if (taskItem) taskItem.remove();
                    } else alert("Could not move task.");
                }).finally(() => {
                    popup.remove();
                    popup = null;
                    contextMenu.style.display = "none";
                });
            });
        }
    });

    // globaler Click Listener zum Schließen
    document.addEventListener("click", function(e) {
        if (contextMenu && !contextMenu.contains(e.target)) {
            contextMenu.style.display = "none";
        }
        if (popup && !popup.contains(e.target)) {
            popup.remove();
            popup = null;
        }
    });



    // =======================
    // Fullscreen
    // =======================
    document.body.addEventListener("click", function (event) {
        if (event.target.classList.contains("fullscreen-btn")) {
            const button = event.target;
            const card = button.closest(".card");
            document.querySelectorAll(".card").forEach(c => {
                c.classList.remove("expanded");
                c.style.pointerEvents = "auto";
            });
            card.classList.add("expanded");
        } else if (!event.target.closest(".card.expanded")) {
            document.querySelectorAll(".card").forEach(c => {
                c.classList.remove("expanded");
                c.style.pointerEvents = "auto";
            });
        }
    });

    // =======================
    // Checkbox Handling
    // =======================
    document.body.addEventListener("change", function (event) {
        const checkbox = event.target;
        if (!checkbox.matches("input[type='checkbox']")) return;

        const taskItem = checkbox.closest("li[data-task-id]");
        if (!taskItem) return;

        const taskId = taskItem.dataset.taskId;
        const parentCard = taskItem.closest(".card");
        const listName = parentCard.dataset.listName || parentCard.querySelector("h2").textContent.trim();
        const incompleteTasksContainer = document.querySelector(`#incomplete-tasks-${listName}`);
        const completedTasksContainer = document.querySelector(`#completed-tasks-${listName}`);




        fetch(`/toggle_task/${taskId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({
                completed: checkbox.checked
            }),
        })

        .then(response => {
            if (response.ok) {
                if (checkbox.checked) {
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
        .catch(error => console.error("Error:", error));
    });

    // =======================
    // Drag & Drop (inkl. Unteraufgaben)
    // =======================
    document.body.addEventListener("dragstart", function (event) {
        const task = event.target.closest("li[data-task-id]");
        if (!task) return;
        draggedItem = task;
        event.dataTransfer.effectAllowed = "move";
    });

    document.body.addEventListener("dragend", function () {
        draggedItem = null;
    });

    document.body.addEventListener("dragover", function(event) {
        const listContainer = event.target.closest("ul[id^='incomplete-tasks-'], ul[id^='completed-tasks-']");
        if (listContainer) event.preventDefault();
    });





    document.body.addEventListener("drop", function (event) {
        // Task, auf den gedroppt wird
        const targetTask = event.target.closest("li[data-task-id]");
        // UL, auf die gedroppt wird (incomplete oder completed)
        const listContainer = event.target.closest("ul[id^='incomplete-tasks-'], ul[id^='completed-tasks-']");

        if (!draggedItem || (!targetTask && !listContainer)) return;
        event.preventDefault();

        // Falls direkt auf eine Task gedroppt, setzen wir die UL
        const parentUL = listContainer || (targetTask ? targetTask.parentNode : null);
        if (!parentUL) return;

        // Task einfügen
        if (targetTask && targetTask.parentNode === parentUL) {
            const bounding = targetTask.getBoundingClientRect();
            const offset = event.clientY - bounding.top;
            if (offset > bounding.height / 2) {
                parentUL.insertBefore(draggedItem, targetTask.nextSibling);
            } else {
                parentUL.insertBefore(draggedItem, targetTask);
            }
        } else {
            // Direkt auf leere Liste drop
            parentUL.appendChild(draggedItem);
        }

        // parentId bestimmen (für Unteraufgaben!)
        const parentLI = parentUL.closest("li[data-task-id]");
        const parentId = parentLI ? parentLI.dataset.taskId : null;

        // Neue ListName bestimmen (wichtig für Special Lists)
        const newListName = parentUL.closest(".card")?.dataset.listName;

        // Reihenfolge korrekt bauen
        const order = Array.from(parentUL.children).map(li => li.dataset.taskId);
        console.log("DEBUG sending order:", order, "parentId:", parentId, "listName:", newListName);
        console.log("Dragged Item:", draggedItem);
        console.log("Target UL:", parentUL);
        console.log("Order to send:", order);
        console.log("Parent ID:", parentId);
        console.log("List Name:", newListName);

        fetch("/update_task_order", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken  // ✅ hier Token mitschicken
            },
            credentials: "same-origin",  // wichtig für Cookies
            body: JSON.stringify({
                order: order,
                parentId: parentId,
                listName: newListName
            })
        })
        .then(res => {
            console.log("Fetch response:", res.status, res.statusText);
            if (!res.ok) console.error("❌ Order update failed");
        });


        draggedItem = null;
        console.log("Order:", order, "Parent:", parentId, "List:", newListName);
    });


});
