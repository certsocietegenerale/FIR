$(function () {
	function refresh_incident_display(container) {
		return function(data) {
			container.html(data);

			container.find('.relative-date').each(function() {
      			then = moment($(this).text(), 'YYYY-MM-DD HH:mm').fromNow();
      			$(this).text(then);
    		});
		};
	}

	function refresh_display(element) {
		var incident_table = element.closest('.incident_table');
		var container;
		if (element.hasClass('incident_display')) {
			container = element;
		}
		else {
			container = element.closest('.incident_display');
		}

		var order_by = incident_table.data('order-param') || 'date';
		var asc = incident_table.data('asc') || false;

		var field = element.data('sort');
		if (field) {
			if (field == order_by) {
				asc = !asc;
			}
			else {
				order_by = field;
			}
		}

		var url = container.data('url');
		var q = container.data('query');

		page = element.data('page') || 1;

		$.get(url, { 'order_by': order_by, 'asc': asc, 'q': q, 'page': page }, refresh_incident_display(container));
	}

	function toggle_star(link) {
		return function(data) {
			var i = link.find('i.star');
    		i.toggleClass('glyphicon-star');
    		i.toggleClass('glyphicon-star-empty');

    		var starred_incidents = $('#starred_incidents');
			if (starred_incidents.length > 0) {
				refresh_display(starred_incidents);
			}
		}
	}

	// Make sure each 'incident_display' comes to life
	$('.incident_display').each(function (index) {
		refresh_display($(this));
	});

	// Change sort when clicking on a column title
	$('.incident_display').on('click', 'thead a', function (event) {
		refresh_display($(this));

		event.preventDefault();
	});

	// Change page when clicking on a pagination link
	$('.incident_display').on('click', 'a.paginate', function(event) {
		refresh_display($(this));

		event.preventDefault();
	});

	// Star/Unstar incidents
	$('.incident_display').on('click', 'a.star', function(event) {
		var link = $(this);
		var url = link.attr('href');
		$.getJSON(url, toggle_star(link));

		event.preventDefault();
	});

});
