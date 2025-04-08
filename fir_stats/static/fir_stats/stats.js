const color = d3
  .scaleOrdinal() // The different colors used to generate graphs
  .range([
    "#e60028",
    "#873d67",
    "#3e7eaf",
    "#d55a39",
    "#1a9656",
    "#666666",
    "#d24b28",
    "#0ac8dc",
    "#82379b",
    "#a50041",
    "#a0af00",
    "#ffa02d",
    "#c30082",
    "#00a550",
    "#64a0c8",
    "#c864cd",
    "#dc4b69",
    "#9be173",
    "#ffb414",
    "#e1648c",
    "#9178d2",
    "#6e3c28",
  ]);

document.addEventListener("DOMContentLoaded", function () {
  // Quarterly stats
  const blSelector = document.getElementById("bl-select");
  const variationTable = document.getElementById("variation-table");

  if (blSelector) {
    blSelector.addEventListener("change", (event) => {
      let urlPieces = [
        location.protocol,
        "//",
        location.host,
        location.pathname,
        "?bl=",
        encodeURI(event.target.value),
      ];
      window.location.href = urlPieces.join("");
    });
  }

  if (variationTable) {
    generate_variation_table(variationTable);
  }

  // Sandbox, Attributes
  const fromDate = document.getElementById("from-date");
  const toDate = document.getElementById("to-date");
  if (fromDate) {
    var date = new Date();
    if (!Date.parse(fromDate.value)) {
      date.setDate(date.getDate() - 365); // by default, suggest date 1 year ago
      fromDate.value = date.toISOString(true).substring(0, 10);
    }
  }
  if (toDate) {
    var date = new Date();
    if (!Date.parse(toDate.value)) {
      toDate.value = date.toISOString(true).substring(0, 10);
    }
  }
  const attrCheckbox = document.querySelectorAll(
    'input[name="attribute_selection"]',
  );
  const goButton = document.getElementById("refresh-stats-button");
  if (goButton) {
    goButton.addEventListener("click", (event) => {
      refresh_stats();
      return false;
    });

    // Attributes page: only elements having the same unit can be selected together
    attrCheckbox.forEach((item) => {
      item.addEventListener("change", (event) => {
        enableDisableAttributes(event);
        return false;
      });
    });

    // attribute page: disable "selected attribute count" unit on page load
    if (document.getElementById("unit")) {
      enableDisableAttributes();
    }
  } else {
    // other pages
    refresh_stats();
  }
  //Load incident table
  for (let link of document.querySelectorAll(".load_all_incidents")) {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      load_all_incidents();
    });
  }
  // CSV Exports
  for (let link of document.querySelectorAll(".export-link")) {
    link.addEventListener("click", (event) => {
      if (link.dataset.type == "xls") {
        return ExcellentExport.excel(link, "stats_incident_export", "FIR");
      } else if (link.dataset.type == "csv") {
        return ExcellentExport.csv(link, "stats_incident_export", ",");
      } else if (link.dataset.type == "tsv") {
        return ExcellentExport.csv(link, "stats_incident_export", "\t");
      }
    });
  }
});
async function load_all_incidents() {
  if (!document.querySelector("#stats_incident_export")) {
    let div = document.querySelector(".stats_incident_display");
    div.classList.add("incident_display");
    updateUrlFromGetParams(div);
    const date_filter = getDateFilterArg(div);
    if (!date_filter) {
      return false;
    }
    const other_filters = getOtherFiltersArg();
    div.dataset.url = `${div.dataset.url}&${date_filter}&${other_filters}`;
    const load_all_incidents = document.querySelector(".load_all_incidents");
    if (load_all_incidents) {
      load_all_incidents.classList.add("d-none");
    }
    await refresh_display(div);
    const incident_table = div.querySelector("table");
    if (!incident_table) {
      // no incident found
      return false;
    }
    incident_table.id = "stats_incident_export";
    const export_links = document.querySelector(".export_links");
    if (export_links) {
      export_links.classList.remove("d-none");
    }
  }
}

// Attributes page: set incident count
async function setIncidentCount(div, unit, with_attribute_only = false) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const other_filters = getOtherFiltersArg(unit, with_attribute_only);
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (response.status != 200) {
    response = { incidents: 0 };
  } else {
    response = await response.json();
  }

  div.textContent = response[unit + "s"];
}

// Enable/disable attributes when they are not the same unit
function enableDisableAttributes(event) {
  const checkedElems = document.querySelectorAll(
    'input[name="attribute_selection"]:checked',
  );
  const allElems = document.querySelectorAll(
    'input[name="attribute_selection"]',
  );

  const unit_field = document.getElementById("unit");

  if (event && event.target.checked) {
    const unit = event.target.dataset.unit;
    allElems.forEach((elem) => {
      if (elem.dataset.unit != unit) {
        elem.disabled = true;
        elem.parentNode.setAttribute(
          "title",
          `This attribute can't be selected because it doesn't have the same unit as '${event.target.value}'`,
        );
        elem.parentNode.setAttribute("data-bs-toggle", "tooltip");
      }
    });
    // enable "count selected attributes"
    unit_field
      .querySelector("option[value=attribute]")
      .removeAttribute("disabled");
  } else if (checkedElems.length === 0) {
    allElems.forEach((elem) => {
      elem.disabled = false;
      elem.parentNode.removeAttribute("title");
      elem.parentNode.removeAttribute("data-bs-original-title");
      elem.parentNode.removeAttribute("data-bs-toggle");
    });

    // disable "count selected attributes"
    unit_field
      .querySelector("option[value=attribute]")
      .setAttribute("disabled", "disabled");
    if (unit.value == "attribute") {
      unit_field.value = "incident";
      unit_field.dispatchEvent(new Event("change"));
    }
  }
  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]',
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
  );
}

function refresh_stats() {
  for (let div of document.querySelectorAll(".d3-lines-chart")) {
    div.innerHTML = "";
    generate_line_chart(div);
  }
  for (let div of document.querySelectorAll(".d3-donut-chart")) {
    div.innerHTML = "";
    generate_donut_chart(div);
  }
  for (let div of document.querySelectorAll(".d3-bars-chart")) {
    div.innerHTML = "";
    generate_bar_chart(div);
  }
  for (let div of document.querySelectorAll(".d3-multiple-donut-chart")) {
    div.innerHTML = "";
    generate_multiple_donut_chart(div);
  }

  for (let div of document.querySelectorAll(".quarterly-table")) {
    div.innerHTML = "";
    generate_stats_table(div);
  }
  // Specific attribute page
  const incCount = document.getElementById("inc_count");
  const incAttributesCount = document.getElementById(
    "inc_with_attribute_count",
  );
  const attributesCount = document.getElementById("attributes_count");

  if (incCount) {
    setIncidentCount(incCount, "incident");
  }
  if (incAttributesCount) {
    setIncidentCount(incAttributesCount, "incident", true);
  }
  if (attributesCount) {
    const checkedElems = document.querySelectorAll(
      'input[name="attribute_selection"]:checked',
    );
    if (checkedElems.length === 0) {
      attributesCount.textContent = "N/A";
    } else {
      setIncidentCount(attributesCount, "attribute");
    }
  }
  // Incident table list: reset when clicking on "go"
  for (let div of document.querySelectorAll(".stats_incident_display")) {
    div.classList.remove("incident_display");
    for (let e of div.querySelectorAll("table")) {
      e.parentNode.removeChild(e);
    }
    for (let e of div.querySelectorAll(".nothing_to_show")) {
      e.classList.add("d-none");
    }
    for (let e of div.querySelectorAll(".loading")) {
      e.classList.add("d-none");
    }
  }
  // CSV export: reset when clicking on "go"
  const export_links = document.querySelector(".export_links");
  if (export_links) {
    export_links.classList.add("d-none");
  }
  const load_all_incidents = document.querySelector(".load_all_incidents");
  if (load_all_incidents) {
    load_all_incidents.classList.remove("d-none");
  }
}

async function generate_stats_table(div) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const other_filters = getOtherFiltersArg();
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (response.status != 200) {
    response = {};
  } else {
    response = await response.json();
  }

  const tbody = document.createElement("tbody");
  const th_template = document.createElement("th");
  const tr_template = document.createElement("tr");
  const td_template = document.createElement("td");
  let th_applied = false;

  for (k in response) {
    response[k] = fillGapsIfKeyIsDate(response[k], div);
    if (!th_applied) {
      th_applied = true;
      tr = tr_template.cloneNode(true);

      th = th_template.cloneNode(true);
      th.textContent = div.dataset.title;
      tr.appendChild(th);
      for (k2 in response[k]) {
        th = th_template.cloneNode(true);

        const parseDate = d3.timeParse(getDateFormat(div));
        th.textContent = parseDate(k2).toLocaleString(navigator.language, {
          month: "short",
        });
        tr.appendChild(th);
      }
      th = th_template.cloneNode(true);
      th.textContent = "Total";
      tr.appendChild(th);
      tbody.appendChild(tr);
    }
    let total = 0;
    for (k2 in response[k]) {
      total += parseInt(response[k][k2]) || 0;
    }
    response[k]["total"] = total;

    tr = tr_template.cloneNode(true);

    td = td_template.cloneNode(true);
    td.textContent = k;
    tr.appendChild(td);
    for (k2 in response[k]) {
      td = td_template.cloneNode(true);
      td.textContent = response[k][k2];
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  div.appendChild(tbody);
}

async function generate_variation_table(div) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const compare_date_filter = getDateFilterArg(div, true);
  const other_filters = getOtherFiltersArg();
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (response.status != 200) {
    response = {};
  } else {
    response = await response.json();
  }
  const compare_response = await (
    await fetch(`${div.dataset.url}&${compare_date_filter}&${other_filters}`, {
      headers: { Accept: "application/json" },
    })
  ).json();

  if (Object.keys(response).length) {
    response = fillGapsIfKeyIsDate(response, div);
  }

  const tblBody = document.createElement("tbody");
  const trHeaders = document.createElement("tr");
  const trNew = document.createElement("tr");
  const trVar = document.createElement("tr");
  const trIcon = document.createElement("tr");

  // Get all categories present in response OR compare_response
  keys = Object.assign({}, response);
  keys = Object.keys(Object.assign(keys, compare_response));
  keys.push("Total");
  response["Total"] = Object.values(response).reduce((p, a) => p + a, 0);
  compare_response["Total"] = Object.values(compare_response).reduce(
    (p, a) => p + a,
    0,
  );

  var end_date = new Date(
    new URLSearchParams(date_filter).get("created_before"),
  );
  var compare_end_date = new Date(
    new URLSearchParams(compare_date_filter).get("created_before"),
  );
  const quarter = Math.floor((end_date.getMonth() - 1) / 3) + 1;
  const compare_quarter = Math.floor((compare_end_date.getMonth() - 1) / 3) + 1;

  // Add legends on the left
  trHeaders.appendChild(document.createElement("th"));
  trIcon.appendChild(document.createElement("th"));

  newDescription = document.createElement("th");
  newDescription.textContent = `Last quarter (Q${quarter}-${end_date.getFullYear()})`;
  newDescription.classList.add("text-end");
  trNew.appendChild(newDescription);

  varDescription = document.createElement("th");
  varDescription.textContent = `Variation from Q${compare_quarter}-${compare_end_date.getFullYear()}`;
  varDescription.classList.add("text-end");
  trVar.appendChild(varDescription);

  for (k of keys) {
    var cur = response[k] || 0;
    var prev = compare_response[k] || 0;
    var diff = cur - prev;

    let cellHeader = document.createElement("th");
    cellHeader.textContent = k;
    cellHeader.classList.add("text-center");
    trHeaders.appendChild(cellHeader);

    let cellNew = document.createElement("td");
    cellNew.textContent = cur;
    cellNew.classList.add("text-center");
    trNew.appendChild(cellNew);

    let cellVar = document.createElement("td");
    cellVar.textContent = diff;
    cellVar.classList.add("text-center");
    trVar.appendChild(cellVar);

    let cellIcon = document.createElement("td");
    cellIcon.classList.add("text-center");
    if (diff < 0) {
      cellIcon.innerHTML = '<i class="bi bi-dash"></i>';
    } else if (diff > 0) {
      cellIcon.innerHTML = '<i class="bi bi-plus"></i>';
    } else {
      cellIcon.textContent = "=";
    }
    trIcon.appendChild(cellIcon);
  }

  tblBody.appendChild(trHeaders);
  tblBody.appendChild(trNew);
  tblBody.appendChild(trVar);
  tblBody.appendChild(trIcon);
  div.appendChild(tblBody);
}

async function generate_multiple_donut_chart(div) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const other_filters = getOtherFiltersArg();
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );

  if (Object.keys(response).length) {
    response = fillGapsIfKeyIsDate(response, div);
  }

  if (response.status != 200) {
    response = {};
  } else {
    response = await response.json();
  }
  var margin = { top: 20, right: 20, bottom: 30, left: 40 },
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

  var arc = d3
    .arc()
    .outerRadius(div.dataset.outerRadius)
    .innerRadius(div.dataset.innerRadius);

  var pie = d3
    .pie()
    .sort(null)
    .value(function (d) {
      return d.value;
    });

  // Convert the recieved response to a javascript array usable by D3
  var data = [];
  for (k in response) {
    data.push(Object.assign({ entry: k }, response[k]));
  }
  // Define the color scale based on the subkeys
  subkeys = [
    ...new Set(
      Object.values(response)
        .map((x) => Object.keys(x))
        .flat(),
    ),
  ];
  color.domain(subkeys);

  data.forEach(function (d) {
    total = 0;
    for (var index in d) {
      total += d[index];
    }
    d.entries = color.domain().map(function (name) {
      return { name: name, value: +d[name] || 0 };
    });
  });

  // Create an SVG element for each entry in the data
  var svg = d3
    .select(div)
    .selectAll(".pie")
    .data(data)
    .enter()
    .append("svg")
    .attr("class", "m-2") // set margin between each SVG
    .attr("width", div.dataset.outerRadius * 2)
    .attr("height", div.dataset.outerRadius * 2)
    .append("g")
    .attr(
      "transform",
      "translate(" +
        div.dataset.outerRadius +
        "," +
        div.dataset.outerRadius +
        ")",
    );

  // Create groups for each arc (slice) within the pie chart
  var g = svg
    .selectAll(".arc")
    .data(function (d) {
      return pie(d.entries);
    })
    .enter()
    .append("g");

  // Append a path element (for each slice) inside the group
  g.append("path")
    .attr("class", "arc")
    .attr("d", arc)
    .style("fill", function (d) {
      return color(d.data.name);
    })
    .attr("title", function (d) {
      return `${d.data.name}: \n${d.data.value}`; // Append a text element (tooltip) to display the value of each slice
    })
    .attr("data-bs-toggle", "tooltip");

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]',
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
  );

  // Append text to display the entry name (label for the donut chart)
  svg
    .append("text")
    .attr("dy", ".35em")
    .style("text-anchor", "middle")
    .style("fill", "currentColor")
    .text(function (d) {
      return d.entry;
    });
}

async function generate_bar_chart(div) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const other_filters = getOtherFiltersArg();
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (response.status != 200) {
    response = {};
  } else {
    response = await response.json();
  }

  var response_compare = {};
  if (div.dataset.compare) {
    const compare_date_filter = getDateFilterArg(div, true);
    response_compare = await (
      await fetch(
        `${div.dataset.url}&${compare_date_filter}&${other_filters}`,
        {
          headers: { Accept: "application/json" },
        },
      )
    ).json();
  }

  if (Object.keys(response).length) {
    response = fillGapsIfKeyIsDate(response, div);
  }

  var margin = { top: 20, right: 20, bottom: 30, left: 40 },
    width = div.dataset.width - margin.left - margin.right,
    height = div.dataset.height - margin.top - margin.bottom;

  const margin_between_bars = 10;

  // True if he bars should contain stacked values
  is_not_stacked = Object.values(response).some((el) => Number.isInteger(el));

  // Calculate how many items fit in one column of the legend
  var legend_per_col = Math.floor(height / 20);
  legend = Object.keys(response).length - 1;

  // Convert the recieved response to a javascript array usable by D3
  var data = [];
  for (k in response) {
    data.push(Object.assign({ entry: k }, response[k]));
  }

  // Adjust the chart size based on the number of legend items
  width =
    width +
    margin.left +
    margin.right -
    120 * Math.floor(legend / legend_per_col);

  // Create the SVG containing the bars
  var svg = d3
    .select(div)
    .append("svg")
    .attr("width", width)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  if (is_not_stacked) {
    // if entry is not stacked: transform each entry of data variable to create a single bar
    data.forEach(function (d) {
      d[d["entry"]] = response[d["entry"]];
      d.values = [
        {
          name: d["entry"],
          y0: 0,
          y1: response[d["entry"]],
          compare: response_compare[d["entry"]],
        },
      ];
      d.total = response[d["entry"]];
    });
    color.domain([]);
  } else {
    // Define the color scale based on the subkeys
    subkeys = [
      ...new Set(
        Object.values(response)
          .map((x) => Object.keys(x))
          .flat(),
      ),
    ];
    color.domain(subkeys);

    // For each data entry, calculate the stacking values for each group
    data.forEach(function (d) {
      var y0 = 0;
      d.values = color.domain().map(function (name) {
        // Get the entry to compare against
        let compare_entry = undefined;
        if (response_compare.hasOwnProperty(d["entry"])) {
          compare_entry = response_compare[d["entry"]][name];
        }
        return {
          name: name,
          y0: y0,
          y1: (y0 += +d[name] || 0),
          compare: compare_entry,
        };
      });
      d.total = d.values[d.values.length - 1].y1; // Store the total value for the entry
    });
  }
  // Define the X and Y scales for the chart
  var x = d3.scaleBand().range([0, width]);
  var y = d3.scaleLinear().rangeRound([height, 0]);

  // set chart X and Y axis
  var xAxis = d3.axisBottom(x);
  var yAxis = d3.axisLeft(y).tickFormat(d3.format(".0f"));

  // Set the domains for the X and Y axes
  x.domain(
    data.map(function (d) {
      return d.entry; // X-axis labels based on the "entry" property of each data entry
    }),
  );
  y.domain([
    0,
    d3.max(data, function (d) {
      return d.total; // Max value on the Y-axis is the largest total from the data
    }),
  ]);

  // Append the X and Y axes to the SVG
  var xAxis_g = svg
    .append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")")
    .call(xAxis);

  // Get the max number of letters of each bar's legend
  var max_len_label = d3.max(Object.keys(response), function (d) {
    return d.length;
  });

  if (max_len_label * 7 > x.bandwidth()) {
    // if the max number overflow some value: rotate the bottom legends
    xAxis_g
      .selectAll("text")
      .attr("transform", "rotate(-90)")
      .style("text-anchor", "end")
      .attr("dy", -8)
      .attr("dx", -10);

    // and extend the SVG to make space for the new text
    let frame = d3.select(div).select("svg");
    frame.attr("height", parseInt(frame.attr("height")) + max_len_label * 6.5);
  }

  svg
    .append("g")
    .attr("class", "y axis")
    .call(yAxis)
    .append("text")
    .attr("transform", "rotate(-90)") // Rotate Y-axis label to be vertical
    .attr("y", 6)
    .attr("dy", ".71em")
    .text(div.dataset.ylabel);

  // Create groups for each data entry along the X axis
  var entry = svg
    .selectAll(".entry")
    .data(data)
    .enter()
    .append("g")
    .attr("class", "g")
    .attr("transform", function (d) {
      return "translate(" + (x(d.entry) + 3) + ",0)"; // Position each group based on the entry's X value
      // shift each bar 3 pixels to the left to better view the Y axis)
    });

  // Append rectangles for the stacked bars to each entry group
  entry
    .selectAll("rect")
    .data(function (d) {
      return d.values;
    })
    .enter()
    .append("rect")
    .attr("width", x.bandwidth() - margin_between_bars) // Width of each rectangle (based on the band scale), minus 10px margin
    .attr("y", function (d) {
      return y(d.y1); // Position the rectangle on the Y axis based on the cumulative value (y1)
    })
    .attr("height", function (d) {
      return y(d.y0) - y(d.y1);
    })
    .attr("title", function (d) {
      let html_escaped_name = new Option(d.name).innerHTML;
      let val = `${html_escaped_name}: ${d.y1 - d.y0}`;
      if (d.hasOwnProperty("compare") && !isNaN(d.compare)) {
        let percent = ((d.compare / d.y1) * 100 - 100).toFixed(0);
        if (percent >= 0) {
          percent = `+${percent}`;
        }
        val = `${val}<br />${percent}%`;
      }
      return val; // Set tooltip content
    })
    .attr("data-bs-toggle", "tooltip")
    .attr("data-bs-html", "true")
    .style("fill", function (d) {
      return color(d.name);
    });

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]',
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
  );
  if (data.length === 0) {
    svg
      .append("text")
      .text("N/A")
      .style("fill", "currentColor")
      .attr("x", "50%")
      .attr("y", "50%");
  }

  // Create a legend for the chart, based on the color domain
  var legend = svg
    .selectAll(".legend")
    .data(color.domain().slice().reverse())
    .enter()
    .append("g")
    .attr("class", "legend")
    .attr("transform", function (d, i) {
      // Calculate the position of each legend item
      legend_per_col = Math.floor(height / 20);
      w = width + 60 + (Math.floor(i / legend_per_col) + 1) * 130;
      d3.select(div)
        .select("svg")
        .style("width", w + "px"); // Adjust the SVG width if needed
      return (
        "translate(" +
        Math.floor(i / legend_per_col) * 130 +
        "," +
        (i % legend_per_col) * 20 +
        ")"
      );
    });

  // Append rectangles to represent the legend colors
  legend
    .append("rect")
    .attr("x", width + 20)
    .attr("width", 18)
    .attr("height", 18)
    .style("fill", function (d) {
      return color(d);
    });

  // Append text to the legend items
  legend
    .append("text")
    .attr("x", width + 53)
    .attr("y", 9)
    .attr("dy", ".35em")
    .style("fill", "currentColor")
    .text(function (d) {
      return d;
    });
}

async function generate_donut_chart(div) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const other_filters = getOtherFiltersArg();
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );

  if (response.status != 200) {
    response = {};
  } else {
    response = await response.json();
  }
  var response_compare = {};
  if (div.dataset.compare) {
    const compare_date_filter = getDateFilterArg(div, true);
    response_compare = await (
      await fetch(
        `${div.dataset.url}&${compare_date_filter}&${other_filters}`,
        {
          headers: { Accept: "application/json" },
        },
      )
    ).json();
  }

  if (Object.keys(response).length) {
    response = fillGapsIfKeyIsDate(response, div);
  }

  // Set up the chart's width, height, and radius
  var width = div.dataset.size,
    height = div.dataset.size,
    radius = div.dataset.radius;

  var arc = d3
    .arc()
    .outerRadius(radius - 10) // Set up chart radius
    .innerRadius((radius - 10) / 2); // Set up inner radius (for donuts shape)

  // Create the pie chart layout
  var pie = d3
    .pie()
    .sort(null)
    .value(function (d) {
      return response[d];
    });

  // Create the SVG element
  var svg = d3
    .select(div)
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .append("g")
    .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")"); // Center the SVG relative to its div

  // the pie should have One color per key
  color.domain(Object.keys(response));

  if (Object.keys(response).length != 0) {
    // add data to the pie
    var g = svg
      .selectAll(".arc")
      .data(pie(Object.keys(response)))
      .enter()
      .append("g")
      .attr("class", "arc");

    // Fill each slice with a different color
    g.append("path")
      .attr("d", arc)
      .style("fill", function (d) {
        return color(d.data);
      })
      .attr("data-bs-toggle", "tooltip")
      .attr("data-bs-html", "true")
      .attr("title", function (d) {
        let html_escaped_name = new Option(d.data).innerHTML;
        let val = `${html_escaped_name}: ${response[d.data]}`;
        if (
          response_compare.hasOwnProperty(d.data) &&
          !isNaN(response_compare[d.data])
        ) {
          let percent = (
            (response_compare[d.data] / response[d.data]) * 100 -
            100
          ).toFixed(0);
          if (percent >= 0) {
            percent = `+${percent}`;
          }
          val = `${val}<br />${percent}%`;
        }
        return val; // Add text labels inside the arcs (tooltips)
      });
  } else {
    // if there is no data: create a pie with one single entry ("N/A": 1)
    let emptyPie = d3.pie().sort(null).value(1);
    var g = svg
      .selectAll(".arc")
      .data(emptyPie(["N/A"]))
      .enter()
      .append("g")
      .attr("class", "arc");

    // Color the entry with gray (#CCC)
    g.append("path").attr("d", arc).style("fill", "#CCC");

    // Append label 'N/A' to the center of the SVG
    svg
      .append("text")
      .attr("dy", ".35em")
      .style("text-anchor", "middle")
      .style("fill", "currentColor")
      .text("N/A");
  }

  var legend_height = Math.max(Object.keys(response).length, div.dataset.size);

  // Create an SVG for the legend and append it next to the chart
  var legend = d3
    .select(div)
    .append("svg")
    .attr("class", "legend")
    .attr("width", radius)
    .attr("height", legend_height)
    .selectAll("g")
    .data(color.domain().slice().reverse())
    .enter()
    .append("g")
    .attr("transform", function (d, i) {
      return "translate(0," + i * 20 + ")";
    });

  // Append a rectangle for each color in the legend
  legend
    .append("rect")
    .attr("width", 18)
    .attr("height", 18)
    .style("fill", color);

  // Append text next to each rectangle to display the label
  legend
    .append("text")
    .attr("x", 24)
    .attr("y", 9)
    .attr("dy", ".35em")
    .style("fill", "currentColor")
    .text(function (d) {
      return d;
    });

  // enable tooltips
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]',
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
  );
}

async function generate_line_chart(div) {
  const date_filter = getDateFilterArg(div);
  if (!date_filter) {
    return false;
  }
  const other_filters = getOtherFiltersArg();
  var response = await fetch(
    `${div.dataset.url}&${date_filter}&${other_filters}`,
    {
      headers: { Accept: "application/json" },
    },
  );
  if (response.status != 200) {
    response = {};
  } else {
    response = await response.json();
  }
  var response_compare = {};
  if (div.dataset.compare) {
    const compare_date_filter = getDateFilterArg(div, true);
    response_compare = await (
      await fetch(
        `${div.dataset.url}&${compare_date_filter}&${other_filters}`,
        {
          headers: { Accept: "application/json" },
        },
      )
    ).json();
  }
  var parseDate = d3.timeParse(getDateFormat(div));

  if (Object.keys(response).length) {
    response = fillGapsIfKeyIsDate(response, div);
  }

  // Convert the recieved response to a javascript array usable by D3
  var data = [];
  for (k in response) {
    let elem = { date: parseDate(k) };
    if (isNaN(response[k])) {
      elem = Object.assign(elem, response[k]);
    } else {
      elem["value"] = response[k];
    }
    for (k2 in response_compare) {
      let k_date = parseDate(k);
      let k2_date = parseDate(k2);

      // If we compare relative to the previous quarter
      if (div.dataset.days == "quarterly") {
        let temp_quarterly_date = parseDate(k2);
        temp_quarterly_date.setMonth(temp_quarterly_date.getMonth() + 3);
        if (k_date.getMonth() == temp_quarterly_date.getMonth()) {
          elem["compare"] = response_compare[k2];
        }
        // Else: assume the comparison to be yearly
      } else {
        if (
          k_date.getMonth() == k2_date.getMonth() &&
          k_date.getYear() - 1 == k2_date.getYear() &&
          k_date.getDate() == k2_date.getDate()
        ) {
          elem["compare"] = response_compare[k2];
        }
      }
    }
    if (
      Object.keys(response_compare).length &&
      !elem.hasOwnProperty("compare")
    ) {
      elem["compare"] = 0;
    }

    data.push(elem);
  }

  data.sort((a, b) => a.date - b.date);

  var margin = { top: 20, right: 80, bottom: 30, left: 50 },
    width = div.dataset.width - margin.left - margin.right,
    height = div.dataset.height - margin.top - margin.bottom;

  // Set up the x and y scales for the chart
  var x = d3.scaleTime().range([0, width]);
  var y = d3.scaleLinear().range([height, 0]);

  // Define x and y axes using D3
  var xAxis = d3.axisBottom(x);

  if (getDiffDays(div) > 30) {
    xAxis.tickFormat(d3.timeFormat("%Y/%m")); // Format x-axis labels as Year/Month
  } else {
    xAxis.tickFormat(d3.timeFormat("%d")); // or Day if the scale is <30 days
  }

  var yAxis = d3.axisLeft(y);

  var line = d3
    .line()
    .curve(d3.curveBasis) // Smooth the lines between data points
    .x(function (d) {
      return x(d.date); // Use the date for x scale
    })
    .y(function (d) {
      return y(d.value); //and the value for y one
    });

  // Create the SVG element and add a group element to hold the chart
  var svg = d3
    .select(div)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")"); // Add margins

  // Define the number of series (lines) that will be drawed.
  // Each serie has one color
  if (data.length !== 0) {
    color.domain(
      Object.keys(Object.assign({}, ...data)).filter(function (key) {
        return key !== "date"; // Filter out the "date" key from the domain
      }),
    );
  }

  // Set the x-axis domain (based on the date range)
  var begin_date = new Date(
    new URLSearchParams(date_filter).get("created_after"),
  );
  var end_date = new Date(
    new URLSearchParams(date_filter).get("created_before"),
  );
  begin_tz = begin_date.getTimezoneOffset() * 60000;
  end_tz = end_date.getTimezoneOffset() * 60000;
  begin_date = new Date(begin_date - begin_tz);
  end_date = new Date(end_date - end_tz);
  begin_date.setHours(23, 59, 59);
  end_date.setHours(0, 0, 0);

  if (getDiffDays(div) >= 1825) {
    begin_date.setMonth(0);
    end_date.setMonth(0);
    begin_date.setDate(0);
    end_date.setDate(0);
  } else if (getDiffDays(div) >= 30) {
    begin_date.setDate(0);
    end_date.setDate(0);
  } else {
    begin_date.setDate(begin_date.getDate() - 1);
  }
  x.domain([begin_date, end_date]);

  // Pass values to the series
  var values = color.domain().map(function (name) {
    return {
      name: name,
      values: data.map(function (d) {
        // if the serie we are building is "compare": return compare values
        if (name == "compare") {
          return { date: d.date, value: d.compare };
        }
        // if the serie we are building is made of a single serie
        else if (d.hasOwnProperty("value")) {
          return { date: d.date, value: d.value };
        } else {
          // otherwise return normal values
          return { date: d.date, value: +d[name] || 0 };
        }
      }),
    };
  });

  // Set the y-axis domain (based on the maximum value in the data)
  y.domain([
    0,
    d3.max(values.map((a) => d3.max(a.values.map((b) => b.value)))),
  ]);
  // Append the x-axis to the SVG element
  svg
    .append("g")
    .attr("class", "x axis")
    .style("font-size", "12px")
    .attr("transform", "translate(0," + height + ")") // Position the axis at the bottom
    .call(xAxis); // Apply the axis configuration

  // Append the y-axis to the SVG element
  svg
    .append("g")
    .attr("class", "y axis")
    .style("font-size", "12px")
    .call(yAxis)
    .append("text") // Add a label to the y-axis
    .attr("transform", "rotate(-90)") // Rotate the label vertically
    .attr("y", 6)
    .attr("dy", ".71em")
    .style("text-anchor", "end");

  // Create a group for each data series and plot the lines
  var item = svg
    .selectAll(".item")
    .data(values)
    .enter()
    .append("g")
    .attr("class", "item");

  // Draw a line for each data series
  item
    .append("path")
    .attr("class", "line")
    .attr("d", function (d) {
      return line(d.values); // Generate the line path for the data points
    })
    .style("stroke", function (d) {
      return color(d.name); // Set the line color based on the series name
    })
    .style("fill", "none"); // Do not fill the area between the bottom and the line with a color

  // Add labels to the lines at the ending point of each line
  item
    .append("text")
    .datum(function (d) {
      if (!d.values.length) {
        return { name: "", value: null }; // values is empty, return here for safety
      }
      // use the year as legend by default
      let year = d.values[0].date.getFullYear();
      if (d["name"] === "compare") {
        // if it's a compare line: use year-1
        year -= 1;
      } else if (!data.some((element) => element.hasOwnProperty("value"))) {
        // if response is a nested object: use name as serie name
        year = d.name;
      }
      return { name: year, value: d.values.at(-1) }; // Use the first data point text, last data point position for the label
    })
    .attr("transform", function (d) {
      if (d.value == null) {
        return "";
      }
      return "translate(" + x(d.value.date) + "," + y(d.value.value) + ")"; // Position the label at the last data point
    })
    .attr("x", 3) // Offset the label slightly to the right
    .attr("dy", ".35em") // Vertical alignment
    .style("fill", "currentColor")
    .text(function (d) {
      return String(d["name"]); // Display the name of the data series
    });
  if (Object.keys(response).length === 0) {
    svg
      .append("text")
      .text("N/A")
      .style("fill", "currentColor")
      .attr("x", "45%")
      .attr("y", "50%");
  }
}

function getDiffDays(div) {
  let params = new URL(document.location.toString()).searchParams;
  const parseDate = d3.timeParse("%Y-%m-%d");
  var begin_date = new Date();
  var end_date = new Date();
  begin_date.setHours(0, 0, 0);
  end_date.setHours(0, 0, 0);

  // date supplied via ?date= argument: override end date
  if (params.get("date") && parseDate(params.get("date"))) {
    end_date = parseDate(params.get("date"));
    begin_date = new Date(end_date);
    end_date.setHours(23, 59, 59);
  }

  if (!isNaN(parseInt(div.dataset.days))) {
    return parseInt(div.dataset.days);
  } else if (div.dataset.days == "quarterly") {
    let quarter = Math.floor((end_date.getMonth() + 3) / 3) - 1; // value from 0 to 3
    end_date.setMonth(quarter * 3);
    begin_date.setMonth(quarter * 3 - 3);
    begin_date.setDate(1);
    end_date.setDate(0);
    return parseInt((end_date - begin_date) / (1000 * 60 * 60 * 24));
  } else if (div.dataset.days == "yearly") {
    end_date.setMonth(end_date.getMonth());
    begin_date.setMonth(begin_date.getMonth() - 12);
    begin_date.setDate(1);
    end_date.setDate(0);
    return parseInt((end_date - begin_date) / (1000 * 60 * 60 * 24));
  }
  // if the date is provied via a dedicated <input type="date">
  const fromDate = document.getElementById("from-date");
  const toDate = document.getElementById("to-date");
  if (
    fromDate &&
    toDate &&
    Date.parse(toDate.value) &&
    Date.parse(toDate.value)
  ) {
    begin_date = new Date(Date.parse(fromDate.value));
    end_date = new Date(Date.parse(toDate.value));

    const diffDays = parseInt((end_date - begin_date) / (1000 * 60 * 60 * 24));
    return diffDays;
  }

  return 0;
}

function fillGapsIfKeyIsDate(response, div) {
  var begin_date = new Date();
  var end_date = new Date();
  begin_date.setHours(0, 0, 0);
  end_date.setHours(0, 0, 0);

  let params = new URL(document.location.toString()).searchParams;
  const parseUserSuppliedDate = d3.timeParse("%Y-%m-%d");
  // date supplied via ?date= argument: override end date
  if (params.get("date") && parseUserSuppliedDate(params.get("date"))) {
    end_date = parseUserSuppliedDate(params.get("date"));
    begin_date = new Date(end_date);
  }

  if (getDiffDays(div) >= 1825) {
    begin_date.setMonth(0);
    end_date.setMonth(0);
    begin_date.setDate(1);
    end_date.setDate(1);
  }
  if (getDiffDays(div) > 30) {
    begin_date.setDate(1);
    end_date.setDate(1);
  }

  if (div.dataset.days === undefined) {
    // date provied via a dedicated <input type="date">
    const fromDate = document.getElementById("from-date");
    const toDate = document.getElementById("to-date");
    if (
      !fromDate ||
      !toDate ||
      !Date.parse(fromDate.value) ||
      !Date.parse(toDate.value)
    ) {
      // if this date is missing or not valid: bail out
      return response;
    }
    begin_date = new Date(Date.parse(fromDate.value));
    end_date = new Date(Date.parse(toDate.value));
  } else if (isNaN(parseInt(div.dataset.days))) {
    // string provided in data-days
    if (div.dataset.days == "quarterly") {
      let quarter = Math.floor((end_date.getMonth() + 3) / 3) - 1; // value from 0 to 3
      end_date.setMonth(quarter * 3);
      begin_date.setMonth(quarter * 3 - 3);
      begin_date.setDate(1);
      end_date.setDate(0);
    } else if (div.dataset.days == "yearly") {
      begin_date.setMonth(begin_date.getMonth() - 13);
      begin_date.setDate(1);
      end_date.setDate(0);
    } else {
      return false;
    }
  } else {
    // data-days property onboarded as int in the HTML code
    begin_date.setDate(begin_date.getDate() - parseInt(div.dataset.days));
  }
  // re-set altered hours/day of months
  begin_date.setHours(0, 0, 0);
  end_date.setHours(0, 0, 0);
  if (getDiffDays(div) >= 1825) {
    begin_date.setMonth(0);
    end_date.setMonth(0);
    begin_date.setDate(1);
    end_date.setDate(1);
  }
  if (getDiffDays(div) > 30) {
    begin_date.setDate(1);
    end_date.setDate(1);
  }

  dateFormat = getDateFormat(div);
  const parseDate = d3.timeParse(dateFormat);
  const printDate = d3.timeFormat(dateFormat);

  var response_keys = Object.keys(response).map((key) => parseDate(key));
  if (response_keys.includes(null)) {
    // the keys are not dates -> return the array as is
    return response;
  }

  response_keys.forEach(function (part, index) {
    this[index] = this[index].toDateString();
  }, response_keys);

  // loop through all values
  walk = begin_date;
  while (walk <= end_date) {
    // if one value is missing from the array:
    if (!response_keys.includes(walk.toDateString())) {
      // set it to empty object or 0
      if (
        response_keys &&
        typeof response[Object.keys(response)[0]] == "object"
      ) {
        response[printDate(walk)] = {};
      } else {
        response[printDate(walk)] = 0;
      }
    }
    if (getDiffDays(div) >= 1825) {
      walk.setYear(walk.getFullYear() + 1);
    } else if (getDiffDays(div) < 31) {
      walk.setDate(walk.getDate() + 1);
    } else {
      walk.setMonth(walk.getMonth() + 1);
    }
  }

  // sort object keys by ascending date
  sorted_response = Object.keys(response)
    .sort(function (x, y) {
      if (parseDate(x) < parseDate(y)) {
        return -1;
      }
      if (parseDate(x) > parseDate(y)) {
        return 1;
      }
      return 0;
    })
    .reduce((obj, key) => {
      obj[key] = response[key];
      return obj;
    }, {});
  return sorted_response;
}

function getDateFilterArg(div, compare_with_previous = false) {
  var begin_date = new Date();
  var end_date = new Date();
  let params = new URL(document.location.toString()).searchParams;
  const parseDate = d3.timeParse("%Y-%m-%d");

  // date supplied via ?date= argument: override end date
  if (params.get("date") && parseDate(params.get("date"))) {
    end_date = parseDate(params.get("date"));
    begin_date = new Date(end_date);
  }
  begin_date.setHours(0, 0, 0);
  end_date.setHours(23, 59, 59);

  if (div.dataset.days === undefined) {
    // date provied via a dedicated <input type="date">
    const fromDate = document.getElementById("from-date");
    const toDate = document.getElementById("to-date");
    if (
      !fromDate ||
      !toDate ||
      !Date.parse(toDate.value) ||
      !Date.parse(toDate.value)
    ) {
      // if this date is missing or not valid: bail out
      return false;
    }
    begin_date = new Date(Date.parse(fromDate.value));
    end_date = new Date(Date.parse(toDate.value));
    begin_date.setHours(0, 0, 0);
    end_date.setHours(23, 59, 59);
  } else {
    // data-days property onboarded in the HTML code
    if (isNaN(parseInt(div.dataset.days))) {
      // string provided in data-days
      if (div.dataset.days == "quarterly") {
        let quarter = Math.floor((end_date.getMonth() + 3) / 3) - 1; // value from 0 to 3
        end_date.setMonth(quarter * 3);
        begin_date.setMonth(quarter * 3 - 3);
        begin_date.setDate(1);
        end_date.setDate(0);
      } else if (div.dataset.days == "yearly") {
        end_date.setMonth(end_date.getMonth());
        begin_date.setMonth(begin_date.getMonth() - 13);
        begin_date.setDate(1);
        end_date.setDate(0);
      } else {
        return false;
      }
    } else {
      // int provided in data-days
      begin_date.setDate(end_date.getDate() - parseInt(div.dataset.days));
    }
  }

  if (compare_with_previous) {
    if (div.dataset.days == "quarterly") {
      let quarter = Math.floor((end_date.getMonth() - 1) / 3); // get previous quarter
      end_date.setMonth(quarter * 3);
      begin_date.setMonth(quarter * 3 - 3);
      begin_date.setDate(1);
      end_date.setDate(0);
    } else {
      // by default, we compare relative to the previous year
      end_date.setMonth(end_date.getMonth() - 12);
      begin_date.setMonth(begin_date.getMonth() - 12);
    }
  }

  begin_tz = begin_date.getTimezoneOffset() * 60000;
  end_tz = end_date.getTimezoneOffset() * 60000;
  begin_date = new Date(begin_date - begin_tz).toISOString().slice(0, -5);
  end_date = new Date(end_date - end_tz).toISOString().slice(0, -5);
  return `created_before=${end_date}&created_after=${begin_date}`;
}

function getDateFormat(div) {
  const days = getDiffDays(div);

  if (days < 3) {
    return "%Y-%m-%d %H:%M"; // Less than 3 days, use hours
  } else if (days < 31) {
    return "%Y-%m-%d"; // Between 3 days and 1 month, use days
  } else if (days < 1825) {
    return "%Y-%m"; // Between 10 months and 5 years, use months
  } else {
    return "%Y"; // Otherwise, use years
  }
}

function getOtherFiltersArg(force_unit = false, with_attribute_only = false) {
  let filters = "";
  let params = new URL(document.location.toString()).searchParams;

  if (params.get("bl") && params.get("bl") != "All") {
    filters += `&concerned_business_lines=${encodeURIComponent(params.get("bl"))}`;
  }
  if (filters !== "") {
    filters = filters.slice(1);
  }

  let form = document.getElementById("stats-form");
  if (form) {
    form = new FormData(form);
    let detection = document.getElementById("id_detection");
    if (form.get("detection") && detection) {
      detection = detection.options[detection.selectedIndex].text;
      filters += `&detection=${encodeURIComponent(detection)}`;
    }

    let bls = document.getElementById("id_concerned_business_lines");
    if (form.get("concerned_business_lines") && bls) {
      options = Array.from(bls.selectedOptions).map(({ text }) => text);
      for (let o of options) {
        filters += `&concerned_business_lines=${encodeURIComponent(o)}`;
      }
    }
    if (form.get("is_incident")) {
      filters += "&is_incident=true";
    }
    if (form.get("is_major")) {
      filters += "&is_major=true";
    }
    for (let c of form.getAll("category_selection")) {
      filters += `&category=${encodeURIComponent(c)}`;
    }
    for (let a of form.getAll("attribute_selection")) {
      filters += `&attribute=${encodeURIComponent(a)}`;
    }

    // if we want only incidents with attributes set
    if (
      with_attribute_only &&
      form.getAll("attribute_selection").length === 0
    ) {
      for (let a of document.querySelectorAll(
        'input[name="attribute_selection"]',
      )) {
        filters += `&attribute=${encodeURIComponent(a.value)}`;
      }
    }

    // severity: check if all possible severities are int
    // if yes, then allow matematical operations
    if (form.get("severity")) {
      const all_severities = [];
      const comp = form.get("severity_comparator");
      const val = parseInt(form.get("severity"));
      const values_to_search = [];

      for (let a of document.getElementById("id_severity").children) {
        if (a.value) {
          all_severities.push(parseInt(a.value));
        }
      }
      // if comparator is '=' or any value is not a number: consider equal
      if (all_severities.some((v) => v === NaN) || comp == "et") {
        values_to_search.push(form.get("severity"));
      } else {
        for (let item of all_severities) {
          if (comp == "lt" && item < val) {
            values_to_search.push(item);
          } else if (comp == "lte" && item <= val) {
            values_to_search.push(item);
          } else if (comp == "gt" && item > val) {
            values_to_search.push(item);
          } else if (comp == "gte" && item >= val) {
            values_to_search.push(item);
          }
        }
        if (values_to_search.length === 0) {
          values_to_search.push(null);
        }
      }
      for (let v of values_to_search) {
        filters += `&severity=${encodeURIComponent(v)}`;
      }
    }
    if (form.get("unit") || force_unit) {
      let unit = form.get("unit");
      if (force_unit) {
        unit = force_unit;
      }
      filters += `&unit=${encodeURIComponent(unit)}`;
    }
  }
  return filters;
}
