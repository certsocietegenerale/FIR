var editors = {}

$(function () {

  $('.markdown').each(function (index) {
    editors[$(this).attr("id")] = init_easymde($(this));
  });

  $('.markdown-text').each(function (index) {
    var elt = $(this);

    md = elt.text();
    elt.html(marked(md));
    elt.removeClass('hide');
  });

});

function init_easymde(textarea, initial_text) {
  var easymde = new EasyMDE({
    element: textarea[0],
    renderingConfig: {
      codeSyntaxHighlighting: true
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
    ]
  });

  return easymde
}
