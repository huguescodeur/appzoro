// ? Logique pour faire disparaitre les messages flash après 5s
setTimeout(function () {
  var flashMessage = document.getElementById("flash-message");
  if (flashMessage) {
    flashMessage.style.display = "none";
  }
}, 3000);
