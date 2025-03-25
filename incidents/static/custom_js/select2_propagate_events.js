// Convert select2 events to JS events
// From https://github.com/select2/select2/issues/1908#issuecomment-871095578
function addNativeEventTrigger(e) {
  if (window.document.documentMode) {
    // (IE doesnt support Event() constructor)
    // https://caniuse.com/?search=Event()
    var evt = document.createEvent("HTMLEvents");
    evt.initEvent("change", false, true);
    e.currentTarget.dispatchEvent(evt);
  } else {
    const event = new Event("change");
    e.currentTarget.dispatchEvent(event);
  }
  $(e.currentTarget).one("change", addNativeEventTrigger);
}

$(document).ready(function () {
  $("select").each(function (e) {
    $(this).one("change", addNativeEventTrigger);
  });
});
