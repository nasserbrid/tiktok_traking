// static/js/home.js

document.addEventListener("DOMContentLoaded", function () {
  // Animation au scroll pour les cartes
  const cards = document.querySelectorAll(".card");

  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  }, observerOptions);

  cards.forEach((card) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(30px)";
    card.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    observer.observe(card);
  });

  // Confirmation avant suppression
  const deleteButtons = document.querySelectorAll('a[href*="supprimer"]');
  deleteButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      if (!this.href.includes("compte_delete")) {
        // Si ce n'est pas la page de confirmation, on demande confirmation
        if (!confirm("Es-tu sûr de vouloir supprimer ce compte ?")) {
          e.preventDefault();
        }
      }
    });
  });

  // Auto-dismiss des alerts après 5 secondes
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });

  // Tooltip pour les badges de statut
  const badges = document.querySelectorAll(".badge");
  badges.forEach((badge) => {
    badge.setAttribute("title", badge.textContent.trim());
  });

  console.log("🚀 TikTok Tracking App loaded");

  const popup = document.getElementById("my-popup");
  const closeBtn = document.getElementById("popup-close");

  // Afficher la popup après 1 seconde par exemple
  setTimeout(() => {
    popup.style.display = "flex";
  }, 1000);

  // Fermer la popup
  closeBtn.addEventListener("click", () => {
    popup.style.display = "none";
  });

  // Fermer si clic en dehors du contenu
  popup.addEventListener("click", (e) => {
    if (e.target === popup) {
      popup.style.display = "none";
    }
  });

  const container = document.getElementById("live-notifications-container");
  const socket = new WebSocket("ws://" + window.location.host + "/ws/lives/");
//   const socket = new WebSocket("wss://" + window.location.host + "/wss/lives/");

 socket.onopen = () => console.log("✅ WebSocket connecté");
 socket.onerror = (err) => console.error("❌ WebSocket erreur", err);


  socket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    if (data.type === "live_notification") {
      const popup = document.createElement("div");
      popup.classList.add("live-popup");
      popup.textContent = `🔴 ${data.compte} est en live ! Titre : ${data.titre}`;
      container.appendChild(popup);

      // Supprime la popup après 5 secondes
      setTimeout(() => popup.remove(), 5000);
    }
  };
});
