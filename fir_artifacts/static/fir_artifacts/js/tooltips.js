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
	a.attr("href","https://www.virustotal.com/gui/search/"+hash)
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
		$(this).html($(this).html().replace(pattern,'<span data-bs-toggle="tooltip" data-bs-html="true" data-bs-delay="500" title class="hostname">\$1</span>'))
	})

	$('span.hostname').each(function(){
		$(this).attr('data-bs-original-title', centralops_tooltip($(this).text()))
	})
}

function find_ips(node) {
	$(node).each(function(){
		pattern = /((((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))|(((([0-9a-fA-F]){1,4}):){1,4}:(((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])))|(::(ffff(:0{1,4}){0,1}:){0,1}(((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])))|(fe80:(:(([0-9a-fA-F]){1,4})){0,4}%[0-9a-zA-Z]{1,})|(:((:(([0-9a-fA-F]){1,4})){1,7}|:))|((([0-9a-fA-F]){1,4}):((:(([0-9a-fA-F]){1,4})){1,6}))|(((([0-9a-fA-F]){1,4}):){1,2}(:(([0-9a-fA-F]){1,4})){1,5})|(((([0-9a-fA-F]){1,4}):){1,3}(:(([0-9a-fA-F]){1,4})){1,4})|(((([0-9a-fA-F]){1,4}):){1,4}(:(([0-9a-fA-F]){1,4})){1,3})|(((([0-9a-fA-F]){1,4}):){1,5}(:(([0-9a-fA-F]){1,4})){1,2})|(((([0-9a-fA-F]){1,4}):){1,6}:(([0-9a-fA-F]){1,4}))|(((([0-9a-fA-F]){1,4}):){1,7}:)|(((([0-9a-fA-F]){1,4}):){7,7}(([0-9a-fA-F]){1,4})))(?!([^<]+)?>)/ig
		$(this).html($(this).html().replace(pattern,'<span data-bs-toggle="tooltip" data-bs-html="true" data-bs-delay="500" title class="ip-addr">\$1</span>'))
	})

	$('span.ip-addr').each(function(){
		$(this).attr('data-bs-original-title', centralops_tooltip($(this).text()))
	})
}

function find_hashes(node) {
	$(node).each(function(){
		pattern = /([a-fA-F0-9]{32,64})(?!([^<]+)?>)/ig
		$(this).html($(this).html().replace(pattern,'<span data-bs-toggle="tooltip" data-bs-html="true" data-bs-delay="500"title class="hash">\$1</span>'))
	})

	$('span.hash').each(function(){
		$(this).attr('data-bs-original-title', virustotal_tooltip($(this).text()))
	})
}

$(function () {
	find_hostnames('.artifacts')
	find_ips('.artifacts')
	find_hashes('.artifacts')

	const tooltipTriggerList = document.querySelectorAll('span.hostname, span.ip-addr, span.hash')
	const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
});
