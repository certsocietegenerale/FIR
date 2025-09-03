document.addEventListener("DOMContentLoaded", function () {
  loadDynamicCSS();

  // Make sure each 'incident_display' comes to life
  for (let div of document.getElementsByClassName("incident_display")) {
    // if there is only one table in the page: retrieve browser URL arguments
    if (document.querySelectorAll(".incident_display").length === 1) {
      updateUrlFromGetParams(div);
    }

    refresh_display(div);
  }
});

function updateUrlFromGetParams(div) {
  // if a "page" arg was provided as query string : update the queried URL to fetch the desired page
  var current_page =
    new URL(window.location.href).searchParams.get("page") || "";
  if (current_page.length != 0 && !isNaN(parseInt(current_page))) {
    let url = new URL(div.dataset.url, window.location.origin);
    url.searchParams.set("page", current_page);
    div.dataset.url = url.pathname + url.search;
  }

  // if an "ordering" arg provided as query string : apply ordering to the queried URL
  var ordering =
    new URL(window.location.href).searchParams.get("ordering") || "";
  if (ordering.length != 0) {
    let url = new URL(div.dataset.url, window.location.origin);
    url.searchParams.set("ordering", ordering);
    div.dataset.url = url.pathname + url.search;
  }

  // if an "q" arg provided as query string : apply search query to the queried URL
  var query = new URL(window.location.href).searchParams.get("q") || "";
  if (query.length != 0) {
    let url = new URL(div.dataset.url, window.location.origin);
    url.searchParams.set("query", query);
    div.dataset.url = url.pathname + url.search;
  }
}

function addTableEventListners(div) {
  // Change sort when clicking on a column title
  for (let sub of div.querySelector("thead").querySelectorAll("a[data-sort]")) {
    sub.addEventListener("click", function (event) {
      let div_url = new URL(div.dataset.url, window.location.origin);
      let ordering = div_url.searchParams.get("ordering");

      if (ordering == event.target.dataset.sort) {
        ordering = "-" + ordering;
      } else if ("-" + ordering == event.target.dataset.sort) {
        ordering = ordering.substring(1);
      } else {
        ordering = event.target.dataset.sort;
      }

      // if there is only one table in the page: change web browser URL
      if (document.querySelectorAll(".incident_display").length === 1) {
        let this_url = new URL(window.location.href);
        this_url.searchParams.set("ordering", ordering);
        window.history.pushState({}, "", this_url.toString());
      }

      // change URL queried
      div_url.searchParams.set("ordering", ordering);
      div.dataset.url = div_url.pathname + div_url.search;

      //refresh div
      refresh_display(div);
      event.preventDefault();
    });
  }

  // Change page when clicking on a pagination link
  for (let sub of div.querySelectorAll("a.paginate")) {
    sub.addEventListener("click", function (event) {
      // update browser query string
      let href = event.target.href;
      if (typeof href == "undefined") {
        // handle cases when user clicks on the <i> element in the link
        href = event.target.closest(".paginate").href;
      }
      let this_url = new URL(window.location.href);
      let new_page =
        new URL(href, window.location.origin).searchParams.get("page") || "";
      if (new_page.length != 0 && !isNaN(parseInt(new_page))) {
        this_url.searchParams.set("page", new_page);
      } else if (new_page.length == 0) {
        this_url.searchParams.delete("page");
      }
      window.history.pushState({}, "", this_url.toString());

      // refresh div
      let url = new URL(href);
      div.dataset.url = url.pathname + url.search;
      refresh_display(div);
      event.preventDefault();
    });
  }

  // Star/Unstar incidents
  for (let sub of div.querySelectorAll("a[data-id]")) {
    sub.addEventListener("click", function (event) {
      toggle_star(event.target);
      event.preventDefault();
    });
  }
}

function escapeHtml(html) {
  var text = document.createTextNode(html);
  var p = document.createElement("p");
  p.appendChild(text);
  return p.innerHTML;
}

let statusMap = null;

async function getStatusMap() {
  if (!statusMap) {
    let url = "/api/statuses";
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

    // Convert array to map for fast lookup
    statusMap = {};
    for (const item of entries) {
      console.log(item.flag);
      statusMap[item.name] = (item.flag || "")
        .replace(/[^a-zA-Z0-9_-]+/g, "")
        .replace(/(.+)/g, "-$1");
    }
  }
  return statusMap;
}

// parse a templated string without allowing arbitrary code execution
// Inspired from https://stackoverflow.com/a/59084440
async function parseStringTemplate(str, obj) {
  if (!str) {
    return str;
  }
  let parts = str.split(/\$\{(?!\d)[\w\?\:_\|-]*\}/); // static text
  let args = str.match(/[^{\}]+(?=})/g) || []; // parts to replace

  // perform replacement
  let parameters = await Promise.all(
    args.map(async (argument_with_params) => {
      argument = argument_with_params.split("?")[0].split("|")[0]; // allow custom-made strings manipulation: lower, upper, etc

      if (obj[argument] === undefined) {
        return "";
      } else if (Array.isArray(obj[argument])) {
        // arrays: join values with ", "
        return escapeHtml(obj[argument].join(", "));
      } else if (
        typeof obj[argument] == "boolean" &&
        // booleans: allow to display specific texts depending on the boolean value.
        argument_with_params.split("?").length == 2
      ) {
        let iftrue = argument_with_params.split("?")[1].split(":")[0];
        let iffalse = argument_with_params.split(":")[1];
        return escapeHtml(obj[argument] ? iftrue : iffalse);
      } else {
        // strings: allow custom-made text manipulation
        if (
          typeof obj[argument] == "string" &&
          argument_with_params.split("|").length == 2
        ) {
          let op = argument_with_params.split("|")[1];
          if (op == "lower") {
            return escapeHtml(obj[argument].toLowerCase());
          } else if (op == "upper") {
            return escapeHtml(obj[argument].toUpperCase());
          } else if (op == "flag") {
            const map = await getStatusMap();
            return escapeHtml(map[obj[argument]] || "");
          }
        }
        return escapeHtml(obj[argument]);
      }
    }),
  );

  // reassemble strings
  return String.raw({ raw: parts }, ...parameters);
}

// create an HTML element and add classes of to it based on a template
function createElementFromTemplate(elemToCreate, template) {
  const elem = document.createElement(elemToCreate);
  if (typeof template == "string") {
    template = document.querySelector(template);
  }
  for (let c of template.classList) {
    if (c != "d-none") {
      elem.classList.add(c);
    }
  }

  return elem;
}

async function loadDynamicCSS() {
  let url = "/api/severities";
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

  const sheet = document.querySelector("link[rel=stylesheet]").sheet;
  for (elem of entries) {
    let name = elem["name"].toLowerCase().replace(/[^a-z0-9]+/g, "");
    let color = elem["color"].toLowerCase().replace(/[^a-z0-9#]+/g, "");
    sheet.insertRule(`.dynamic-severity-${name} {background-color: ${color}}`);
  }
}

async function toggle_star(target) {
  if (typeof target.dataset.id == "undefined") {
    target = target.closest("a[data-id]");
  }
  let classes = target.querySelector("i.star").classList;
  let inc_id = parseInt(target.dataset.id);
  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");
  if (isNaN(inc_id) || !csrftoken) {
    return;
  }
  var response = await fetch(`/api/incidents/${inc_id}`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
      "Content-type": "application/json",
    },
    body: JSON.stringify({ is_starred: !classes.contains("bi-star-fill") }),
  });

  if (response.status != 200) {
    console.error(await response.json());
  } else {
    let inc_id = parseInt(target.dataset.id);
    for (toedit of document.querySelectorAll(`[data-id="${inc_id}"]`)) {
      if (classes.contains("bi-star-fill")) {
        toedit.querySelector("i.star").classList.remove("bi-star-fill");
        toedit.querySelector("i.star").classList.add("bi-star");
      } else {
        toedit.querySelector("i.star").classList.remove("bi-star");
        toedit.querySelector("i.star").classList.add("bi-star-fill");
      }
    }
    if (document.getElementById("starred_incidents")) {
      refresh_display(document.getElementById("starred_incidents"));
    }
  }
}

async function refresh_display(div) {
  const loading = div.querySelector(".loading");
  const error_p = div.querySelector(".error_message");

  if (loading) {
    loading.classList.remove("d-none");
  }
  if (error_p) {
    error_p.textContent = "";
  }
  var url = div.dataset.url;
  var request = await fetch(url, {
    headers: { Accept: "application/json" },
  });
  var response = await request.json();
  if (request.status != 200) {
    console.error(response);
    if (loading) {
      loading.classList.add("d-none");
    }
    if (error_p) {
      if ("detail" in response) {
        error_p.textContent = response["detail"];
      } else {
        error_p.textContent = response;
      }
    }
    return;
  }

  if (response["results"].length === 0) {
    let nts = div.querySelector(".nothing_to_show");
    nts.classList.remove("d-none");
    div.textContent = "";
    div.appendChild(nts);
    if (loading) {
      loading.classList.add("d-none");
      div.appendChild(loading);
    }
    return;
  }

  const thead_template = document.querySelector(
    "#incident-list-template thead",
  );
  const tbody_template = document.querySelector(
    "#incident-list-template tbody tr",
  );

  const thead = thead_template.cloneNode(true);
  const table = createElementFromTemplate("table", "#incident-list-template");
  const tbody = createElementFromTemplate(
    "tbody",
    "#incident-list-template tbody",
  );
  var loading_count = document.querySelector(".loading_count");
  if (loading_count && !loading_count.dataset.template) {
    loading_count.dataset.template = loading_count.textContent;
  }

  while (url != null) {
    for (let entry of response["results"]) {
      const tr = createElementFromTemplate(
        "tr",
        "#incident-list-template tbody tr",
      );

      // remove path from business lines
      for (i in entry["concerned_business_lines"]) {
        entry["concerned_business_lines"][i] = entry[
          "concerned_business_lines"
        ][i]
          .split(" > ")
          .pop();
      }
      // format incident date
      entry["date"] = entry["date"].split("T")[0];

      // format last action date
      moment.locale(navigator.language);
      entry["last_comment_date"] = moment(
        entry["last_comment_date"],
        "YYYY-MM-DD HH:mm",
      ).fromNow();

      // parse string templates in td class
      if (tr.getAttribute("class")) {
        tr.setAttribute(
          "class",
          await parseStringTemplate(tr.getAttribute("class"), entry),
        );
      }

      for (let td_template of tbody_template.children) {
        const td = createElementFromTemplate("td", td_template);
        // parse string template
        td.innerHTML = await parseStringTemplate(td_template.innerHTML, entry);

        // hide elements if user is viewer
        if (td.querySelector(".hide-if-viewer") && !entry["can_edit"]) {
          td.querySelector(".hide-if-viewer").classList.add("d-none");
        }
        // add link to the incident/event if requested
        if (td.querySelector(".edit-button") || td.querySelector(".add-link")) {
          if (entry["is_incident"]) {
            td.querySelector("a").href = "/incidents/" + entry["id"];
          } else {
            td.querySelector("a").href = "/events/" + entry["id"];
          }
          if (td.querySelector(".edit-button")) {
            td.querySelector("a").href += "/edit";
          }
        }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    if (div.dataset.nopage && response["next"]) {
      url = response["next"];
      request = await fetch(url, {
        headers: { Accept: "application/json" },
      });
      response = await request.json();
      if (request.status != 200) {
        console.error(response);
        return;
      }

      // Loading indicator
      if (loading_count) {
        let curr_page = new URL(url).searchParams.get("page") || "1";
        loading_count.textContent = await parseStringTemplate(
          loading_count.dataset.template,
          { page: curr_page, total_pages: response["total_pages"] },
        );
        loading_count.classList.remove("d-none");
      }
    } else {
      url = null;
    }
  }

  let ordering =
    new URL(window.location.href, window.location.origin).searchParams.get(
      "ordering",
    ) || "";
  let order = "up";
  if (ordering.charAt(0) == "-") {
    order = "down";
    ordering = ordering.substring(1);
  }
  for (elem of thead.querySelectorAll("a[data-sort]")) {
    if (elem.dataset.sort == ordering) {
      elem.innerHTML += ` <span class="bi bi-chevron-${order}"></i>`;
    }
  }
  table.appendChild(thead);
  table.appendChild(tbody);

  let nts = div.querySelector(".nothing_to_show"); // preserve div "nothing to show" when rebuilding table
  if (!nts.classList.contains("d-none")) {
    nts.classList.add("d-none");
  }
  div.innerHTML = "";
  div.appendChild(table);
  div.appendChild(nts);
  if (loading) {
    loading.classList.add("d-none");
    div.appendChild(loading);
  }
  const pagination_template = document.querySelector("#pagination-template");
  if (
    response["total_pages"] != 1 &&
    pagination_template &&
    !div.dataset.nopage
  ) {
    response["current_page"] =
      new URL(div.dataset.url, window.location.origin).searchParams.get(
        "page",
      ) || "1";
    const pagination = document.createElement("div");
    pagination.innerHTML += await parseStringTemplate(
      pagination_template.innerHTML,
      response,
    );
    div.appendChild(pagination);
    for (let sub of div.querySelectorAll("a[href=null]")) {
      sub.classList.add("d-none");
    }
  }
  addTableEventListners(div);
}
