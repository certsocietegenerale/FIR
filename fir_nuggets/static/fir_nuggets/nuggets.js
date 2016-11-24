// hotkeys

$(document).keypress(function(e){

	if (e.keyCode == 14 && e.ctrlKey) { // Ctrl + n
		console.log('(nuggets) Ctrl + n')
		$("#add-nugget").click()
	}

	if (e.keyCode == 13 && e.ctrlKey) { // Ctrl + ENTER
		console.log('(nuggets) Ctrl + ENTER')
		$("#submit-nugget").click();
		$("#submit-nugget").remove();
	}

	if (e.keyCode == 5 && e.ctrlKey) {
		console.log('(nuggets) Ctrl + E')
		$("#nuggets tr:hover .edit-nugget-row a").click()
	}

});


// helper function for getting cookie value

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

/* Button functions */

$(function() {

	$('#tab_nuggets').on('click', '.delete-nugget', function(e) {
		e.preventDefault();
		ajax_action($(this), delete_nugget);
	});

	$('#tab_nuggets').on('click', '.edit-nugget', function(e) {
		e.preventDefault();
		ajax_action($(this), edit_nugget);
	});

	$('#add-nugget').on('click', function(e) {
		e.preventDefault();
		ajax_action($(this), edit_nugget);
	});

	$('#nugget_modals').on('click', '#submit-nugget', function(e) {
		e.preventDefault();
		submit_nugget();
	});
})

function ajax_action(elt, callback) {

	$.ajax({
		url: elt.data('url'),
		headers: {'X-CSRFToken': getCookie('csrftoken')},
	}).success(function(data) {
		callback(data);
	});
}

function delete_nugget (data) {
	$("#nugget_"+data).remove();
	$("#raw"+data).remove();
	count = parseInt($('#nuggets-count').text());
	$('#nuggets-count').text(count - 1);
	if (count-1 == 0) {
		$('#tab_nuggets_title').addClass('hidden');
	}
}

/* Nugget form */

function edit_nugget(data) {
	$("#nugget_modals").empty();
	$("#nugget_modals").html(data);
	$("#addNugget").modal('show');
	$("#id_source").focus();
}

function submit_nugget () {
	data = $("#nugget_form").serialize()

	$.ajax({
		type: 'POST',
		url: $("#nugget_form").attr('action'),
		data: data,
		headers: {'X-CSRFToken': getCookie('csrftoken')},
		success: function (msg) {

			if (msg.status == 'success') {
				if (msg.mode == 'edit') {
					$("#addNugget").modal('hide');
					$("#nugget_"+msg.nugget_id).html(msg.row);
					$("#raw_"+msg.nugget_id).html(msg.raw);
					$("#nugget_"+msg.nugget_id).effect('highlight', 'slow');
				}

				else if (msg.mode == 'new') {
					url = $("#nuggets").data('fetch-url');
					el = $("#nuggets");
					$.get(url, function(data) {
					  el.html(data);
					  $("#addNugget").modal('hide');

					  // Update count
					  count = parseInt($('#nuggets-count').text());
					  $('#nuggets-count').text(count + 1);

					  $('#tab_nuggets_title').removeClass('hidden');
					  $('#tab_nuggets_title a').tab('show');
					  $("#nugget_"+msg.nugget_id).effect('highlight', 2000);
					});
				}
			}

			else if (msg.status == 'error') {
				html = $.parseHTML(msg.data);
				$("#addNugget .modal-body").html($(html).find('.modal-body'));
			}
		}
	})
}

/* Other functions */

function toggle_raw (id) {
	$('#raw_'+id).toggle();
}
