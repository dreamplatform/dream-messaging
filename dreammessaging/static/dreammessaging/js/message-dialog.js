$(document).ready(function () {

/* Radio lists
======================================================== */

  $('.radio-list input').on('change', function () {
    $('.radio-list-item').removeClass('selected');
    $('label[for="' + $(this).attr('id') + '"]').closest('.radio-list-item').addClass('selected');
  });

/* My messages full message
======================================================== */

  (function(){
    var $toggleContainer = $('#toggle-container'),
        $backButton = $('.js-mymessages-back-link'),
        $fullMessage = $('#content-full-message .full-message'),
        fullMessageContent = {
          timestamp: $fullMessage.find('.timestamp'),
          type: $fullMessage.find('.type img'),
          sender: $fullMessage.find('.sender'),
          recipient: $fullMessage.find('.recipient .text'),
          icon: $fullMessage.find('.recipient .icon img'),
          content: $fullMessage.find('.content .content-container')
        };

    $('.js-open-message').click(function(event){
      event.preventDefault();

      $wrapper = $(this).siblings('.wrapper');
      fullMessageContent.timestamp.html($wrapper.find('.timestamp').html());
      fullMessageContent.type.attr('src', $wrapper.find('.type img').attr('src'));
      fullMessageContent.type.attr('title', $wrapper.find('.type img').attr('title'));
      fullMessageContent.sender.html($wrapper.find('.sender').html());
      fullMessageContent.recipient.html($wrapper.find('.recipient .text').html());
      fullMessageContent.icon.attr('src', $wrapper.find('.recipient .icon img').attr('src'));
      fullMessageContent.content.html($wrapper.find('.content div').html());

      $toggleContainer.animate({'left': '-100%'});
      $backButton.fadeIn();
    });

    $backButton.click(function(event){
      $toggleContainer.animate({'left': 0});
      $backButton.fadeOut();
      event.preventDefault();
    });
  })();

});