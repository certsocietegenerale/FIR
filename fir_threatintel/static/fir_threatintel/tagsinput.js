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
  for (let elem of document.querySelectorAll(".tagsinput")) {
    if (elem === input) continue;

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

function attachTagInputHandlers(container = document) {
  for (const input of container.querySelectorAll(".tagsinput")) {
    const hidden = input.parentElement.querySelector(".tags-hidden");
    const tagBox = input.parentElement.querySelector(".tag-box");

    if (!input.classList.contains("all-tags")) {
      renderTags(
        input.value.split(",").filter((n) => n),
        hidden,
        tagBox,
      );
      input.value = "";
    }

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === ",") {
        e.preventDefault();
        const value = input.value.trim();
        if (!value) return;

        if (input.classList.contains("all-tags")) {
          renderTagsOnAllInputs(input, value);
        } else {
          const tags = [...tagBox.querySelectorAll("span")].map(
            (x) => x.textContent,
          );
          if (!tags.includes(value)) {
            tags.push(value);
            input.value = "";
            renderTags(tags, hidden, tagBox);
            hidden.value = tags.join(",");
          }
        }
      }
    });
  }
}
