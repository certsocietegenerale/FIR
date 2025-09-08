// Compile Handlebars templates
const observables_template = Handlebars.compile(
  document.querySelector("#yeti-observables-template").innerHTML,
);
const tab_data_template = Handlebars.compile(
  document.querySelector("#yeti-tab-data-template").innerHTML,
);

document.addEventListener("DOMContentLoaded", () => {
  yeti_query_artifacts();
});

function yeti_query_artifacts() {
  let artifacts = document.querySelectorAll("#artifacts .artifacts-table a");
  const searchparams = new URLSearchParams();

  for (let art of artifacts) {
    searchparams.append("observable", art.textContent);
  }

  fetch(`/api/yeti?${searchparams}`, {
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.hasOwnProperty("detail")) {
        throw new Error(data.detail);
      }
      document.querySelector("#tab_threatintel").innerHTML = "";
      render_results(data);
    })
    .catch((err) => console.error("Error querying observables:", err));
}

function render_results(data) {
  // Helper for joining arrays (e.g. multiple sources)
  Handlebars.registerHelper("join", function (array, sep) {
    if (!Array.isArray(array)) {
      return "";
    }
    return array.join(sep);
  });

  // Render the HTML from templates
  document.querySelector("#tab_threatintel").innerHTML =
    observables_template(data);
  document.querySelector("#ti-tab .ti-count").innerHTML =
    tab_data_template(data);

  // Initialize tags input (scoped to tab_threatintel)
  attachTagInputHandlers(document.querySelector("#tab_threatintel"));

  // Send button
  const sendBtn = document.querySelector(".send-to-yeti");
  if (sendBtn) {
    sendBtn.addEventListener("click", function (event) {
      event.preventDefault();

      const observables = [];
      document
        .querySelectorAll("#tab_threatintel .yeti-form tr.observable")
        .forEach((row) => {
          const checkbox = row.querySelector("input[type=checkbox]:checked");
          if (checkbox) {
            const observable = {
              value: row.querySelector(".value").textContent.trim(),
              tags: row
                .querySelector(".tags-hidden")
                .value.split(",")
                .filter(Boolean),
            };
            observables.push(observable);
          }
        });

      if (observables.length > 0) {
        yeti_post_observables(observables);
      }
    });
  }

  // Toggle button (switch read <-> send mode)
  document.querySelectorAll(".toggle-send-to-yeti").forEach((toggleBtn) => {
    toggleBtn.addEventListener("click", function (event) {
      event.preventDefault();
      document
        .querySelector("#tab_threatintel div.yeti-form")
        .classList.toggle("d-none");
      document
        .querySelector("#tab_threatintel div.yeti-read")
        .classList.toggle("d-none");
    });
  });

  // "Select all" checkbox
  document
    .querySelectorAll("#tab_threatintel input.check-all")
    .forEach((checkAll) => {
      checkAll.addEventListener("click", function () {
        const state = this.checked;
        const targetClass = this.dataset.target;
        document
          .querySelectorAll(
            `#tab_threatintel .${targetClass} input[type=checkbox]`,
          )
          .forEach((cb) => {
            cb.checked = state;
          });
      });
    });
}

function yeti_post_observables(observables) {
  const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value;
  const fid = document.querySelector("#yeti-fid").textContent;

  observables.forEach((obs) => {
    obs.fid = fid;
  });

  fetch("/api/yeti", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify({ observables: observables }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.hasOwnProperty("detail")) {
        throw new Error(data.detail);
      }
      yeti_query_artifacts();
    })
    .catch((err) => console.error("Error posting observables:", err));
}
