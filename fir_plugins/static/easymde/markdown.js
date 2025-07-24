var editors = {};

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".markdown").forEach(function (el) {
    editors[el.id] = init_easymde(el);
  });

  document.querySelectorAll(".markdown-text").forEach(function (elt) {
    elt.innerHTML = marked(elt.textContent);
    elt.classList.remove("hide");
  });
});

function init_easymde(textarea) {
  var easymde = new EasyMDE({
    element: textarea,
    renderingConfig: {
      codeSyntaxHighlighting: true,
    },
    forceSync: true,
    spellChecker: false,
    toolbar: [
      "bold",
      "italic",
      "heading-smaller",
      "heading-bigger",
      "|",
      "link",
      "code",
      "|",
      "unordered-list",
      "ordered-list",
      "table",
      "horizontal-rule",
      "|",
      "preview",
      "guide",
    ],
  });

  return easymde;
}
