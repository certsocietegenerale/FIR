async function detach_relation(target) {
  const relation_id = parseInt(target.dataset.relation);
  const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]");

  var response = await fetch(`/api/relations/${relation_id}`, {
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

document.addEventListener("DOMContentLoaded", function () {
  for (const button of document.querySelectorAll(".detach-relation")) {
    button.addEventListener("click", function (event) {
      detach_relation(button);
    });
  }
});
