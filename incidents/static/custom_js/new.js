$(document).ready(function() {
	if ($("#id_date").val() == "") {
		var date = new Date();
		date = new Date(date.getTime() - new Date().getTimezoneOffset() * 60 * 1000).toISOString().slice(0, 16)
		$("#id_date").val(date);
	}
});
