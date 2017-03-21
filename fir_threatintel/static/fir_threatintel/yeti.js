var observables_template = Handlebars.compile($("#yeti-observables-template").html());
var matches_template = Handlebars.compile($("#yeti-matches-template").html());
var tab_data_template = Handlebars.compile($("#yeti-tab-data-template").html());

var headers = {
  "Accept": "application/json",
}
if (YETI_HTTP_AUTH_USERNAME != "") {
  headers["Authorization"] = "Basic " + btoa(YETI_HTTP_AUTH_USERNAME + ":" + YETI_HTTP_AUTH_PASSWORD);
}

YETI_API_KEY = $("#yeti_api_key").val();
YETI_ENDPOINT = $("#yeti_endpoint").val(); + ""
YETI_OBSERVABLE_ENDPOINT = YETI_ENDPOINT + "/observable/bulk";
YETI_MATCH_ENDPOINT = YETI_ENDPOINT + "/analysis/match";

if (YETI_API_KEY != "") {
  headers["X-Api-Key"] = YETI_API_KEY;
}

$(function () {
  query_yeti();
});

function query_yeti() {
  if (YETI_ENDPOINT == "") {
    return;
  }

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
    url: YETI_MATCH_ENDPOINT,
    type: 'POST',
    headers: headers,
    contentType: "application/json",
    data: JSON.stringify({"observables": observables}),
    success: function(data) {
      $("#tab_threatintel").empty();
      render_results(data);
    }
  });
}

function render_results(data) {

  Handlebars.registerHelper("join", function(array, sep, key) {
    ar = {}
    for (var i in array) {
      ar[array[i][key]] = 1;
    }
    return Object.keys(ar).join(sep);
  });



  $("#tab_threatintel").html(matches_template(data)).append(observables_template(data));
  $("#ti-tab .ti-count").html(tab_data_template(data))

  $('.tagsinput').tagsInput();

  // Send button
  $("#send-to-yeti").click(function(event) {
    event.preventDefault();
    var all_tags = $(".all-tags").val().split(',');
    var observables = []

    $(".yeti-send tr.observable").each(function() {
      if ($(this).find("input[type=checkbox]:checked").length !== 0) {
        var observable = {
          "value": $(this).find('.value').text(),
          "tags":  all_tags.concat($(this).find('input.tagsinput').val().split(','))
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

  fid = $("#fid").data("fid");
  for (var i in observables) {
    observables[i]['context'] = {"FID": fid, "source" : "FIR", "Description": "Seen in FIR ID:"+fid};
    observables[i]['source'] = "FIR"
  }

  // extra options are set in ajaxSetup
  $.ajax({
    url: YETI_OBSERVABLE_ENDPOINT,
    type: 'POST',
    headers: headers,
    contentType: "application/json",
    data: JSON.stringify({"observables": observables, "refang": false}),
    success: function(data) {
      query_yeti();
    }
  });
}
