document.addEventListener("DOMContentLoaded", (event) => {
  yeti_query_artifacts();
});

async function yeti_query_artifacts() {
  const tab_threatintel = document.getElementById("tab_threatintel");
  let artifacts = document.querySelectorAll(".artifacts-table a");
  const searchparams = new URLSearchParams();

  for (let art of artifacts) {
    searchparams.append("observable", art.textContent);
  }
  const query = await fetch(`/api/yeti?${searchparams}`, {
    headers: { accept: "application/json" },
  });
  const response = await query.json();

  if (query.status != 200) {
    console.error(response);
    tab_threatintel.textContent = response.detail;
  } else {
    await render_yeti_table(response);
  }
}

async function render_yeti_table(response) {
  const tab_threatintel = document.getElementById("tab_threatintel");
  const read_elem_template = createElementFromTemplate("div", ".yeti-matches");
  read_elem_template.innerHTML = document.querySelector(
    ".yeti-matches .yeti-read",
  ).innerHTML;

  // update count
  const count_elem = document.getElementById("ti-count");
  const count_template = document.getElementById("yeti-tab-data-template");

  count_elem.innerHTML = await parseStringTemplate(
    count_template.innerHTML,
    response,
  );
  // copy template
  tab_threatintel.innerHTML = read_elem_template.outerHTML;

  // then edit it in place
  const known_tr_template = document.querySelector(
    "#tab_threatintel .known-template",
  );
  const unknown_tr_template = document.querySelector(
    "#tab_threatintel .unknown-template",
  );
  const known_table = document.querySelector("#tab_threatintel .known");
  const unknown_table = document.querySelector("#tab_threatintel .unknown");

  known_tr_template.remove();
  for (const known of response["known"]) {
    known_table.innerHTML += await parseStringTemplate(
      known_tr_template.innerHTML,
      known,
    );
  }
  if (response["known"].length === 0) {
    known_table.classList.add("d-none");
  }
  // display tags as multiple
  for (const tags of document.querySelectorAll(
    "#tab_threatintel .badge-primary",
  )) {
    tags.outerHTML = tags.outerHTML.replaceAll(
      ", ",
      '</span><span class="badge badge-primary me-1">',
    );
  }

  unknown_tr_template.remove();
  for (const unknown of response["unknown"]) {
    unknown_table.innerHTML += await parseStringTemplate(
      unknown_tr_template.innerHTML,
      { item: unknown },
    );
  }
  if (response["unknown"].length === 0) {
    unknown_table.classList.add("d-none");
  }

  // button "send to yeti": replace content by inputs
  document
    .querySelector("#tab_threatintel .toggle-send-to-yeti")
    .addEventListener("click", (evt) => {
      evt.preventDefault();
      render_yeti_form(response);
    });
}

async function render_yeti_form(response) {
  const tab_threatintel = document.querySelector("#tab_threatintel .widget");
  // copy template
  const form_elem_template = createElementFromTemplate("div", ".yeti-matches");
  form_elem_template.innerHTML = document.querySelector(
    ".yeti-matches .yeti-form",
  ).innerHTML;
  tab_threatintel.innerHTML = form_elem_template.innerHTML;

  // then edit it in place
  const known_tr_template = document.querySelector(
    "#tab_threatintel .known-template",
  );
  const unknown_tr_template = document.querySelector(
    "#tab_threatintel .unknown-template",
  );
  const known_table = document.querySelector("#tab_threatintel .known");
  const unknown_table = document.querySelector("#tab_threatintel .unknown");

  known_tr_template.remove();
  for (const known of response["known"]) {
    known_table.insertAdjacentHTML(
      "beforeend",
      await parseStringTemplate(known_tr_template.innerHTML, known),
    );
    const rows = known_table.querySelectorAll("tr");
    const lastRow = rows[rows.length - 1];
    const hidden = lastRow.querySelector(".tags-hidden");
    const tagBox = lastRow.querySelector(".tag-box");
    renderTags(known.tags, hidden, tagBox);
  }
  if (response["known"].length === 0) {
    known_table.classList.add("d-none");
  }

  unknown_tr_template.remove();
  for (const unknown of response["unknown"]) {
    unknown_table.innerHTML += await parseStringTemplate(
      unknown_tr_template.innerHTML,
      { item: unknown },
    );
  }
  if (response["unknown"].length === 0) {
    unknown_table.classList.add("d-none");
  }

  // handle "Select all" checkbox
  for (const chkbox of document.querySelectorAll(
    "#tab_threatintel input[type=checkbox]",
  )) {
    chkbox.addEventListener("change", (evt) => {
      if (evt.target.classList.contains("check-all")) {
        for (const chkbox2 of document.querySelectorAll(
          "#tab_threatintel input[type=checkbox]",
        )) {
          chkbox2.checked = true;
        }
      } else if (!evt.target.checked) {
        document.querySelector("#tab_threatintel .check-all").checked = false;
      }
    });
  }

  // Tags input handling
  for (const input of document.querySelectorAll(
    "#tab_threatintel .tagsinput",
  )) {
    const hidden = input.parentElement.querySelector(".tags-hidden");
    const tagBox = input.parentElement.querySelector(".tag-box");

    input.addEventListener("keydown", (e) => {
      const tags = [...tagBox.querySelectorAll("span")].map(
        (x) => x.textContent,
      );
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        const value = input.value.trim();
        if (value && !tags.includes(value)) {
          if (input.classList.contains("tags-all")) {
            renderTagsOnAllInputs(input, value);
          } else {
            tags.push(value);
            input.value = "";
            renderTags(tags, hidden, tagBox);
            hidden.value = tags.join(",");
          }
        }
      }
    });
  }

  // cancel button
  document
    .querySelector("#tab_threatintel .toggle-yeti-cancel")
    .addEventListener("click", (evt) => {
      evt.preventDefault();
      render_yeti_table(response);
    });

  // send to yeti
  document
    .querySelector("#tab_threatintel .send-to-yeti")
    .addEventListener("click", (evt) => {
      evt.preventDefault();
      send_to_yeti();
    });
}

async function send_to_yeti() {
  observables = [];
  const fid = document.querySelector("#tab_threatintel .fid").textContent;

  for (const tr of document.querySelectorAll("#tab_threatintel tr")) {
    const tds = tr.querySelectorAll("td");
    if (
      tds.length === 0 ||
      !tds[0].querySelector("input[type=checkbox]") ||
      tds[1].querySelector("strong")
    ) {
      // header or title rows
      continue;
    }
    if (tds[0].querySelector("input[type=checkbox]").checked) {
      const tags = [...tds[2].querySelectorAll("span")].map(
        (x) => x.textContent,
      );
      observables.push({ value: tds[1].textContent, tags: tags, fid: fid });
    }
  }

  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
  const query = await fetch(`/api/yeti`, {
    headers: { accept: "application/json" },
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
      "Content-type": "application/json",
    },
    body: JSON.stringify({ observables: observables }),
  });
  const response = await query.json();

  if (query.status != 200) {
    console.error(response);
    tab_threatintel.textContent = response.detail;
  } else {
    await yeti_query_artifacts();
  }
}

function renderTags(tags, hidden, tagBox) {
  tagBox.innerHTML = "";
  tags.forEach((tag, i) => {
    const pill = document.createElement("div");
    pill.className = "tag-pill";

    const span = document.createElement("span");
    span.textContent = tag;

    const remove = document.createElement("button");
    remove.textContent = "×";
    remove.addEventListener("click", () => {
      tags.splice(i, 1);
      renderTags(tags, hidden, tagBox);
      hidden.value = tags.join(",");
    });

    pill.appendChild(span);
    pill.appendChild(remove);
    tagBox.appendChild(pill);
  });
}

function renderTagsOnAllInputs(input, value) {
  for (let elem of document.querySelectorAll("#tab_threatintel .tagsinput")) {
    if (elem == input) {
      continue;
    }
    const hidden = elem.parentElement.querySelector(".tags-hidden");
    const tagBox = elem.parentElement.querySelector(".tag-box");
    const tags = [...tagBox.querySelectorAll("span")].map((x) => x.textContent);
    if (!tags.includes(value)) {
      tags.push(value);
      renderTags(tags, hidden, tagBox);
      hidden.value = tags.join(",");
    }
  }
  input.value = "";
}
