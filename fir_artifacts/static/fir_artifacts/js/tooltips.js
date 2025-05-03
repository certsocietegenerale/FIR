function centralops_tooltip(ip) {
  const d = document.createElement("div");
  const ul = document.createElement("ul");
  const li = document.createElement("li");
  const a = document.createElement("a");

  li.textContent = "Centralops on ";
  a.href =
    "http://centralops.net/co/DomainDossier.aspx?addr=" +
    encodeURIComponent(ip) +
    "&dom_whois=1&net_whois=1&dom_dns=1";
  a.target = "_blank";
  a.textContent = ip;

  li.appendChild(a);
  ul.appendChild(li);
  d.appendChild(ul);
  return d.outerHTML;
}

function virustotal_tooltip(hash) {
  const d = document.createElement("div");
  const ul = document.createElement("ul");
  const li = document.createElement("li");
  const a = document.createElement("a");

  li.textContent = "Virustotal on ";
  a.href = "https://www.virustotal.com/gui/search/" + encodeURIComponent(hash);
  a.target = "_blank";
  a.textContent = hash;

  li.appendChild(a);
  ul.appendChild(li);
  d.appendChild(ul);
  return d.outerHTML;
}

function find_hostnames(nodes) {
  for (n of document.querySelectorAll(nodes)) {
    const pattern = /((([\w\-]+\.)+)([a-zA-Z]{2,6}))(?!([^<]+)?>)/gi;
    const replace =
      '<span data-bs-toggle="tooltip" data-bs-html="true" data-bs-delay="500" title class="hostname">\$1</span>';
    n.innerHTML = n.innerHTML.replace(pattern, replace);
  }

  for (const span of document.querySelectorAll("span.hostname")) {
    span.setAttribute(
      "data-bs-original-title",
      centralops_tooltip(span.textContent),
    );
  }
}

function find_ips(nodes) {
  for (n of document.querySelectorAll(nodes)) {
    const pattern =
      /((((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))|(((([0-9a-fA-F]){1,4}):){1,4}:(((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])))|(::(ffff(:0{1,4}){0,1}:){0,1}(((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])))|(fe80:(:(([0-9a-fA-F]){1,4})){0,4}%[0-9a-zA-Z]{1,})|(:((:(([0-9a-fA-F]){1,4})){1,7}|:))|((([0-9a-fA-F]){1,4}):((:(([0-9a-fA-F]){1,4})){1,6}))|(((([0-9a-fA-F]){1,4}):){1,2}(:(([0-9a-fA-F]){1,4})){1,5})|(((([0-9a-fA-F]){1,4}):){1,3}(:(([0-9a-fA-F]){1,4})){1,4})|(((([0-9a-fA-F]){1,4}):){1,4}(:(([0-9a-fA-F]){1,4})){1,3})|(((([0-9a-fA-F]){1,4}):){1,5}(:(([0-9a-fA-F]){1,4})){1,2})|(((([0-9a-fA-F]){1,4}):){1,6}:(([0-9a-fA-F]){1,4}))|(((([0-9a-fA-F]){1,4}):){1,7}:)|(((([0-9a-fA-F]){1,4}):){7,7}(([0-9a-fA-F]){1,4})))(?!([^<]+)?>)/gi;
    const replace =
      '<span data-bs-toggle="tooltip" data-bs-html="true" data-bs-delay="500" title class="ip-addr">\$1</span>';
    n.innerHTML = n.innerHTML.replace(pattern, replace);
  }

  for (const span of document.querySelectorAll("span.ip-addr")) {
    span.setAttribute(
      "data-bs-original-title",
      centralops_tooltip(span.textContent),
    );
  }
}

function find_hashes(nodes) {
  for (n of document.querySelectorAll(nodes)) {
    const pattern = /([a-fA-F0-9]{32,64})(?!([^<]+)?>)/gi;
    const replace =
      '<span data-bs-toggle="tooltip" data-bs-html="true" data-bs-delay="500"title class="hash">\$1</span>';
    n.innerHTML = n.innerHTML.replace(pattern, replace);
  }
  for (const span of document.querySelectorAll("span.hash")) {
    span.setAttribute(
      "data-bs-original-title",
      virustotal_tooltip(span.textContent),
    );
  }
}

document.addEventListener("DOMContentLoaded", function () {
  find_hostnames(".artifacts");
  find_ips(".artifacts");
  find_hashes(".artifacts");

  const tooltipTriggerList = document.querySelectorAll(
    "span.hostname, span.ip-addr, span.hash",
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
  );
});
