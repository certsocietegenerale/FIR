$(function () {

  // Contextmenu on ROW
  // Trigger action when the contextual menu is about to be shown
  $(".artifacts-table a").bind("contextmenu", function (e) {


    url = "/abuse/task/" + $(this).attr('id') + "/";

    state = {
      SUCCESS: '"glyphicon glyphicon-ok" style="color:#00FF00;"',
      FAILURE: '"glyphicon glyphicon-remove" style="color:#FF0000;"',
      PENDING: '"glyphicon glyphicon-option-horizontal"',
      UNKNOWN: '"glyphicon glyphicon-question-sign"',
      ERROR: '"glyphicon glyphicon-warning-sign" style="color:#FF0000"'
    }

    if ($(".custom-menu li a span:eq(1)").length == 1) {
      $(".custom-menu li a span:eq(0)").remove();
    }

    $.ajax({
      method: "GET",
      url: url,
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function (response) {
        visualIndicator = '<span class=' + state[response.state] + '></span>';
        $(".custom-menu li a").prepend(visualIndicator);
      },
      error: function (response) {
        visualIndicator = '<span class=' + state['ERROR'] + '></span>';
        $(".custom-menu li a").prepend(visualIndicator);
      }
    });

    // Avoid showing the real one
    e.preventDefault();

    // Display contextual menu
    $(".custom-menu")
      .finish()
      .toggle(100)
      .css({
        top: e.pageY + "px",
        left: e.pageX + "px"
      });
  });

  // Discard contextual menu if click happen else where
  $(document).bind("mousedown", function (e) {

    if (!$(e.target).parents(".custom-menu").length > 0) {

      $(".custom-menu").hide(100);
    }
  });

  // When the contextual menu element is clicked this displays available actions
  $(".custom-menu li").click(function (){

    switch($(this).attr("data-action")) {
      case "first": get_email_template($(this)); break;
    }

    // Hide the contextual menu after an action was selected
    $(".custom-menu").hide(100);
  });

  // Event handler for "Send Abuse"
  function get_email_template(button) {
    url = $(button).data('url')
    $('#send_email').button('reset')

    type = $(button).data('type')

    $("#sendEmail").modal('show');
    /*$.ajax({
      type: "GET",
      url: url,
      success: function(msg) {
        $('#sendEmail #id_behalf').val(msg.behalf)
        $('#sendEmail #id_to').val(msg.to)
        $('#sendEmail #id_cc').val(msg.cc)
        $('#sendEmail #id_bcc').val(msg.bcc)
        $('#sendEmail #id_subject').val(msg.subject)
        $('#sendEmail #id_body').val(msg.body)

        $('#sendEmail').data('type', type)

        tinyMCE.get('id_body').setContent(msg.body)
        $('#sendEmail').data('bl', msg.bl)
      }
    });*/
 
  }

});
