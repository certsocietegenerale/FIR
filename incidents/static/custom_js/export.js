$(function () {
  $(".export-link").click(function (e) {
    var link = this;
    var table_id = $(link).data('table');
    var delimiter = $(link).data('delimiter');

    if (delimiter === undefined) {
      delimiter = '\t';
    }

    ExcellentExport.csv(link, table_id, delimiter);
  });
});
