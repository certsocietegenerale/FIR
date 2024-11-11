function removeDOM(className) {
  domelem = document.getElementsByClassName(className)[0];
  if (domelem != undefined) {
    domelem.remove();
  }
}

function configDisplay(show) {
  document.getElementsByClassName(
    "form-row field-dynamic_config",
  )[0].style.display = show;
}

function allowOnlyNumbers(e) {
  if (!/[0-9]/i.test(e.key)) {
    e.preventDefault();
  }
}

function changeNameType(type) {
  if (type == "number") {
    document.getElementById("id_name").value = document
      .getElementById("id_name")
      .value.replace(/[^0-9]/gi, "");
    document
      .getElementById("id_name")
      .addEventListener("keypress", allowOnlyNumbers);
  } else {
    document
      .getElementById("id_name")
      .removeEventListener("keypress", allowOnlyNumbers);
  }
}

function addColorField(color) {
  div = document.createElement("div");
  div.classList.add("form-row", "field-color");
  div.innerHTML =
    '<div><div class="flex-container"><label class="required" for="id_color">Color:</label><input type="text" id="id_color" class="colorfield_field jscolor form-control" name="color" value="' +
    color +
    '" placeholder="' +
    color +
    '" data-jscolor="{hash:true,width:225,height:150,format:\'hex\',required:true,paletteCols:4,paletteHeight:28}" required /></div></div>';
  document.getElementsByClassName("module aligned")[0].appendChild(div);
  jscolor.install();
}

function getColor(getFrom, default_color) {
  color = undefined;
  if (getFrom == "config") {
    color = JSON.parse(
      document.getElementById("id_dynamic_config").value,
    ).color;
  } else if (getFrom == "input") {
    elem = document.getElementById("id_color");
    if (elem != undefined) {
      color = elem.value;
    }
  }
  if (color == undefined) {
    return default_color;
  }
  return color;
}

document.addEventListener("DOMContentLoaded", function (event) {
  function toggle_labelgroup() {
    e = document.getElementById("id_group");
    if (e == undefined) {
      return;
    }
    value = e.options[e.selectedIndex].text;
    configDisplay("none");

    if (value == "severity") {
      existing_color = getColor("config", "#000000");
      changeNameType("number");
      addColorField(existing_color);
      document // event listner has been removed when editing HTML
        .getElementById("id_group")
        .addEventListener("change", toggle_labelgroup);
    } else {
      changeNameType("text");
      removeDOM("field-color");
    }
    return true;
  }

  function save_json() {
    json = JSON.parse(document.getElementById("id_dynamic_config").value);
    color = getColor("input");
    delete json.color;
    if (color != undefined) {
      json.color = color;
    }
    document.getElementById("id_dynamic_config").value = JSON.stringify(json);
  }

  id_group = document.getElementById("id_group");
  if (id_group != undefined) {
    id_group.addEventListener("change", toggle_labelgroup);
  }
  toggle_labelgroup();

  label_form = document.getElementById("label_form");
  if (label_form != undefined) {
    label_form.addEventListener("submit", save_json);
  }
});
