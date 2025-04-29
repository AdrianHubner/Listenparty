document.addEventListener("DOMContentLoaded", function() {
  const unlockButtons = document.querySelectorAll(".unlock-btn");
  unlockButtons.forEach(button => {
    button.addEventListener("click", function() {
      const listName = this.getAttribute("data-list-name");
      const password = prompt("Bitte Passwort eingeben:");
      if (password !== null) {
        fetch("/secret/verify", {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: new URLSearchParams({
            list_name: listName,
            password: password
          })
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // Erfolgreich entsperrt: Leite zu einer Ansicht weiter, die die Inhalte der Liste anzeigt.
            // Das könnte z. B. der Endpunkt "view_list" sein.
            window.location.href = "/view_list/" + encodeURIComponent(listName);
          } else {
            alert("Falsches Passwort!");
          }
        })
        .catch(error => {
          console.error("Fehler beim Überprüfen des Passworts:", error);
        });
      }
    });
  });
});
