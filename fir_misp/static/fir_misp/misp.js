var observables_template = Handlebars.compile($("#misp-observables-template").html());
var tab_data_template = Handlebars.compile($("#misp-tab-data-template").html());
var misp_error_message_template = Handlebars.compile($("#misp-error-message-template").html());

$(function () {
  query_misp();
});

function query_misp() {
  artifacts = [];
  inputs = $("input[name='artifacts_misp']").serializeArray();
  for (var i in inputs) {
    artifacts.push(inputs[i]['value']);
  }
  input_int = $("input[name='inc_id_misp']").serializeArray();
  inc_id = input_int[0]["value"]
  misp_query_artifacts(artifacts, inc_id);
}

function misp_query_artifacts(observables, incident_id) {
  // extra options are set in ajaxSetup
  $.ajax({
    url: "/misp/query_misp_artifacts",
    type: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')},
    contentType: "application/json",
    data: JSON.stringify({"observables": observables, "incident_id":incident_id}),
    success: function(data) {
      $("#tab_misp").empty();
      render_results(data);
    },
    error: function (data, status, error) {
      $("#tab_misp").append(misp_error_message_template({"error_message": "An error happened : " + error + ". Details : " + JSON.stringify(data["responseJSON"])}))
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



  $("#tab_misp").html(observables_template(data));
  $("#misp-tab .misp-count").html(tab_data_template(data))

  $('.tagsinput').tagsInput();

  // check by default the most recent misp event (last one in the list)
  $(".misp_event input[type=checkbox]").last().prop("checked", true)

  // display tags suggestion if button clicked
  $(".show_tag_suggestions").click(function(event) {
    event.preventDefault();
    $(this).parent().next(".tag_suggestions").toggleClass("d-none");
  });

  // activate tooltips
  const tooltipTriggerList = document.querySelectorAll('.tooltip-info')
	const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

  // add tag value suggestion onclick
  $(".tag_suggestion").click(function(event) {
    event.preventDefault();
    input_elt = $(this).parent().prevAll().find(".tagsinput-add-container input")
    input_elt.val($(this).attr("data-value"))
    $(this).parent().prevAll().find(".tagsinput-add-container input").trigger("blur") // to submit the tag
  });

  // Send button
  $("#send-to-misp").click(function(event) {
    event.preventDefault();
    var all_tags = $(".all-tags").val().split(',').filter(Boolean);
    var observables = []
    var misp_events = []

    $(".misp-send tr.misp_event").each(function() {
      if ($(this).find("input[type=checkbox]:checked").length !== 0) {
        var misp_event = {
          "value": $(this).find('.value').text(),
        }
        misp_events.push(misp_event)
      }
    });

    $(".misp-send tr.observable").each(function() {
      if ($(this).find("input[type=checkbox]:checked").length !== 0) {
        var observable = {
          "value": $(this).find('.value').text(),
          "tags": all_tags.concat($(this).find('input.tagsinput').val().split(',').filter(Boolean))
        }
        observables.push(observable)
      }
    });

    misp_post_observables(observables, misp_events, $(this));

  });

  // toggle buttons
  $("#toggle-send").click(function(event) {
    event.preventDefault();
    $("div.send").toggle();
    $("div.read").toggle();
    $(this).text($(this).text() == "Cancel" ? "Send to misp..." : "Cancel");
  });

  // "Select all" checkbox
  $("input.check-all").click(function(event) {
    state = this.checked;
    targetClass = $(this).data('target');
    $("."+targetClass+" input[type=checkbox]").prop("checked", state);
  });
}

function misp_post_observables(observables, misp_events, row) {

  $('#waitingMessage').show();
  
  // extra options are set in ajaxSetup
  $.ajax({
    url: "/misp/send_misp_artifacts",
    type: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')},
    contentType: "application/json",
    data: JSON.stringify({"observables": observables, "misp_events": misp_events, "fid": $("#fid").data("fid")}),
    success: function(data) {
      $('#waitingMessage').hide();
      query_misp();
    },
    error: function (data, status, error) {
      $('#waitingMessage').hide();
      $("#tab_misp").prepend(misp_error_message_template({"error_message": "An error happened : " + error + ". Details : " + JSON.stringify(data["responseJSON"])}))
    }
  });
}
