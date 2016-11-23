$(function () {
  function get_template(button) {
    url = $(button).data('url')
    $('#send_email').button('reset')

    type = $(button).data('type')

    $.ajax({
      type: "GET",
      url: url,
      success: function(msg) {
        $("#sendEmail").modal('show');

        $('#sendEmail #id_behalf').val(msg.behalf)
        $('#sendEmail #id_to').val(msg.to)
        $('#sendEmail #id_cc').val(msg.cc)
        $('#sendEmail #id_bcc').val(msg.bcc)
        $('#sendEmail #id_subject').val(msg.subject)
        editors["id_body"].value(msg.body)

        $('#sendEmail').data('type', type)

        $('#sendEmail').data('bl', msg.bl)
      }
    });
  }

  function add_auto_comment(type, bl) {
    date = new Date();
    // date format 1899-12-06 07:15
    date = date.getFullYear() + "-" + (date.getMonth()+1) +"-" + date.getDate() + " " + date.getHours() + ":" + date.getMinutes()

    comment_ = ''
    action_ = ''

    if (type == 'takedown') {
      comment_ = 'Takedown started'
      action_ = $("#id_action option:contains('Takedown')").attr('value')
    }

    if (type == 'alerting') {
      comment_ = 'Alert sent'
      if (bl != undefined) {
        comment_ += ' to ' + bl;
      }
      console.log(comment_)
      action_ = $("#id_action option:contains('Alerting')").attr('value')
    }

  if (action_ != '') {
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
  }

  function send_email() {
    $('#send_email').button('loading')

    type = $('#sendEmail').data('type')
    bl = $('#sendEmail').data('bl')

    $("#id_body").val(editors["id_body"].value());
    data = $("#email_form").serialize()

    $.ajax({
      type: 'POST',
      url: $("#email_form").attr('action'),
      data: data,
      success: function(msg) {

        if (msg.status == 'ok') {
              b = $('#send_email')
              b.text('Sent')
              b.prop('disabled', true)
              $("#sendEmail").modal('hide')
              add_auto_comment(type, bl)
            }
        if (msg.status == 'ko') {
              b = $('#send_email')
              b.text('ERROR')
              b.prop('disabled', true)
              alert("Something went terribly, terribly wrong:\n"+msg.error)
              $("#sendEmail").modal('hide')
        }
      }
    });
  }

  // When you click on 'alert', display submenu or modal
  $('#details-actions-alert').click(function (event) {
    if ($(this).data('url') == undefined) {
      $('.details-actions-supmenu').hide();
      $('#details-actions-alert-bls').show();
      event.preventDefault();
    }
    else {
      get_template($(this));
    }
  });

  // A click on a submenu displays the modal
  $('.details-alert-bl').click(function (event) {
    get_template($(this));
  });

  // Fetch the EmailForm
  emailform_url = $('#details-actions-alert-bls').data('url');
  $.get(emailform_url, function (data) {
    // Add form to the page
    $('#addComment').after(data);

    editors["id_body"] = init_simplemde($("#id_body"));

    // Activate 'Send Email' button
    $('#send_email').click(function (event) {
      send_email();
    });
  });
});
