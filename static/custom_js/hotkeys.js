$(document).keypress(function (e) {

	console.log('(master) keypress');
	console.log(e)

	if (e.which == 3 && e.ctrlKey) { // Ctrl + C
		console.log('(master) Ctrl + c');
		$("#details-actions-comment").click();
		tinyMCE.get('id_comment').focus();
	}

});
