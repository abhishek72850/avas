$(function(){
    $('#dialog').dialog({
        autoOpen: false,
        draggable: false
    });

    var make_api_call = function(url, callback) {
        $('#dialog').dialog('open');
        $.ajax({
            url: url,
            method: "GET",
            data: {}
        }).done(function( data ) {
            $('#dialog').dialog('close');
           callback(data);
        }).fail(function( jqXHR, textStatus ) {
            alert('Something went wrong!!');
        });
    }

    $('#search_form').on('submit', function (e) {
        e.preventDefault();
    });

    $('#district_select').selectmenu();

    $('#states_select').selectmenu({
        change: function(e, ui) {
            state_id = $(this).val();

            $('#district_id_result').text('');

            if (state_id) {
                var url = "https://cdn-api.co-vin.in/api/v2/admin/location/districts/" + state_id;

                $('#district_select').selectmenu("disable");

                make_api_call(url, function(data) {
                    $('#district_select').empty();
                    $('#district_select').selectmenu("destroy");
                    
                    $('#district_select').append(new Option('Select District', '', true, true));
                    data.districts.forEach(function(state) {
                        $('#district_select').append(new Option(state.district_name, state.district_id));
                    });

                    $('#district_select').selectmenu({
                        change: district_select_onchange
                    });

                    $('#district_select').selectmenu("enable");
                });
            } else {
                $('#district_select').selectmenu("disable");
            }
        }
    });

    var district_select_onchange = function(e) {
        if ($(this).val())
            $('#district_id_result').text("District id: " + $(this).val());
    }

    var load_states = function() {
        var url = "https://cdn-api.co-vin.in/api/v2/admin/location/states";

        $('#states_select').selectmenu("disable");
        $('#district_select').selectmenu("disable");

        make_api_call(url, function(data) {
            data.states.forEach(function(state) {
                $('#states_select').append(new Option(state.state_name, state.state_id));
            });

            $('#states_select').selectmenu("enable");
        });
    }
    
    load_states();
});