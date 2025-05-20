$(function () {
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
  // show/hide the "Add" sub-menu
  const add_button = document.getElementById("details-actions-add-link");
  const all_submenus = document.getElementsByClassName(
    "details-actions-supmenu",
  );
  const submenu_add = document.getElementById("details-actions-add");
  const main_container = document.getElementById("details-container");
  add_button.addEventListener("click", function (event) {
    for (const sub of all_submenus) {
      sub.classList.add("visually-hidden");
    }
    submenu_add.classList.remove("visually-hidden");
    event.preventDefault();
  });
  main_container.addEventListener("click", function (event) {
    for (const sub of all_submenus) {
      sub.classList.add("visually-hidden");
    }
  });

  // Status changes
  for (let link of document.getElementsByClassName("change-status-button")) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      change_status(event.target);
    });
  }

  // Attributes
  set_delete_attribute_event_listner();
  for (const elem of document.querySelectorAll(
    "#show_attribute_form, #details-add-attribute",
  )) {
    if (elem != null) {
      elem.addEventListener("click", function (event) {
        event.preventDefault();
        show_add_attributes_form();
      });
    }
  }
  const select = document.querySelector("#attributes select");
  if (select) {
    select.addEventListener("change", function (event) {
      update_attribute_placeholder(event.target);
    });
  }
  const form = document.getElementById("add-attribute-form");
  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      add_attribute(form);
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

// Attributes

function set_delete_attribute_event_listner() {
  for (let span of document.getElementsByClassName("delete-attribute")) {
    span.addEventListener("click", function (event) {
      event.preventDefault();
      delete_attribute(event.target);
    });
  }
}

function show_add_attributes_form() {
  const form = document.getElementById("attribute_form");
  const div_attributes = document.getElementById("attributes");
  const show_attribute = document.getElementById("show_attribute_form");
  const input_value = document.getElementById("attribute-value");
  const select = document.querySelector("#attribute_form select");

  input_value.value = "";
  div_attributes.classList.remove("visually-hidden");
  form.classList.remove("visually-hidden");
  show_attribute.classList.add("visually-hidden");
  select.focus();
  update_attribute_placeholder(select);
}

async function delete_attribute(target) {
  if (typeof target.dataset.attribute == "undefined") {
    target = target.closest(".delete-attribute[data-attribute]");
  }

  let attribute = parseInt(target.dataset.attribute);
  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
  if (isNaN(attribute) || !csrftoken) {
    return;
  }
  var response = await fetch(`/api/attributes/${attribute}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
    },
  });

  if (response.status != 204) {
    console.error(await response.json());
  } else {
    const tr = target.closest("tr");
    tr.remove();
    const tbody = document.querySelector("#attributes tbody");
    const attributes = document.getElementById("attributes");
    if (tbody.childElementCount == 0) {
      attributes.classList.add("visually-hidden");
    }
  }
  set_delete_attribute_event_listner();
}

async function add_attribute(target) {
  const data = new FormData(target);
  const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");

  const request = await fetch("/api/attributes", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
    },
    body: data,
  });

  const response = await request.json();
  if (request.status != 201) {
    console.error(response);
  } else {
    document.getElementById("attribute_form").classList.add("visually-hidden");
    document
      .getElementById("show_attribute_form")
      .classList.remove("visually-hidden");

    let found = false;
    for (let tr of document.querySelectorAll(
      "#attribute_list .attribute-item",
    )) {
      if (
        tr.querySelector('td[class="head"]').textContent == response["name"]
      ) {
        tr.outerHTML = attribute_json_to_html(response).outerHTML;
        found = true;
      }
    }
    if (!found) {
      document
        .getElementById("attribute_list")
        .appendChild(attribute_json_to_html(response));
    }
    set_delete_attribute_event_listner();
  }
}

function attribute_json_to_html(response) {
  // add the new attribute to DOM
  const tr = document.createElement("tr");
  const td_value = document.createElement("td");
  const td_head = document.createElement("td");
  const span_id = document.createElement("span");

  tr.classList.add("attribute-item", "text-break");
  td_head.classList.add("head");
  span_id.classList.add("delete-attribute");

  td_head.textContent = response["name"];
  td_value.textContent = response["value"];
  span_id.dataset.attribute = response["id"];
  span_id.innerHTML = '<i class="bi bi-x-circle"></i>';

  tr.append(td_head);
  tr.append(td_value);
  tr.innerHTML += `<td>${span_id.outerHTML}</td>`;
  return tr;
}

function update_attribute_placeholder(target) {
  let placeholder = "value";

  const unit = target.options[target.selectedIndex].dataset.unit;
  if (unit != null && unit != "count" && unit != "None") {
    placeholder = `${placeholder} in ${unit}`;
  }

  document.getElementById("attribute-value").placeholder = placeholder;
}
