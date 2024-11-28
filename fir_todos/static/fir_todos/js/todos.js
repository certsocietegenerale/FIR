$(function () {
	if ($('#fir_todos').length > 0) {
		function refresh_tasks_dashboard(element) {
			page = element.data('page') || 1;
			url = $('#tab_tasks').data('url');
			$.get(url, { 'page': page }, function (data) {
				$('#fir_todos').html(data);
			});
		}

		// Fetch todo list if present
		if ($('#fir_todos_list').length > 0) {
			url = $('#fir_todos_list').data('url');
			$.get(url, function (data) {
				$('#fir_todos_list').html(data);

				$("#fir_todos #id_business_line").select2({
					width: '45%',
					theme: "bootstrap-5",
					selectionCssClass: 'select2--small mt-2',
					dropdownCssClass: 'select2--small',
				});

				if ($('.fir_todo_item').length > 0) {
					$('#fir_todos').removeClass('visually-hidden');
				}
			});
		}

		// Fetch dashboard if present
		if ($('#tab_tasks').length > 0) {
			refresh_tasks_dashboard($('#tab_tasks'));
		}

		// Make pagination work
		$('#fir_todos').on('click', 'a.paginate', function(event) {
			refresh_tasks_dashboard($(this));
			event.preventDefault();
		});

		// Click on 'Add' so that form appears
		$('#fir_todos_add').click(function (event) {
			$('#fir_todos_new').removeClass('visually-hidden');
			$('#fir_todos_new input:text:first').focus();

			event.preventDefault();
		});

		// Click in the action bar to make form appear
		$('#details-add-todo').click(function (event) {
			$('#fir_todos').removeClass('visually-hidden');
			$('#fir_todos_add').click();

			event.preventDefault();
		});

		// Custom behavior when comment is added
		$('#fir_todos_list').on('fir.form.success', '#fir_todos_new', function (event) {
			$("#fir_todos #id_business_line").val("").trigger("change") 
			event.stopPropagation();
		});
	}
});
