async function set_major_on_category_change() {
  let url = "/api/categories?is_major=true";
  var entries = [];
  while (url != null) {
    var response = await (
      await fetch(url, {
        headers: { Accept: "application/json" },
      })
    ).json();
    entries = entries.concat(response["results"]);
    url = response["next"];
  }

  document.getElementById("id_category").addEventListener("change", (event) => {
    let is_major = false;
    if (!isNaN(event.target.value)) {
      for (entry of entries) {
        if (entry["name"] == event.target[event.target.selectedIndex].text) {
          is_major = true;
        }
      }
    }
    document.getElementById("id_is_major").checked = is_major;
  });
}

function set_is_major(entries, event) {}

document.addEventListener("DOMContentLoaded", function () {
  // Set date field to current date, if needed
  if (!document.getElementById("id_date").value) {
    var date = new Date();
    date = new Date(date.getTime() - new Date().getTimezoneOffset() * 60 * 1000)
      .toISOString()
      .slice(0, 16);
    document.getElementById("id_date").value = date;
  }
  set_major_on_category_change();
});
