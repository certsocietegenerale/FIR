// Patch handlebars: Convert ${...} to {{...}}
const hb_originalCompile = Handlebars.compile;
Handlebars.compile = function (templateStr, options) {
  const converted = templateStr.replace(/\$\{([^}]+)\}/g, "{{$1}}");
  return hb_originalCompile.call(this, converted, options);
};
