var editors = {}

$(function () {

  $('.markdown').each(function (index) {
    editors[$(this).attr("id")] = init_simplemde($(this));
  });

  $('.markdown-text').each(function (index) {
    var elt = $(this);

    md = elt.text();
    elt.html(marked(md));
    elt.removeClass('hide');
  });

});

function init_simplemde(textarea, initial_text) {
  var simplemde = new SimpleMDE({
    element: textarea[0],
    autosave: {
      enabled: true,
      uniqueId: window.location.href
    },
    renderingConfig: {
      codeSyntaxHighlighting: true
    },
    spellChecker: false
  });

  return simplemde
}
