document.addEventListener("DOMContentLoaded", () => {
  function escapeHtml(html) {
    var text = document.createTextNode(html);
    var p = document.createElement("p");
    p.appendChild(text);
    return p.innerHTML;
  }

  async function fetch_notification_preferences() {
    let url = "/api/notifications_preferences";
    let entries = [];
    while (url != null) {
      var response = await (
        await fetch(url, {
          headers: { Accept: "application/json" },
        })
      ).json();
      entries = entries.concat(response["results"]);
      url = response["next"];
    }

    // split event into "section" and "action", join BLs, escape HTML
    entries = entries.map((entry) => {
      const [section, action] = entry.event.split(":");
      const blJoined = (entry.business_lines || [])
        .map((bl) => String(bl).split(" > ").pop())
        .join(", ");
      return {
        section: escapeHtml(section),
        action: escapeHtml(action),
        method: escapeHtml(entry.method),
        business_lines_joined: escapeHtml(blJoined),
        event: escapeHtml(entry.event),
      };
    });

    const templateSrc = document.querySelector(
      "#notification-preference-template",
    ).innerHTML;
    // get handlebars template
    const template = Handlebars.compile(templateSrc);
    const tbody = document.querySelector("#notifications-preferences tbody");
    tbody.innerHTML = template({ preferences: entries });

    // add delete preference event listner
    for (const unsubscribe of document.querySelectorAll(
      "#notifications-preferences .unsubscribe-notification",
    )) {
      unsubscribe.addEventListener("click", function (event) {
        event.preventDefault();
        delete_notification_preference(event.currentTarget);
      });
    }
  }

  async function populate_notificationpreferences_modal(event) {
    const pref = event.relatedTarget.dataset.notificationpreference;
    const modal = document.querySelector("#subscribe_notifications");

    const existig_notifications = [
      ...new Set(
        Array.from(
          document.querySelectorAll(
            "#notifications-preferences table [data-notificationpreference]",
          ),
        ).map((el) => el.dataset.notificationpreference),
      ),
    ];

    const id_event = modal.querySelector("#id_event");
    const id_method = modal.querySelector("#id_method");
    const id_business_lines = modal.querySelector("#id_business_lines");
    id_event.disabled = false;
    var response = null;

    if (pref) {
      response = await (
        await fetch(`/api/notifications_preferences/${pref}`, {
          headers: { Accept: "application/json" },
        })
      ).json();
      id_event.disabled = true;
    }
    id_method.value = response?.method || "";
    id_event.value = response?.event || "";

    const bls = response?.business_lines || [];
    for (var option of id_business_lines.options) {
      option.selected = false;
      if (bls.includes(option.textContent)) {
        option.selected = true;
      }
    }

    // setup select2 dropdown
    $(modal)
      .find("select")
      .each(function (e) {
        $(this).select2({
          dropdownAutoWidth: true,
          width: "100%",
          theme: "bootstrap-5",
        });
        $(this).trigger("change");
      });

    for (const select of document.querySelectorAll(
      "#subscribe_notifications_form select",
    )) {
      select.addEventListener("change", function (event) {
        const submit_button = document.querySelector(
          "#subscribe_notifications_form button[type=submit]",
        );
        submit_button.disabled = false;
        submit_button.textContent = submit_button.dataset.save;
      });
    }

    modal
      .querySelector("#subscribe_notifications_form")
      .addEventListener("submit", function (event) {
        event.preventDefault();
        save_notification_preference(pref);
      });
  }

  async function save_notification_preference(pref) {
    const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
    const id_event = document.querySelector(
      "#subscribe_notifications_form #id_event",
    );
    const disabled = id_event.disabled;
    id_event.disabled = false;
    const data = new FormData(
      document.querySelector("#subscribe_notifications_form"),
    );
    id_event.disabled = disabled;

    const selected_bls = [
      ...document.querySelector("#id_business_lines").selectedOptions,
    ].map((o) => o.textContent);

    data.delete("business_lines");
    selected_bls.forEach((bl) => {
      data.append("business_lines", bl);
    });

    let url = "/api/notifications_preferences";
    let method = "POST";
    if (pref) {
      url = `/api/notifications_preferences/${pref}`;
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
    if (!query.ok) {
      const submit_button = document.querySelector(
        "#subscribe_notifications_form button[type=submit]",
      );
      submit_button.disabled = true;
      submit_button.textContent = submit_button.dataset.error;
      return;
    }
    const modal = document.querySelector("#subscribe_notifications");
    bootstrap.Modal.getInstance(modal).hide();

    fetch_notification_preferences();
  }

  async function delete_notification_preference(elem) {
    const pref = elem.dataset.notificationpreference;
    let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
    if (!pref || !csrftoken) {
      return;
    }
    var response = await fetch(`/api/notifications_preferences/${pref}`, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "X-CSRFToken": csrftoken.value,
      },
    });

    if (response.status != 204) {
      console.error(await response.json());
    } else {
      elem.parentElement.parentElement.remove();
    }
  }

  async function populate_notificationoptions_modal(event) {
    const notif_method = event.relatedTarget.dataset.method;
    const modal = document.querySelector(
      `#configure_${notif_method}_notifications`,
    );
    var response = await (
      await fetch(`/api/notifications_method_configuration/${notif_method}`, {
        headers: { Accept: "application/json" },
      })
    ).json();

    const existing_config = response?.value || {};

    for (const input of modal.querySelectorAll("input")) {
      const key = input.id.substring(3);
      if (existing_config.hasOwnProperty(key)) {
        input.value = existing_config[key];
      }
    }

    modal
      .querySelector(`#configure_${notif_method}_form`)
      .addEventListener("submit", function (event) {
        event.preventDefault();
        save_notification_options(
          notif_method,
          response?.hasOwnProperty("value"),
        );
      });

    for (const select of document.querySelectorAll(
      `#configure_${notif_method}_form input`,
    )) {
      select.addEventListener("input", function (event) {
        const submit_button = document.querySelector(
          `#configure_${notif_method}_form button[type=submit]`,
        );
        submit_button.disabled = false;
        submit_button.textContent = submit_button.dataset.save;
      });
    }
  }

  async function save_notification_options(notif_method, already_existing) {
    const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
    const data = new FormData(
      document.querySelector(`#configure_${notif_method}_form`),
    );
    const json_data = { method: notif_method, value: {} };
    data.forEach((value, key) => (json_data.value[key] = value));
    delete json_data.value.csrfmiddlewaretoken;

    let url = "/api/notifications_method_configuration";
    let method = "POST";
    if (already_existing) {
      url = `/api/notifications_method_configuration/${notif_method}`;
      method = "PUT";
    }

    const query = await fetch(url, {
      method: method,
      headers: {
        "X-CSRFToken": csrftoken.value,
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(json_data),
    });

    const response = await query.json();
    if (!query.ok) {
      const submit_button = document.querySelector(
        `#configure_${notif_method}_form button[type=submit]`,
      );
      submit_button.disabled = true;
      submit_button.textContent = submit_button.dataset.error;
      return;
    }
    const modal = document.querySelector(
      `#configure_${notif_method}_notifications`,
    );
    bootstrap.Modal.getInstance(modal).hide();
  }

  document
    .querySelector("#subscribe_notifications")
    .addEventListener("show.bs.modal", function (event) {
      populate_notificationpreferences_modal(event);
    });

  const options = document.querySelectorAll(".notification-method-form");
  for (const o of options) {
    o.addEventListener("show.bs.modal", function (event) {
      populate_notificationoptions_modal(event);
    });
  }

  fetch_notification_preferences();
});
