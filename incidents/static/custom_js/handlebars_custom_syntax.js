// Patch handlebars: Convert ${...} to {{...}}
// Then use compileAST from https://github.com/elastic/handlebars
// To allow handlebars usage when having a strict CSP
Handlebars.compile = function (templateStr, options) {
  const converted = templateStr.replace(/\$\{([^}]+)\}/g, "{{$1}}");
  return Handlebars.compileAST(converted, options);
};
