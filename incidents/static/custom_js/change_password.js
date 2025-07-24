addEventListener("DOMContentLoaded", (event) => {
  const pw_form = document.getElementById("password_form");
  const pw_modal = document.getElementById("changePassword");
  const pw_changed = document.getElementById("passwordChangedAlert");
  const pw_error = document.getElementById("passwordNotChangedAlert");
  const pw_error_msg = document.getElementById("passwordNotChangedErrorMsg");

  pw_form.addEventListener("fir.form.success", function (event) {
    bootstrap.Modal.getInstance(pw_modal).hide();
    pw_changed.classList.remove("visually-hidden");
    event.stopPropagation();
  });
  pw_form.addEventListener("fir.form.error", function (event) {
    bootstrap.Modal.getInstance(pw_modal).hide();

    if (event.detail.responseJSON !== undefined) {
      pw_error_msg.textContent = event.detail.responseJSON.Error;
    } else {
      pw_error_msg.textContent = "";
    }

    pw_error.classList.remove("visually-hidden");
    event.stopPropagation();
  });
});
