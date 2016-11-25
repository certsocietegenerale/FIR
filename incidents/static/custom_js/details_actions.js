function Z(i) {
	if (i < 10) {
		i = "0" + i;
	}
	return i;
}

$(function () {
	$('#details-actions-add-link').click(function (event) {
		$('.details-actions-supmenu').hide();
		$('#details-actions-add').show();
		event.preventDefault();
	});

	$('#details-container').click(function (event) {
		$('.details-actions-supmenu').hide();
	});

	//
	// File Uploads
	//
	$('#details-add-file').click(function (event) {
		$('#details-files').removeClass('hidden');
		$('#id_file').click();
		event.preventDefault();
	});

	$("#id_file").change(function() {
		$('div.upload').hide();
		var files = $(this)[0].files;

		$('#filetable').empty();
		$('#filetable').append("<thead><tr><th>Filename</th><th>Description</th></tr></thead>");
		for (var i = 0; i < files.length; i++) {
			var input = "<input type='text' name='description' class='input-medium' />";
			$('#filetable').append("<tr><td>"+files[i].name+"</td><td>"+input+"</td></tr>");
		}
	})

	$("#details-container").on('dragenter', function(e) {
  		$("div.upload").show();
	});

	//
	// Attributes
	//
	function update_attribute_placeholder() {
		var placeholder = 'value';
		var unit = $('#attributes option:selected').attr('data-unit');
		if ((unit != '') && (unit != 'count') && (unit != 'None')) {
			placeholder = placeholder + ' in ' + unit;
		}
		$('#attribute-value').attr('placeholder', placeholder);
	}

	$('#show_attribute_form a').click(function (event) {
		$('#attribute_form').removeClass('hidden');
		$('#attribute_form select:first').focus();
		$('#show_attribute_form').addClass('hidden');

		event.preventDefault();
	});

	$('#attributes select').change(function () {
		update_attribute_placeholder();
	});

	$('#details-add-attribute').click(function (event) {
		$('#attributes').removeClass('hidden');
		$('#show_attribute_form a').click();

		event.preventDefault();
	});

	update_attribute_placeholder();

	// Set up form for new comment
	$('#details-actions-comment').click(function (event) {

		$("#addComment").modal('toggle');

		var form = $('#addComment form');
		form.attr('action', form.data('new-comment-url'));
		form.data('target', '#tab_comments tbody');
		form.data('action', 'prepend');

		$("#id_action").val('');
		var date = new Date();
		date = date.getFullYear() + "-" + Z((date.getMonth()+1)) +"-" + Z(date.getDate()) + " " + Z(date.getHours()) + ":" + Z(date.getMinutes())
		$("#id_date").val(date);
	});

	// Set up form for update
	$('#tab_comments').on('click', '.edit-comment', function (event) {
		var form = $('#addComment form');
		var comment_id = $(this).data('comment-id');

		$.getJSON("/ajax/comment/" + comment_id, function(msg) {
			var comment = jQuery.parseJSON(msg)[0];
			var text = comment.fields.comment;
			var action = comment.fields.action;
			var date = new Date(comment.fields.date);
			// date format 1899-12-06 07:15
			date = date.getUTCFullYear() + "-" + (Z(date.getUTCMonth()+1)) +"-" + Z(date.getUTCDate()) + " " + Z(date.getUTCHours()) + ":" + Z(date.getUTCMinutes())

			$("#addComment").modal('toggle');

			editors["id_comment"].value(text);
			$("#id_action").val(action);
			$("#id_date").val(date);

			form.attr('action', '/ajax/comment/' + comment_id);
			form.data('target', '#comment_id_' + comment_id);
			form.data('action', 'replaceWith');
		});
	});

	// Custom behavior when comment is added
	$('#addComment').on('fir.form.success', function (event) {
		// Dismiss modal
		editors["id_comment"].value("");
		$('#addComment').modal('hide');

		// Hack not to trigger on update
		if ($('#addComment form').data('action') != 'replaceWith') {
			// Update comment count
			var count = parseInt($('#comment-count').text());
			$('#comment-count').text(count + 1);
		}

		event.stopPropagation();
	});

	// Custom behavior when comment is removed
	$('#tab_comments').on('fir.form.success', function (event) {
		// Update comment count
		var count = parseInt($('#comment-count').text());
		$('#comment-count').text(count - 1);

		event.stopPropagation();
	});
});
