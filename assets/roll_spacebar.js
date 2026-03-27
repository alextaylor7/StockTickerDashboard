/* Spacebar triggers Roll Dice when not typing in an input (dashboard page only has roll-btn when on /dashboard). */
(function () {
  document.addEventListener("keydown", function (e) {
    if (e.code !== "Space" && e.key !== " ") return;
    var el = document.activeElement;
    if (el) {
      var tag = el.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (el.isContentEditable) return;
    }
    var btn = document.getElementById("roll-btn");
    if (!btn) return;
    e.preventDefault();
    btn.click();
  });
})();
