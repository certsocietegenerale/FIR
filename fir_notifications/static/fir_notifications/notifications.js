

function update_async_modals(elt) {
	if(!elt) {
		$('.modal-async').on('click', function (e) {
			e.preventDefault();
			ajax_action($(this), modal_action);
		});
	} else {
		$(elt).find('.modal-async').on('click', function (e) {
			e.preventDefault();
			ajax_action($(this), modal_action);
		});
	}
}


$(function() {
	update_async_modals();
});

function ajax_action(elt, callback) {
    var target = elt.data('target');
	$.ajax({
		url: elt.data('url'),
		headers: {'X-CSRFToken': getCookie('csrftoken')},
	}).success(function(data) {
		callback(data, target);
	});
}

function modal_action(data, target_id) {
    var target = $(target_id);
	target.empty();
	target.html(data);
	$(target_id+" .modal").modal('show');
	target.off('click', 'button[type=submit]');
	target.find("select").select2({ dropdownAutoWidth: true, width: '100%' });

	target.first().focus();
	target.on('click', 'button[type=submit]', function(e) {
		e.stopPropagation();
		e.preventDefault();
		var form = $(this).parents('form:first');
		var data = form.serialize();
		$.ajax({
			type: 'POST',
			url: form.attr('action'),
			data: data,
			headers: {'X-CSRFToken': getCookie('csrftoken')},
			success: function (msg) {

				if (msg.status == 'success') {
					$(target_id+" .modal").modal('hide');
					target.empty();
					location.reload();
				}

				else if (msg.status == 'error') {
					var html = $.parseHTML(msg.data);
					$(target_id+" .modal .modal-body").html($(html).find('.modal-body'));
					target.find("select").select2({ dropdownAutoWidth: true, width: '100%' });
				}
			}
		});
	});
}
