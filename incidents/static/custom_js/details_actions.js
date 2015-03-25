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
		files = $(this)[0].files;

		$('#filetable').empty();
		$('#filetable').append("<thead><tr><th>Filename</th><th>Description</th></tr></thead>");
		for (var i = 0; i < files.length; i++) {
			input = "<input type='text' name='description' class='input-medium' />";
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
		placeholder = 'value';
		unit = $('#attributes option:selected').attr('data-unit');
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

	//
	// Comments
	//
	tinymce.init({
		selector: "#add-comment-area textarea",
		height: 200,
		theme: "modern",
    	skin: "light",
    	plugins: "paste,table,code,preview",
    	toolbar: "undo redo | styleselect | bold italic | bullist numlist outdent indent code",
    	language: "en",
    	directionality: "ltr",
    	menubar: false,
    	statusbar: false
	});

	// Set up form for new comment
	$('#details-actions-comment').click(function (event) {
		form = $('#addComment form');
		form.attr('action', form.data('new-comment-url'));
		form.data('target', '#tab_comments tbody');
		form.data('action', 'prepend');

		$("#id_comment").val('');
    	$("#id_action").val('');

    	date = new Date();
    	date = date.getFullYear() + "-" + Z((date.getMonth()+1)) +"-" + Z(date.getDate()) + " " + Z(date.getHours()) + ":" + Z(date.getMinutes())
    	$("#id_date").val(date);
	});

	// Set up form for update
	$('#tab_comments').on('click', '.edit-comment', function (event) {
		form = $('#addComment form');
		comment_id = $(this).data('comment-id');

		$.getJSON("/ajax/comment/" + comment_id, function(msg) {
			var comment = jQuery.parseJSON(msg)[0];
      		text = comment.fields.comment;
      		action = comment.fields.action;
      		date = new Date(comment.fields.date);
      		// date format 1899-12-06 07:15
      		date = date.getUTCFullYear() + "-" + (Z(date.getUTCMonth()+1)) +"-" + Z(date.getUTCDate()) + " " + Z(date.getUTCHours()) + ":" + Z(date.getUTCMinutes())

      		$("#id_comment").val(text);
      		$("#id_action").val(action);
      		$("#id_date").val(date);

      		form.attr('action', '/ajax/comment/' + comment_id);
			form.data('target', '#comment_id_' + comment_id);
			form.data('action', 'replaceWith');

      		tinyMCE.get('id_comment').setContent(text);

      		$("#addComment").modal('toggle');
		});
	});

	// Custom behavior when comment is added
	$('#addComment').on('fir.form.success', function (event) {
		// Dismiss modal
		$('#addComment').modal('hide');

		// Hack not to trigger on update
		if ($('#addComment form').data('action') != 'replaceWith') {
			// Update comment count
			count = parseInt($('#comment-count').text());
			$('#comment-count').text(count + 1);
		}

		event.stopPropagation();
	});

	// Custom behavior when comment is removed
	$('#tab_comments').on('fir.form.success', function (event) {
		// Update comment count
		count = parseInt($('#comment-count').text());
		$('#comment-count').text(count - 1);

		event.stopPropagation();
	});
});
