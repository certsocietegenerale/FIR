function execute_module_async_request () {
  $('.fir-async').each( function() {
    var url = $(this).data('fetch-url');
    var el = $(this);
    $.get(url, function(data) {
      el.html(data)
    })
  });
}

function execute_module_async_request_selector (selector, callback) {
  var url = $(selector).data('fetch-url');
  var el = $(selector);
  $.get(url, function(data) {
    el.html(data)
  })
}

$(function() {execute_module_async_request()});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function toggle() {
  $.getJSON("/user/toggleclosed", function(msg) {
    document.location.reload(true);
  });
}

function bind_button_checkbox(button, checkbox) {

  if (checkbox.prop('checked')) {
    button.addClass('active')
  }

  button.click(function() {
    checkbox.prop('checked', !checkbox.prop('checked'));
  });
}
