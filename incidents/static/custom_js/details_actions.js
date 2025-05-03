$(function () {
  $("#details-actions-add-link").click(function (event) {
    $(".details-actions-supmenu").hide();
    $("#details-actions-add").show();
    event.preventDefault();
  });

  $("#details-container").click(function (event) {
    $(".details-actions-supmenu").hide();
  });


  //
  // Attributes
  //
  function update_attribute_placeholder() {
    var placeholder = "value";
    var unit = $("#attributes option:selected").attr("data-unit");
    if (unit != "" && unit != "count" && unit != "None") {
      placeholder = placeholder + " in " + unit;
    }
    $("#attribute-value").attr("placeholder", placeholder);
  }

  $("#show_attribute_form a").click(function (event) {
    $("#attribute_form").removeClass("visually-hidden");
    $("#attribute_form select:first").focus();
    $("#show_attribute_form").addClass("visually-hidden");

    event.preventDefault();
  });

  $("#attributes select").change(function () {
    update_attribute_placeholder();
  });

  $("#details-add-attribute").click(function (event) {
    $("#attributes").removeClass("visually-hidden");
    $("#show_attribute_form a").click();

    event.preventDefault();
  });

  update_attribute_placeholder();

  // Set up form for new comment
  $("#details-actions-comment").click(function (event) {
    $("#addComment").modal("toggle");

    var form = $("#addComment form");
    form.attr("action", form.data("new-comment-url"));
    form.data("target", "#tab_comments tbody");
    form.data("action", "prepend");

    $("#id_action").val("");
    var date = new Date();
    date = new Date(date.getTime() - new Date().getTimezoneOffset() * 60 * 1000)
      .toISOString()
      .slice(0, 16);
    $("#id_date").val(date);
  });

  // Set up form for update
  $("#tab_comments").on("click", ".edit-comment", function (event) {
    var form = $("#addComment form");
    var comment_id = $(this).data("comment-id");

    $.getJSON("/ajax/comment/" + comment_id, function (msg) {
      var comment = jQuery.parseJSON(msg)[0];
      var text = comment.fields.comment;
      var action = comment.fields.action;
      var date = new Date(comment.fields.date);
      date = new Date(date.getTime() - date.getTimezoneOffset() * 60 * 1000)
        .toISOString()
        .slice(0, 16);

      $("#addComment").modal("toggle");

      editors["id_comment"].value(text);
      $("#id_action").val(action);
      $("#id_date").val(date);

      form.attr("action", "/ajax/comment/" + comment_id);
      form.data("target", "#comment_id_" + comment_id);
      form.data("action", "replaceWith");
    });
  });

  // Custom behavior when comment is added
  $("#addComment").on("fir.form.success", function (event) {
    // Dismiss modal
    editors["id_comment"].value("");
    $("#addComment").modal("hide");

    // Hack not to trigger on update
    if ($("#addComment form").data("action") != "replaceWith") {
      // Update comment count
      var count = parseInt($("#comment-count").text());
      $("#comment-count").text(count + 1);
    }

    event.stopPropagation();
  });

  // Custom behavior when comment is removed
  $("#tab_comments").on("fir.form.success", function (event) {
    // Update comment count
    var count = parseInt($("#comment-count").text());
    $("#comment-count").text(count - 1);

    event.stopPropagation();
  });
});

document.addEventListener("DOMContentLoaded", function () {
  for (let link of document.getElementsByClassName("change-status-button")) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      change_status(event.target);
    });
  }
});

async function change_status(target) {
  if (typeof target.dataset.incid == "undefined") {
    target = target.closest(".change-status-button[data-incid]");
  }
  let inc_id = parseInt(target.dataset.incid);
  let new_status = target.dataset.status;
  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
  if (isNaN(inc_id) || !new_status || !csrftoken) {
    return;
  }
  var response = await fetch(`/api/incidents/${inc_id}`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
      "Content-type": "application/json",
    },
    body: JSON.stringify({ status: new_status }),
  });

  if (response.status != 200) {
    console.error(await response.json());
  } else {
    document.location.reload();
  }
}
