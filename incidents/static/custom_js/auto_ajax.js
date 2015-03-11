function hide_element(self, selector) {
	element = self;
	if (selector != 'self') {
		element = $(selector);
	}

	element.addClass('hidden');
}

// Submit forms over ajax
function submit_form(form) {
	url = form.attr('action');
	data = form.serialize();
	action = form.data('action');
	hide = form.data('hide');
	show = form.data('show');
	target = $(form.data('target'));

	$.post(url, data).success(function (data) {
		// Reset form
		form.trigger('reset');

		// Send events for custom behavior
		form.trigger('fir.form.success');

		// Trigger page action with results
		if (action == 'remove') {
			target.remove();

			hideifnone = form.data('hideifnone');
			if (hideifnone != undefined) {
				if ($(form.data('hideifnone-selector')).length == 0) {
					$(hideifnone).addClass('hidden');
				}
			}
		}
		else {
			target[action](data);
		}

		// Hide asked elements
		if (hide != undefined) {
			if (hide.contructor == Array) {
				hide.forEach(function (el, i, a) {
					hide_element(form, el);
				});
			}
			else {
				hide_element(form, hide);
			}
		}

		// Show asked elements
		if (show != undefined) {
			if (show.constructor == Array) {
				show.forEach(function (el, i, a) {
					$(el).removeClass('hidden');
				});
			}
			else {
				$(show).removeClass('hidden');
			}
		}
	}).fail(function (data) {
		form.trigger('fir.form.error');
	});
}

$(function () {
	// Submit forms over ajax
	$('body').on('submit', 'form[data-ajaxform]', function (event) {
		submit_form($(this));

		event.preventDefault();
	});

	// Submit forms using special link
	$('body').on('click', 'a.submit', function (event) {
		$(this).parents('form:first').submit();

		event.preventDefault();
	});

	// Enable datetimepickers
	$('.datetime').datetimepicker({
		format: 'yyyy-mm-dd hh:ii',
    	autoclose: true,
    	todayBtn: true,
    	keyboardNavigation: false,
	});
});
