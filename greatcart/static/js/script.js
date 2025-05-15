$(document).ready(function() {
    // Prevent dropdown closing on clicking inside
    $(document).on('click', '.dropdown-menu', function (e) {
      e.stopPropagation();
    });
  
    // Radio button change toggle active class
    $('.js-check :radio').change(function () {
      var check_attr_name = $(this).attr('name');
      if ($(this).is(':checked')) {
        $('input[name='+ check_attr_name +']').closest('.js-check').removeClass('active');
        $(this).closest('.js-check').addClass('active');
      } else {
        $(this).closest('.js-check').removeClass('active');
      }
    });
  
    // Checkbox change toggle active class
    $('.js-check :checkbox').change(function () {
      if ($(this).is(':checked')) {
        $(this).closest('.js-check').addClass('active');
      } else {
        $(this).closest('.js-check').removeClass('active');
      }
    });
  
    // Bootstrap tooltip init
    if ($('[data-toggle="tooltip"]').length > 0) {
      $('[data-toggle="tooltip"]').tooltip();
    }
  
    // Message fade in and fade out (handle multiple messages)
    $('.message').hide().fadeIn('fast');
  
    $('.message').each(function(index) {
      const $msg = $(this);
      setTimeout(function() {
        $msg.fadeTo(500, 0.5).slideUp(500, function() {
          $(this).remove();
        });
      }, 4000 + index * 300);  // stagger fadeout if multiple messages
    });
  
  });
  