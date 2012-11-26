$(document).ready(function () {

/* Dialogs
======================================================== */

$('.js-open-message').colorbox({
  transition: 'elastic',
  scrolling: false,
  innerWidth: '500px',
  innerHeight: '550px',
  initialWidth: '100px',
  initialHeight: '100px',
  opacity: 0.5,
  onLoad: function() {
    $('#cboxClose').hide();
  },
  onComplete: function() {
    $('#cboxClose').fadeIn(400);
  }
});

$('.js-send-new-message').colorbox({
  transition: 'elastic',
  iframe: true,
  fastIframe: false,
  scrolling: false,
  innerWidth: '500px',
  innerHeight: '550px',
  initialWidth: '100px',
  initialHeight: '100px',
  opacity: 0.5,
  href: function () {
    return $(this).attr('data-url');
  },
  onLoad: function() {
    $('#cboxClose').hide();
  },
  onComplete: function() {
    $('#cboxClose').fadeIn(400);
  }
});

/* Filters
======================================================== */

/* Submit form on clicking "option" element */
/*
$('.filter select').on('change', function () {
  $(this).closest('form').submit();
});
*/

// Turn selectboxes into comboboxes
$('.filter select').each(function () {
  $(this).combobox();
});

/* Submit form on clicking enter on search field */
$(".search input").keypress(function (e) {
  if (e.which == 13) {
    e.preventDefault();
    $(this).closest('form').submit();
  }
});

/* Inline messages
======================================================== */

(function(){
  var $inlineMessages = $('.message-inline'),
      resizeTimeout;

  $('#messages-linear').on('click', '.message-inline.expandable', function(e){
    var $this = $(this);
    if( ( $(e.target).closest('.content').length > 0 /*&& $this.hasClass('open')*/ ) ) {
      return;
    }
    $this.toggleClass('open');
  });

  $(window).resize(function() {
    window.clearTimeout(resizeTimeout);
    resizeTimeout = window.setTimeout(function() {
      $inlineMessages.each(function() {
        var $this = $(this);
        if( $this.find('.content div').height() > 30 ) {
          $this.addClass('expandable');
        } else {
          $this.removeClass('expandable');
        }
      });
    }, 300);
  });
})();

/* Functions
======================================================== */

window.cboxForceReload = function() {
  $(document).on('cbox_closed', function(){ window.location.reload(true); });
}

});
