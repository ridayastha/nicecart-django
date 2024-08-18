$(document).ready(function() {
    // Prevent closing from click inside dropdown
    $(document).on('click', '.dropdown-menu', function(e) {
        e.stopPropagation();
    });

    // Radio button change event
    $('.js-check :radio').change(function() {
        var check_attr_name = $(this).attr('name');
        if ($(this).is(':checked')) {
            $('input[name="' + check_attr_name + '"]').closest('.js-check').removeClass('active');
            $(this).closest('.js-check').addClass('active');
        } else {
            $(this).closest('.js-check').removeClass('active');
        }
    });

    // Checkbox change event
    $('.js-check :checkbox').change(function() {
        if ($(this).is(':checked')) {
            $(this).closest('.js-check').addClass('active');
        } else {
            $(this).closest('.js-check').removeClass('active');
        }
    });

    // Bootstrap tooltip initialization
    if ($('[data-toggle="tooltip"]').length > 0) {  // check if element exists
        $('[data-toggle="tooltip"]').tooltip();
    }

    // Fade out message after 4 seconds
    setTimeout(function() {
        console.log("Fading out the message box");
        $('.alert').fadeOut('slow');  // Changed from #message to .alert for general usage
    }, 4000);
});
