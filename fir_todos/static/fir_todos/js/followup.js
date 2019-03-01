$(function () {
	url = $('#fir_todos').data('url');
	$.get(url, function (data) {
		$('#fir_todos_followup').html(data);
	});
});
