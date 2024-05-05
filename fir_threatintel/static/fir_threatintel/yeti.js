var observables_template = Handlebars.compile($("#yeti-observables-template").html());
var tab_data_template = Handlebars.compile($("#yeti-tab-data-template").html());

$(function () {
  query_yeti();
});

function query_yeti() {
  artifacts = [];
  inputs = $("input[name='artifacts']").serializeArray();
  for (var i in inputs) {
    artifacts.push(inputs[i]['value']);
  }
  yeti_query_artifacts(artifacts);
}

function yeti_query_artifacts(observables) {
  // extra options are set in ajaxSetup
  $.ajax({
    url: "/threatintel/query_yeti_artifacts",
    type: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')},
    contentType: "application/json",
    data: JSON.stringify({"observables": observables}),
    success: function(data) {
      $("#tab_threatintel").empty();
      render_results(data);
    }
  });
}

function render_results(data) {

  Handlebars.registerHelper("join", function(array, sep) {
    if (!Array.isArray(array)) {
      return "";
    }
    return array.join(sep);
  });



  $("#tab_threatintel").html(observables_template(data));
  $("#ti-tab .ti-count").html(tab_data_template(data))

  $('.tagsinput').tagsInput();

  // Send button
  $("#send-to-yeti").click(function(event) {
    event.preventDefault();
    var all_tags = $(".all-tags").val().split(',').filter(Boolean);
    var observables = []

    $(".yeti-send tr.observable").each(function() {
      if ($(this).find("input[type=checkbox]:checked").length !== 0) {
        var observable = {
          "value": $(this).find('.value').text(),
          "tags": all_tags.concat($(this).find('input.tagsinput').val().split(',').filter(Boolean))
        }
        observables.push(observable)
      }
    });

    yeti_post_observables(observables, $(this));

  });

  // toggle buttons
  $("#toggle-send").click(function(event) {
    event.preventDefault();
    $("div.send").toggle();
    $("div.read").toggle();
    $(this).text($(this).text() == "Cancel" ? "Send to Yeti..." : "Cancel");
  });

  // "Select all" checkbox
  $("input.check-all").click(function(event) {
    state = this.checked;
    targetClass = $(this).data('target');
    $("."+targetClass+" input[type=checkbox]").prop("checked", state);
  });
}

function yeti_post_observables(observables, row) {
  for (var i in observables) {
    observables[i]['fid'] = $("#fid").data("fid");
  }

  // extra options are set in ajaxSetup
  $.ajax({
    url: "/threatintel/send_yeti_artifacts",
    type: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')},
    contentType: "application/json",
    data: JSON.stringify({"observables": observables}),
    success: function(data) {
      query_yeti();
    }
  });
}
