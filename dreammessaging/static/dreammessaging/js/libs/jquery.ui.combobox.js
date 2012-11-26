  (function( $ ) {
    $.widget( "ui.combobox", {
      _create: function() {
        var input, initial,
          that = this,
          select = this.element.hide(),
          selected = select.children( ":selected" ),
          value = selected.val() ? selected.text() : "",
          wrapper = this.wrapper = $( "<span>" )
            .addClass( "ui-combobox" )
            .insertAfter( select );

        function removeIfInvalid(element) {
          var value = $( element ).val(),
            matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex( value ) + "$", "i" ),
            valid = false;
          select.children( "option" ).each(function() {
            if ( $( this ).text().match( matcher ) ) {
              this.selected = valid = true;
              return false;
            }
          });
          if ( !valid ) {
            // remove invalid value, as it didn't match anything
            $( element )
              .val( initial.value )
              .attr( "title", value + " didn't match any item" );
            select.val( initial.option );
            input.data( "autocomplete" ).term = initial.value;
            return false;
          }
        }

        input = $( "<input>" )
          .appendTo( wrapper )
          .val( value )
          .attr( "title", "" )
          .attr( "placeholder", $(select).closest('[data-placeholder]').attr('data-placeholder') )
          .addClass( "ui-state-default ui-combobox-input" )
          .autocomplete({
            delay: 0,
            minLength: 0,
            position: { my : "left top", at: "left bottom+10" },
            source: function( request, response ) {
              var matcher = new RegExp( $.ui.autocomplete.escapeRegex(request.term), "i" );
              response( select.children( "option" ).map(function() {
                var item, text = $( this ).text();
                if ( /*this.value &&*/ ( !request.term || matcher.test(text) ) ) { // TODO: proper filter disabling functionality
                  item = {
                    label: text.replace(
                      new RegExp(
                        "(?![^&;]+;)(?!<[^<>]*)(" +
                        $.ui.autocomplete.escapeRegex(request.term) +
                        ")(?![^<>]*>)(?![^&;]+;)", "gi"
                      ), "<strong>$1</strong>" ),
                    value: text,
                    option: this
                  };
                  if( this.selected ) {
                    initial = item;
                  }
                  return item;
                }
              }) );
            },
            select: function( event, ui ) {
              ui.item.option.selected = true;
              that._trigger( "selected", event, {
                item: ui.item.option
              });
              // Submit form on selecting autocomplete option
              $(input).closest('form').submit();
            },
            change: function( event, ui ) {
              if ( !ui.item )
                return removeIfInvalid( this );
            }
          })
          .addClass( "ui-widget ui-widget-content ui-corner-left" );

        input.data( "autocomplete" )._renderItem = function( ul, item ) {
          return $( "<li>" )
            .data( "item.autocomplete", item )
            .append( "<a>" + item.label + "</a>" )
            .appendTo( ul );
        };

        $( "<a>" )
          .attr( "tabIndex", -1 )
          .attr( "title", "Show All Items" )
          .appendTo( wrapper )
          .addClass( "ui-combobox-toggle" )
          .click(function() {
            // close if already visible
            if ( input.autocomplete( "widget" ).is( ":visible" ) ) {
              input.autocomplete( "close" );
              removeIfInvalid( input );
              return;
            }

            // work around a bug (likely same cause as #5265)
            $( this ).blur();

            // pass empty string as value to search for, displaying all results
            input.autocomplete( "search", "" );
            input.focus();
          });

      },

      destroy: function() {
        this.wrapper.remove();
        this.element.show();
        $.Widget.prototype.destroy.call( this );
      }
    });
  })( jQuery );