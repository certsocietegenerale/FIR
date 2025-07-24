async function delete_file(id) {
  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");

  var response = await fetch(`/api/files/${id}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
    },
  });

  if (response.status != 204) {
    console.error(await response.json());
  } else {
    document.location.reload();
  }
}

function file_added(files) {
  document.querySelector("div.upload").style.display = "none";
  const table = document.getElementById("filetable");

  table.innerHTML =
    "<thead><tr><th>Filename</th><th>Description</th></tr></thead>";
  for (f of files.files) {
    const description = document.createElement("td");
    description.textContent = f.name;

    const input =
      '<input type="text" name="description" class="input-medium file-descriptions" />';
    table.innerHTML += `<tr>${description.outerHTML}<td>${input}</td></tr>`;
  }
}

async function upload_files(id) {
  let formData = new FormData();
  for (f of document.getElementById("id_file").files) {
    formData.append("file", f);
  }
  for (d of document.getElementsByClassName("file-descriptions")) {
    formData.append("description", d.value);
  }

  let csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");

  var response = await fetch(`/api/files/${id}/upload`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-CSRFToken": csrftoken.value,
    },
    body: formData,
  });

  if (response.status != 200) {
    console.error(await response.json());
  } else {
    document.location.reload();
  }
}

document.addEventListener("DOMContentLoaded", function () {
  for (div of document.querySelectorAll(".details-file-delete")) {
    div.addEventListener("click", function (event) {
      event.preventDefault();
      delete_file(div.dataset.id);
    });
  }

  document
    .getElementById("btn-upload")
    .addEventListener("click", function (event) {
      event.preventDefault();
      upload_files(document.getElementById("upload_form").dataset.id);
    });

  document.getElementById("btn-browse").addEventListener("click", function () {
    document.getElementById("id_file").click();
  });

  document
    .getElementById("details-add-file")
    .addEventListener("click", function () {
      event.preventDefault();
      const details = document.getElementById("details-files");
      details.classList.remove("visually-hidden");
      document.getElementById("id_file").click();
    });

  document
    .getElementById("details-container")
    .addEventListener("dragenter", function () {
      document.querySelector("div.upload").style.display = "block";
    });

  document.getElementById("id_file").addEventListener("change", function () {
    file_added(document.getElementById("id_file"));
  });
});
