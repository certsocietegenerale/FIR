$(function () {

  // Contextmenu on ROW
  // Trigger action when the contextual menu is about to be shown
  $(".artifacts-table a").bind("contextmenu", function (e) {

    artifact_id = $(this).data('id')
    abuse_link = $("#send_abuse_link").data('urltemplate')

    $("#send_abuse_link").data('url', abuse_link.replace(/0\/$/, artifact_id + '/'))
    url = "/abuse/task/" + artifact_id + "/";

    state = {
      SUCCESS: '"glyphicon glyphicon-ok" style="color:#00FF00;"',
      FAILURE: '"glyphicon glyphicon-remove" style="color:#FF0000;"',
      PENDING: '"glyphicon glyphicon-time"',
      UNKNOWN: '"glyphicon glyphicon-question-sign"',
      ERROR: '"glyphicon glyphicon-warning-sign" style="color:#FF0000"'
    }

    if ($(".custom-menu #visualIndicator")) {
      $(".custom-menu #visualIndicator").remove();
    }

    $.ajax({
      method: "GET",
      url: url,
      headers: {'X-CSRFToken': getCookie('csrftoken')},
      success: function (response) {
        visualIndicator = '<span id="visualIndicator" class=' + state[response.state] + '></span>';
        $(".custom-menu li a").prepend(visualIndicator);
      },
      error: function (response) {
        visualIndicator = '<span id="visualIndicator" class=' + state['ERROR'] + '></span>';
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
    url = $("#send_abuse_link").data('url')

    $('#send_abuse_email').button('reset')

    $.ajax({
      type: "GET",
      url: url,
      success: function(msg) {
        $('#sendAbuseEmail #abuse_to').val(msg.to)
        $('#sendAbuseEmail #abuse_cc').val(msg.cc)
        $('#sendAbuseEmail #abuse_bcc').val(msg.bcc)
        $('#sendAbuseEmail #abuse_subject').val(msg.subject)
        $('#sendAbuseEmail #abuse_body').val(msg.body)

        trustLevel = ((msg.trust == 1) ? 'knowledge' : 'analyze')
        $('#sendAbuseEmail #abuse_to').attr('trust', trustLevel)

        $('#sendAbuseEmail').data('artifact', msg.artifact)

        editors["abuse_body"].value(msg.body)
        $("#sendAbuseEmail").modal('show')

        if ('enrichment_raw' in msg) {
          $("#abuse_enrichment_names").text(msg.enrichment_names.join(' | '))
          $("#abuse_enrichment_emails").text(msg.enrichment_emails)
          $("#abuse_enrichment_raw").text(msg.enrichment_raw)
          $("#abuse_tab_enrichment_link").removeClass('hide');
        } else {
          $("#abuse_tab_enrichment_link").addClass('hide');
        }
      }
    });

  }

  // Fetch the EmailForm
  emailform_url = $('#details-actions-abuse').data('url');
  $.get(emailform_url, function (data) {
    // Add form to the page
    $('#addComment').after(data);


    editors["abuse_body"] = init_simplemde($("#abuse_body"));
    // Activate 'Send Email' button
    $('#send_abuse_email').click(function (event) {
      send_email();
    });
    $('#sendAbuseEmail').on('shown.bs.modal', function (e) {
      editors["abuse_body"].codemirror.refresh()
    })
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

    $("#abuse_body").val(editors["abuse_body"].value());
    data = $("#abuse_email_form").serialize()

    $.ajax({
      type: 'POST',
      url: $("#abuse_email_form").attr('action'),
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
