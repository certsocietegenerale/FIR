function execute_module_async_request () {
  $('.fir-async').each( function() {
    var url = $(this).data('fetch-url');
    var el = $(this);
    $.get(url, function(data) {
      el.html(data)
    })
  });
}

$(function() {execute_module_async_request()});
