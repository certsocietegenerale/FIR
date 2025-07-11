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

  // Show add comment modal
  const add_comment_button = document.getElementById("details-actions-comment");
  if (add_comment_button) {
    add_comment_button.addEventListener("click", function (event) {
      event.preventDefault();
      display_comment_form();
    });
  }
  // delete button comment
  for (let delete_comment_button of document.querySelectorAll(
    ".delete-comment",
  )) {
    delete_comment_button.addEventListener("click", function (event) {
      event.preventDefault();
      delete_comment(delete_comment_button.dataset.id);
      delete_comment_button.parentElement.parentElement.remove();
    });
  }
  // edit button comment
  for (let edit_comment_button of document.querySelectorAll(".edit-comment")) {
    edit_comment_button.addEventListener("click", function (event) {
      event.preventDefault();
      display_comment_form(edit_comment_button.dataset.id);
    });
  }
  // Submit comment
  const comment_form = document.getElementById("comment_form");
  if (comment_form) {
    comment_form.addEventListener("submit", function (event) {
      submit_comment_form(comment_form);
      event.preventDefault();
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

async function display_comment_form(id) {
  const main_div = document.getElementById("addComment");
  const comment_form = main_div.querySelector("form");
  const comment_modal = bootstrap.Modal.getOrCreateInstance("#addComment");

  if (id != undefined) {
    const query = await fetch(`/api/comments/${parseInt(id)}`);
    const response = await query.json();
    editors["id_comment"].value(response["comment"]);
    document.getElementById("id_action").value = response["action"];

    var date = new Date(response["date"]);
    date = new Date(date.getTime() - new Date().getTimezoneOffset() * 60 * 1000)
      .toISOString()
      .slice(0, 16);
    document.getElementById("id_date").value = date;
    comment_form.dataset.id = parseInt(id);
  } else {
    editors["id_comment"].value("");
    document.getElementById("id_action").value = "";
    var date = new Date();
    date = new Date(date.getTime() - new Date().getTimezoneOffset() * 60 * 1000)
      .toISOString()
      .slice(0, 16);
    document.getElementById("id_date").value = date;
    delete comment_form.dataset.id;
  }

  comment_modal.show();

  comment_form.dataset.action = "prepend";
  comment_form.setAttribute("action", "/api/comments");
  editors["id_comment"].codemirror.refresh();
}

async function delete_comment(id) {
  id = parseInt(id);
  if (isNaN(id)) {
    return;
  }
  const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
  const query = await fetch(`/api/comments/${id}`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": csrftoken.value,
    },
  });

  if (query.status != 204) {
    console.error(await query.json());
  } else {
    const count = document.getElementById("comment-count");
    count.textContent = parseInt(count.textContent) - 1;
  }
}

async function submit_comment_form(form) {
  const data = new FormData(form);
  const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
  const existing_id = document.querySelector("#addComment form").dataset.id;

  var url = "/api/comments";
  var method = "POST";
  if (existing_id) {
    url = `/api/comments/${existing_id}`;
    method = "PUT";
  }

  const query = await fetch(url, {
    method: method,
    headers: {
      "X-CSRFToken": csrftoken.value,
      Accept: "application/json",
    },
    body: data,
  });
  const response = await query.json();

  if (existing_id) {
    document.getElementById(`comment_id_${existing_id}`).remove();
  } else {
    const count = document.getElementById("comment-count");
    count.textContent = parseInt(count.textContent) + 1;
  }

  add_comment_to_dom(response);
  // hide modal
  const main_div = document.getElementById("addComment");
  const comment_modal = bootstrap.Modal.getOrCreateInstance("#addComment");
  comment_modal.hide();
}

function add_comment_to_dom(response) {
  // create the new comment and add it to DOM
  const tr = document.createElement("tr");
  tr.id = `comment_id_${parseInt(response["id"])}`;
  const td_date = document.createElement("td");
  td_date.classList.add("comment-date");
  td_date.textContent = moment(response["date"]).format("YYYY-MM-DD HH:mm");
  const td_user = document.createElement("td");
  td_user.textContent = response["opened_by"];
  const td_action = document.createElement("td");
  td_action.textContent = response["action"];
  const td_comment = document.createElement("td");
  td_comment.innerHTML = response["parsed_comment"];
  const td_edit = document.createElement("td");
  const td_delete = document.createElement("td");
  if (response["can_edit"]) {
    td_edit.innerHTML = `<a href="#" data-id="${parseInt(response["id"])}" class="edit-comment"><i class="bi bi-pencil"></i></a>`;
    td_delete.innerHTML = `<a href="#" data-id="${parseInt(response["id"])}" class="delete-comment"><i class="bi bi-x-circle"></i></a>`;
  }
  tr.appendChild(td_date);
  tr.appendChild(td_user);
  tr.appendChild(td_comment);
  tr.appendChild(td_action);
  tr.appendChild(td_edit);
  tr.appendChild(td_delete);

  const comment_table = document.querySelector("#tab_comments table tbody");
  comment_table.appendChild(tr);

  // reorganize the table
  var rows = [].slice.call(comment_table.querySelectorAll("tr"));
  rows.sort(function (a, b) {
    return (
      moment(b.cells[0].textContent).unix() -
      moment(a.cells[0].textContent).unix()
    );
  });
  rows.forEach(function (v) {
    comment_table.appendChild(v);
  });

  // delete button comment
  for (let delete_comment_button of document.querySelectorAll(
    ".delete-comment",
  )) {
    delete_comment_button.addEventListener("click", function (event) {
      event.preventDefault();
      delete_comment(delete_comment_button.dataset.id);
      delete_comment_button.parentElement.parentElement.remove();
    });
  }

  // edit button comment
  for (let edit_comment_button of document.querySelectorAll(".edit-comment")) {
    edit_comment_button.addEventListener("click", function (event) {
      event.preventDefault();
      display_comment_form(edit_comment_button.dataset.id);
    });
  }
}
