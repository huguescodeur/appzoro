// ? Logique pour faire disparaitre les messages flash après 5s
setTimeout(function () {
  var flashMessage = document.getElementById("flash-message");
  if (flashMessage) {
    flashMessage.style.display = "none";
  }
}, 5000);

// ? Logique pour faire la mise à jour dynamique du prix total
document.addEventListener("DOMContentLoaded", function () {
  var formVente = document.querySelector(".form_vente");
  var prixUnitaireDiv = document.getElementById("prixUnitaire");
  var prixTotalDiv = document.getElementById("prixTotal");

  // Fonction pour mettre à jour le prix unitaire
  function updatePrixUnitaire() {
    var id_produit = formVente.elements["produit"].value;

    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/get_prix_unitaire/" + id_produit, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          var response = JSON.parse(xhr.responseText);
          var prix_unitaire = response.prix_unitaire;

          if (prix_unitaire !== null) {
            prixUnitaireDiv.textContent =
              "Prix unitaire : $" + prix_unitaire.toFixed(2);
            updatePrixTotal();
          } else {
            prixUnitaireDiv.textContent = "Prix unitaire : N/A";
            prixTotalDiv.textContent = "Prix total : N/A";
          }
        } else {
          console.error("Erreur lors de la récupération du prix unitaire.");
        }
      }
    };
    xhr.send();
  }

  // Événement pour déclencher la mise à jour du prix unitaire lors de la sélection de produit
  formVente.addEventListener("input", function (event) {
    if (event.target.name === "produit") {
      updatePrixUnitaire();
    }
  });

  // Fonction pour mettre à jour le prix total
  function updatePrixTotal() {
    var quantite = parseInt(formVente.elements["quantite"].value, 10);
    var prix_unitaire_text = prixUnitaireDiv.textContent.split(":")[1].trim();
    var prix_unitaire = parseFloat(prix_unitaire_text.replace("$", "").trim());

    if (!isNaN(quantite) && !isNaN(prix_unitaire)) {
      var prix_total = quantite * prix_unitaire;
      prixTotalDiv.textContent = "Prix total : $" + prix_total.toFixed(2);
    } else {
      prixTotalDiv.textContent = "Prix total : N/A";
    }
  }

  // Événement pour déclencher la mise à jour du prix total lors du changement de quantité
  formVente.addEventListener("input", function (event) {
    if (event.target.name === "quantite") {
      updatePrixTotal();
    }
  });

  // Appeler la fonction initiale au chargement de la page
  updatePrixUnitaire();
  updatePrixTotal();
});
