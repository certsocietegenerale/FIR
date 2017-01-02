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
    url = $(button).children("a").attr('data-url')

    $('#send_abuse_email').button('reset')

    //type = $(button).data('type')

    $.ajax({
      type: "GET",
      url: url,
      success: function(msg) {
        $('#sendAbuseEmail #id_to').val(msg.to)
        $('#sendAbuseEmail #id_cc').val(msg.cc)
        $('#sendAbuseEmail #id_bcc').val(msg.bcc)
        $('#sendAbuseEmail #id_subject').val(msg.subject)
        $('#sendAbuseEmail #id_body').val(msg.body)

        trustLevel = ((msg.trust == 1) ? 'knowledge' : 'analyze')
        $('#sendAbuseEmail #id_to').attr('trust', trustLevel)

        $('#sendAbuseEmail').data('artifact', msg.artifact)

        //$('#sendAbuseEmail').data('type', type)

        tinyMCE.get('id_body').setContent(msg.body)

        $("#sendAbuseEmail").modal('show');
      }
    });

  }

  // Fetch the EmailForm
  emailform_url = $('#details-actions-abuse').data('url');
  $.get(emailform_url, function (data) {
    // Add form to the page
    $('#addComment').after(data);

    // Activate tinyMCE editor
    tinymce.init({
      selector: "#id_body",
      height: 300,
      theme: "modern",
      skin: "light",
      plugins: "paste,table,code,preview",
      toolbar: "undo redo | styleselect | bold italic | bullist numlist outdent indent code",
      language: "en",
      directionality: "ltr",
      menubar: false,
      statusbar: false
    });

    // Activate 'Send Email' button
    $('#send_abuse_email').click(function (event) {
      send_email();
    });
  });

  function add_auto_comment() {
    date = new Date();
    // date format 1899-12-06 07:15
    date = date.getFullYear() + "-" + (date.getMonth()+1)
      + "-" + date.getDate() + " " + date.getHours()
      + ":" + date.getMinutes()

    comment_ = 'Abuse email sent to ' + $('#sendAbuseEmail').data('artifact')
    action_ = $("#id_action option:contains('Abuse')").attr('value')

    $.ajax({
        type: 'POST',
        url: $('#comment_form').data('new-comment-url'),
        data: {
          comment: comment_,
          action: action_,
          date: date,
          csrfmiddlewaretoken: getCookie('csrftoken'),
        },
        success: function(data) {
          $('#tab_comments tbody').prepend(data);
          // Update comment count
          count = parseInt($('#comment-count').text());
          $('#comment-count').text(count + 1);
        }
    });
  }

  function send_email() {
    $('#send_abuse_email').button('loading')

    //type = $('#sendEmail').data('type')
    //bl = $('#sendEmail').data('bl')

    var body = tinyMCE.get('id_body').getContent()
    $("#id_body").val(body)
    data = $("#email_form").serialize()

    $.ajax({
      type: 'POST',
      url: $("#email_form").attr('action'),
      data: data,
      success: function(msg) {

        if (msg.status == 'ok') {
          b = $('#send_abuse_email')
          b.text('Sent')
          b.prop('disabled', true)
          $("#sendAbuseEmail").modal('hide')
          add_auto_comment()
        }
        if (msg.status == 'ko') {
          b = $('#send_abuse_email')
          b.text('ERROR')
          b.prop('disabled', true)
          alert("Something went terribly, terribly wrong:\n"+msg.error)
          $("#sendAbuseEmail").modal('hide')
        }
      }
    });
  }



});
