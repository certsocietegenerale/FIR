function centralops_tooltip(ip) {
	d = $('<div />')
	ul = $('<ul />')

	li = $('<li />')
	li.text("Centralops on ")
	a = $('<a></a>')
	a.attr("href","http://centralops.net/co/DomainDossier.aspx?addr="+ip+"&dom_whois=1&net_whois=1&dom_dns=1")
	a.attr('target','_blank')
	a.text(ip)
	li.append(a)

	ul.append(li)

	d.append(ul)

	return d.html()
}

function virustotal_tooltip(hash) {
	// https://www.virustotal.com/en/search/?query=

	d = $('<div />')
	ul = $('<ul />')

	li = $('<li />')
	li.text("Virustotal on ")
	a = $('<a></a>')
	a.attr("href","https://www.virustotal.com/en/search/?query="+hash)
	a.attr('target','_blank')
	a.text(hash)
	li.append(a)

	ul.append(li)

	d.append(ul)

	return d.html()

}

function find_hostnames(node) {
	$(node).each(function(){
		pattern = /((([\w\-]+\.)+)([a-zA-Z]{2,6}))(?!([^<]+)?>)/ig
		$(this).html($(this).html().replace(pattern,'<span data-toggle="tooltip" title class="hostname">\$1</span>'))
	})

	$('span.hostname').each(function(){
		$(this).attr('data-original-title', centralops_tooltip($(this).text()))
	})
}

function find_ips(node) {
	$(node).each(function(){
		pattern = /((\d){1,3}\.(\d){1,3}\.(\d){1,3}\.(\d){1,3})(?!([^<]+)?>)/ig
		$(this).html($(this).html().replace(pattern,'<span data-toggle="tooltip" title class="ip-addr">\$1</span>'))
	})

	$('span.ip-addr').each(function(){
		$(this).attr('data-original-title', centralops_tooltip($(this).text()))
	})
}

function find_hashes(node) {
	$(node).each(function(){
		pattern = /([a-fA-F0-9]{32,64})(?!([^<]+)?>)/ig
		$(this).html($(this).html().replace(pattern,'<span data-toggle="tooltip" title class="hash">\$1</span>'))
	})

	$('span.hash').each(function(){
		$(this).attr('data-original-title', virustotal_tooltip($(this).text()))
	})
}

$(function () {
	find_hostnames('.artifacts')
	find_ips('.artifacts')
	find_hashes('.artifacts')

	$('span.hostname').tooltip({'html':true, 'trigger':'manual', 'delay': {'show':100, 'hide':200} })
	$('span.ip-addr').tooltip({'html':true, 'trigger':'manual', 'delay': {'show':100, 'hide':200} })
	$('span.hash').tooltip({'html':true, 'trigger':'manual', 'delay': {'show':100, 'hide':200} })

	var tooltipTimer = false;
	timeout = 500

	function sticky_tooltip(){
		tooltip = $('.tooltip')
		tooltip.on('mouseover', function() { clearTimeout(tooltipTimer) })
		.on('mouseleave', function() {
			setTimeout(function(){
				tooltip.prev().tooltip('hide')
			}, timeout);
		})
	}

	$('span.hostname').on('mouseover',function(){
		clearTimeout(tooltipTimer)
		$(this).tooltip('show');
		sticky_tooltip();
	})
	.on('mouseleave', function() {
		tooltipTimer = setTimeout(function(){$('.tooltip').prev().tooltip('hide')}, timeout)
	})

	$('span.ip-addr').on('mouseover',function(){
		clearTimeout(tooltipTimer)
		$(this).tooltip('show');
		sticky_tooltip();
	})
	.on('mouseleave', function() {
		tooltipTimer = setTimeout(function(){$('.tooltip').prev().tooltip('hide')}, timeout)
	});


	$('span.hash').on('mouseover',function(){
		clearTimeout(tooltipTimer)
		$(this).tooltip('show');
		sticky_tooltip();
	})
	.on('mouseleave', function() {
		tooltipTimer = setTimeout(function(){$('.tooltip').prev().tooltip('hide')}, timeout)
	});
});
