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
	// arrays: check if we requested length
	let op = "";
	if (argument_with_params.split("|").length == 2) {
          op = argument_with_params.split("|")[1];
	}
	if (op == "length") {
          return escapeHtml(obj[argument].length);
	} else {
          // join values with ", "
          return escapeHtml(obj[argument].join(", "));
        }
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
