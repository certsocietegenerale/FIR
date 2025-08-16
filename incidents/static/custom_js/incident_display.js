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
      statusMap[item.name] = (item.flag || "")
        .replace(/[^a-zA-Z0-9_-]+/g, "")
        .replace(/(.+)/g, "-$1");
    }
  }
  return statusMap;
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
  for (const elem of entries) {
    let name = (elem["name"] || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
    let color = (elem["color"] || "").toLowerCase().replace(/[^a-z0-9#]+/g, "");
    if (name && color) {
      sheet.insertRule(
        `.dynamic-severity-${name} {background-color: ${color}}`,
      );
    }
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
    for (const toedit of document.querySelectorAll(`[data-id="${inc_id}"]`)) {
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

// Small helper: render "${key}" placeholders in a plain string (for loading_count)
function renderPlainTemplate(str, ctx) {
  return str.replace(/\$\{(\w+)\}/g, (_, k) => (k in ctx ? ctx[k] : ""));
}

async function fetchAllPages(firstUrl, showLoadingFn) {
  let url = firstUrl;
  let allResults = [];
  let lastResponseMeta = null;

  while (url != null) {
    const req = await fetch(url, { headers: { Accept: "application/json" } });
    const res = await req.json();
    if (!req.ok) throw res;

    allResults = allResults.concat(res.results || []);
    lastResponseMeta = res;

    // progress callback, if any
    if (showLoadingFn && res.next) {
      const curr_page =
        new URL(res.next, window.location.origin).searchParams.get("page") ||
        "1";
      showLoadingFn({
        page: curr_page,
        total_pages: res.total_pages || "?",
      });
    }

    url = res.next;
  }

  return { results: allResults, meta: lastResponseMeta };
}

async function refresh_display(div) {
  const loading = div.querySelector(".loading");
  const error_p = div.querySelector(".error_message");
  const nts = div.querySelector(".nothing_to_show");

  if (loading) loading.classList.remove("d-none");
  if (error_p) error_p.textContent = "";

  try {
    // 1) Fetch data (single page or all pages)
    let apiUrl = div.dataset.url;
    let data, meta;

    const loading_count = document.querySelector(".loading_count");
    if (loading_count && !loading_count.dataset.template) {
      loading_count.dataset.template = loading_count.textContent;
    }

    if (div.dataset.nopage) {
      const { results, meta: m } = await fetchAllPages(apiUrl, (ctx) => {
        if (loading_count) {
          loading_count.textContent = renderPlainTemplate(
            loading_count.dataset.template,
            ctx,
          );
          loading_count.classList.remove("d-none");
        }
      });
      data = { results };
      meta = m || { total_pages: 1 };
    } else {
      const req = await fetch(apiUrl, {
        headers: { Accept: "application/json" },
      });
      const res = await req.json();
      if (!req.ok) throw res;
      data = res;
      meta = res;
    }

    if (!data.results || data.results.length === 0) {
      // Nothing to show

      if (nts) {
        nts.classList.remove("d-none");
        div.textContent = "";
        div.appendChild(nts);
      } else {
        div.textContent = "";
      }
      return;
    }

    // 2) Preprocess incidents
    const statusMap = await getStatusMap();
    moment.locale(navigator.language);

    const normalized = data.results.map((incident) => {
      const blJoined = (incident.concerned_business_lines || [])
        .map((bl) => String(bl).split(" > ").pop())
        .join(", ");
      const severityClass = String(incident.severity || "")
        .toLowerCase()
        .replace(/[^a-z0-9]/g, "");
      const date = (incident.date || "").split("T")[0] || "";
      const last_comment_date = incident.last_comment_date
        ? moment(incident.last_comment_date, "YYYY-MM-DDTHH:mm").fromNow()
        : "";

      return {
        ...incident,
        business_lines_joined: escapeHtml(blJoined),
        severityClass: escapeHtml(severityClass),
        date: escapeHtml(date),
        last_comment_date: escapeHtml(last_comment_date),
        status_flag: escapeHtml(statusMap[incident.status] || ""),
      };
    });

    // 3) Render with Handlebars
    const templateSource = document.querySelector(
      "#incident-list-template",
    ).innerHTML;
    const template = Handlebars.compile(templateSource);
    const html = template({ results: normalized });

    // Rebuild container: table + optional pagination
    div.innerHTML = html;
    if (error_p) div.appendChild(error_p);
    if (nts) div.appendChild(nts);

    // 4) Add sort chevrons
    let ordering =
      new URL(window.location.href, window.location.origin).searchParams.get(
        "ordering",
      ) || "";
    let order = "up";
    if (ordering.charAt(0) === "-") {
      order = "down";
      ordering = ordering.substring(1);
    }
    for (const elem of div.querySelectorAll("thead a[data-sort]")) {
      if (elem.dataset.sort === ordering) {
        elem.innerHTML += ` <span class="bi bi-chevron-${order}"></span>`;
      }
    }

    // 5) Pagination (if present and not nopage)
    const pagination_template = document.querySelector("#pagination-template");
    if (
      meta &&
      meta.total_pages &&
      meta.total_pages != 1 &&
      pagination_template &&
      !div.dataset.nopage
    ) {
      const ctx = {
        ...meta,
        current_page:
          new URL(div.dataset.url, window.location.origin).searchParams.get(
            "page",
          ) || "1",
      };
      // Use Handlebars for the pagination template too
      const pagTpl = Handlebars.compile(pagination_template.innerHTML);
      const pagHtml = pagTpl(ctx);
      const wrapper = document.createElement("div");
      wrapper.innerHTML = pagHtml;
      div.appendChild(wrapper);

      for (let sub of div.querySelectorAll("a[href='null'], a[href='']")) {
        sub.classList.add("d-none");
      }
    }

    // 6) Re-bind events
    addTableEventListners(div);
  } catch (error) {
    console.error(error);
    if (error_p) {
      error_p.textContent =
        error?.detail || (typeof error === "string" ? error : "Error");
    }
  } finally {
    if (loading) {
      loading.classList.add("d-none");
      div.appendChild(loading);
    }
    const loading_count = document.querySelector(".loading_count");
    if (loading_count) loading_count.classList.add("d-none");
  }
}
