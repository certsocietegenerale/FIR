document.addEventListener("DOMContentLoaded", () => {
  const editors = {};

  // Context menu on artifact rows
  document.querySelectorAll(".artifacts-table a").forEach((anchor) => {
    anchor.addEventListener("contextmenu", async (e) => {
      e.preventDefault();

      const artifact = anchor.innerText;
      const url = `/api/artifacts_enrichment/${artifact}/status`;

      const state = {
        SUCCESS: '"bi bi-check-circle text-success"',
        FAILURE: '"bi bi-x-circle text-danger"',
        PENDING: '"bi bi-clock"',
        UNKNOWN: '"bi bi-question-circle"',
        ERROR: '"bi bi-exclamation-triangle text-primary"',
      };

      const customMenu = document.querySelector(".custom-menu");

      // Remove old indicator
      const oldIndicator = customMenu.querySelector("#visualIndicator");
      if (oldIndicator) oldIndicator.remove();

      try {
        const response = await fetch(url);

        if (!response.ok) throw new Error("Request failed");
        const data = await response.json();
        const visualIndicator = `<span id="visualIndicator" class=${state[data.state]}></span>`;
        customMenu
          .querySelector("li a")
          .insertAdjacentHTML("afterbegin", visualIndicator);
      } catch {
        const visualIndicator = `<span id="visualIndicator" class=${state.ERROR}></span>`;
        customMenu
          .querySelector("li a")
          .insertAdjacentHTML("afterbegin", visualIndicator);
      }

      // Show context menu
      customMenu.style.display = "block";
      customMenu.style.top = `${e.pageY}px`;
      customMenu.style.left = `${e.pageX}px`;

      customMenu.dataset.artifact = artifact;
    });
  });

  // Context Menu: Hide menu when clicking elsewhere
  document.addEventListener("mousedown", (e) => {
    const customMenu = document.querySelector(".custom-menu");
    if (!e.target.closest(".custom-menu")) {
      customMenu.style.display = "none";
    }
  });

  // Context Menu: handle click on "Send abuse"
  document.querySelectorAll(".custom-menu li").forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const artifact = item.parentElement.dataset.artifact;
      getEmailTemplate(artifact);
      document.querySelector(".custom-menu").style.display = "none";
    });
  });

  function addInputListeners() {
    document
      .querySelectorAll("#sendAbuseEmail :is(input, textarea)")
      .forEach((item) => {
        item.addEventListener("input", (e) => {
          if (item.type == "email") {
            if (
              areEmailsValid(item.value) &&
              item.getAttribute("trust") == "analyze"
            ) {
              item.setAttribute("trust", "");
            } else if (!areEmailsValid(item.value)) {
              if (item.id == "abuse_to") {
                item.setAttribute("trust", "analyze");
              } else if (item.value.length != 0) {
                item.setAttribute("trust", "analyze");
              } else {
                item.setAttribute("trust", "");
              }
            }
          }

          const sendButton = document.querySelector("#send_abuse_email");
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

  async function getEmailTemplate(artifact) {
    const inc = document.getElementById("details-container").dataset.eventId;
    const sendButton = document.querySelector("#send_abuse_email");
    sendButton.disabled = false;
    sendButton.textContent = sendButton.dataset.origText;

    try {
      const response = await fetch(`/api/abuse/${inc}?artifact=${artifact}`);
      const msg = await response.json();

      document.querySelector("#sendAbuseEmail #abuse_to").value = msg.to || "";
      document.querySelector("#sendAbuseEmail #abuse_cc").value = msg.cc || "";
      document.querySelector("#sendAbuseEmail #abuse_bcc").value =
        msg.bcc || "";
      document.querySelector("#sendAbuseEmail #abuse_subject").value =
        msg.subject || "";
      document.querySelector("#sendAbuseEmail #abuse_body").value =
        msg.body || "";

      const trustLevel = msg.trust === 1 ? "knowledge" : "analyze";
      document
        .querySelector("#sendAbuseEmail #abuse_to")
        .setAttribute("trust", trustLevel);

      document.querySelector("#sendAbuseEmail").dataset.artifact =
        msg.artifact || "";
      editors["abuse_body"].value(msg.body || "");

      // Show modal
      const abuseModal = new bootstrap.Modal(
        document.getElementById("sendAbuseEmail"),
      );
      abuseModal.show();
      addInputListeners();

      if ("enrichment_raw" in msg) {
        document.querySelector("#abuse_enrichment_names").textContent = (
          msg.enrichment_names || ""
        ).join(" | ");
        document.querySelector("#abuse_enrichment_emails").textContent =
          msg.enrichment_emails || "";
        document.querySelector("#abuse_enrichment_raw").textContent =
          msg.enrichment_raw || "";
        document
          .querySelector("#abuse_tab_enrichment_link")
          .classList.remove("hide");
      } else {
        document
          .querySelector("#abuse_tab_enrichment_link")
          .classList.add("hide");
      }
    } catch (err) {
      console.error("Error fetching email template", err);
    }
  }

  // Fetch EmailForm
  async function fetchEmailForm() {
    const emailFormUrl = document.querySelector("#details-actions-abuse")
      .dataset.url;
    try {
      const response = await fetch(emailFormUrl);
      const data = await response.text();
      document
        .querySelector("#addComment")
        .insertAdjacentHTML("afterend", data);

      editors["abuse_body"] = init_easymde(
        document.getElementById("abuse_body"),
      );

      const abuseModalEl = document.getElementById("sendAbuseEmail");
      const abuseForm = document.getElementById("abuse_email_form");
      const inc = document.getElementById("details-container").dataset.eventId;
      const submit = document.getElementById("send_abuse_email");

      abuseForm.action = `/api/abuse/${inc}`;
      submit.addEventListener("click", () => {
        sendEmail();
      });

      abuseModalEl.addEventListener("shown.bs.modal", () => {
        editors["abuse_body"].codemirror.refresh();
      });
    } catch (err) {
      console.error("Error loading email form", err);
    }
  }
  fetchEmailForm();

  async function addAutoComment() {
    const form = new FormData();
    const email = document.querySelector("#sendAbuseEmail #abuse_to");
    const main_container = document.getElementById("details-container");

    form.append("comment", `Abuse email sent to ${email.value}`);
    form.append("action", "Abuse");
    form.append("incident", main_container.dataset.eventId);

    await add_comment(form);
  }

  async function sendEmail() {
    const inc = document.getElementById("details-container").dataset.eventId;
    const csrftoken = document.querySelector(
      "[name=csrfmiddlewaretoken]",
    ).value;
    const sendButton = document.querySelector("#send_abuse_email");
    sendButton.disabled = true;
    sendButton.textContent = sendButton.dataset.loadingText;

    document.querySelector("#abuse_body").value = editors["abuse_body"].value();
    const form = document.querySelector("#abuse_email_form");
    const formData = new FormData(form);

    try {
      const response = await fetch(`/api/abuse/${inc}`, {
        method: "PUT",
        body: formData,
        headers: {
          "X-CSRFToken": csrftoken,
        },
      });
      const msg = await response.json();

      if (msg.status === "ok") {
        const abuseModal = bootstrap.Modal.getInstance(
          document.getElementById("sendAbuseEmail"),
        );
        abuseModal.hide();
        addAutoComment();
        sendButton.textContent = sendButton.dataset.origText;
        sendButton.disabled = false;
      } else {
        sendButton.textContent = sendButton.dataset.errorText;
      }
    } catch (err) {
      sendButton.textContent = sendButton.dataset.errorText;
    }
  }
});
