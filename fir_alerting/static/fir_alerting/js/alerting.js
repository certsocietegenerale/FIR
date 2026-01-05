document.addEventListener("DOMContentLoaded", () => {
  const editors = {};

  async function getTemplate(button) {
    const inc = document.getElementById("details-container").dataset.eventId;
    const bl = button.dataset.bl || "";
    const type = button.dataset.type;
    const sendButton = document.querySelector("#send_email");

    try {
      const response = await fetch(
        `/api/alerting/${inc}?type=${type}&bl=${bl}`,
      );
      if (!response.ok) throw new Error("Failed to fetch template");
      const msg = await response.json();

      // Show Bootstrap modal
      const modalEl = document.getElementById("sendEmail");
      const sendEmailModal = new bootstrap.Modal(modalEl);
      sendEmailModal.show();
      addInputListeners();

      modalEl.querySelector("#id_behalf").value = msg.behalf || "";
      modalEl.querySelector("#id_to").value = msg.to || "";
      modalEl.querySelector("#id_cc").value = msg.cc || "";
      modalEl.querySelector("#id_bcc").value = msg.bcc || "";
      modalEl.querySelector("#id_subject").value = msg.subject || "";
      editors["id_body"].value(msg.body || "");

      modalEl.dataset.type = type;
      modalEl.dataset.bl = bl;
    } catch (err) {
      console.error("Error loading template:", err);
    }
  }

  function addInputListeners() {
    document
      .querySelectorAll("#email_form :is(input, textarea)")
      .forEach((item) => {
        item.addEventListener("input", (e) => {
          if (item.type == "email") {
            if (areEmailsValid(item.value)) {
              item.classList.remove("invalid-input");
            } else {
              if (["id_behalf", "id_to"].includes(item.id)) {
                item.classList.add("invalid-input");
              } else if (item.value.length != 0) {
                item.classList.add("invalid-input");
              } else {
                item.classList.remove("invalid-input");
              }
            }
          }

          const sendButton = document.querySelector("#send_email");
          sendButton.disabled = false;
          sendButton.textContent = sendButton.dataset.origText;
        });
      });
  }

  function areEmailsValid(value) {
    if (!value) return false;

    // Split on comma or semicolon
    const parts = value
      .split(",")
      .flatMap((part) => part.split(";"))
      .map((e) => e.trim())
      .filter(Boolean);

    const validator = document.createElement("input");
    validator.type = "email";

    return parts.every((part) => {
      let email = part;

      // If the email is in quotes with <>, extract the part inside <>
      const match = part.match(/<(.+)>/);
      if (match) {
        email = match[1].trim();
      }

      validator.value = email;
      return validator.checkValidity();
    });
  }

  async function addAutoComment(type, bl) {
    const form = new FormData();
    const main_container = document.getElementById("details-container");

    var comment = "Takedown started";

    if (type == "alerting") {
      comment = "Alert sent";
      if (bl) {
        comment += ` to ${bl}`;
      }
    }
    comment += ".";
    form.append("comment", comment);
    form.append("action", type);
    form.append("incident", main_container.dataset.eventId);

    await add_comment(form);
  }

  async function sendEmail() {
    const inc = document.getElementById("details-container").dataset.eventId;
    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]",
    ).value;
    const sendButton = document.querySelector("#send_email");
    sendButton.disabled = true;
    sendButton.textContent = sendButton.dataset.loadingText;

    const modalEl = document.getElementById("sendEmail");
    const type = modalEl.dataset.type;
    const bl = modalEl.dataset.bl;

    document.querySelector("#id_body").value = editors["id_body"].value();

    const form = document.querySelector("#email_form");
    const formData = new FormData(form);

    try {
      const response = await fetch(`/api/alerting/${inc}`, {
        method: "PUT",
        body: formData,
        headers: {
          "X-CSRFToken": csrftoken,
        },
      });

      const msg = await response.json();

      if (msg.status === "ok") {
        bootstrap.Modal.getInstance(modalEl).hide();
        addAutoComment(type, bl);
        sendButton.textContent = sendButton.dataset.origText;
        sendButton.disabled = false;
      } else if (msg.status === "ko") {
        sendButton.textContent = sendButton.dataset.errorText;
        console.error(msg.detail);
      }
    } catch (err) {
      console.error("Error sending email:", err);
      sendButton.textContent = sendButton.dataset.errorText;
    }
  }

  // Main button click handler
  const alertButton = document.querySelector("#details-actions-alert");
  if (alertButton) {
    alertButton.addEventListener("click", (event) => {
      event.preventDefault();
      if (
        alertButton.dataset.type == "alerting" &&
        !alertButton.dataset.bl &&
        document.querySelectorAll("#details-actions-alert-bls a").length != 0
      ) {
        document
          .querySelector(".details-actions-supmenu")
          ?.classList.add("visually-hidden");
        document
          .querySelector("#details-actions-alert-bls")
          ?.classList.remove("visually-hidden");
      } else {
        getTemplate(alertButton);
      }
    });
  }

  // Submenu click handler
  document.querySelectorAll(".details-alert-bl").forEach((el) => {
    el.addEventListener("click", () => {
      event.preventDefault();
      document
        .querySelector("#details-actions-alert-bls")
        ?.classList.add("visually-hidden");
      getTemplate(el);
    });
  });

  // Fetch the email form
  async function fetchEmailForm() {
    const emailformUrl = document.querySelector("#details-actions-alert-bls")
      ?.dataset.url;
    if (!emailformUrl) return;

    try {
      const response = await fetch(emailformUrl);
      const data = await response.text();

      document
        .querySelector("#addComment")
        .insertAdjacentHTML("afterend", data);
      editors["id_body"] = init_easymde(document.getElementById("id_body"));

      document.querySelector("#send_email").addEventListener("click", () => {
        sendEmail();
      });
    } catch (err) {
      console.error("Error fetching email form:", err);
    }
  }
  fetchEmailForm();
});
