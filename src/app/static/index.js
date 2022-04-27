$(document).ready(function() {
    var inputs = ['weight', 'width', 'length', 'depth', 'height', 'storage_size', 'screen_size', 'camera_pixel'];
    var show = ['weight'];

    $('#unusual_value_hint').attr('hidden', true);
    $("#unusual_value_hint li").remove();
    $('#all_data_valid').attr('hidden', true);

    showHideInputs(inputs, show);
    $('.category_dropdown').on('change', function() {
        var chosenOption = $(this).val();
        switch (chosenOption) {
            case '46051':
                var show = ['weight'];
                showHideInputs(inputs, show);
                break;
            case '38371':
                var show = ['weight', 'storage_size', 'screen_size'];
                showHideInputs(inputs, show);
                break;
            case '5651':
                var show = ['depth', 'height', 'length', 'width'];
                showHideInputs(inputs, show);
                break;
            case '34501':
                var show = ['width'];
                showHideInputs(inputs, show);
                break;
            case '46071':
                var show = ['screen_size', 'storage_size'];
                showHideInputs(inputs, show);
                break;
            case '36731':
                var show = ['screen_size', 'camera_pixel'];
                showHideInputs(inputs, show);
                break;
        }
    });

    var attribute_name_mapping = {
        'weight': 'Weight',
        'width': 'Width',
        'length': 'Length',
        'depth': 'Depth',
        'height': 'Height',
        'storage_size': 'Storage Size',
        'screen_size': 'Screen Size',
        'camera_pixel_max': 'Camera Pixel'
    }

    $('#data-validation-btn').click(function() {
        $('#unusual_value_hint').attr('hidden', true);
        $("#unusual_value_hint li").remove();
        $('#all_data_valid').attr('hidden', true);

        $.getJSON($SCRIPT_ROOT + '/validate', {
            category_id: $('select[name="category_id"]').val(),
            weight: $('input[name="weight"]').val(),
            width: $('input[name="width"]').val(),
            length: $('input[name="length"]').val(),
            depth: $('input[name="depth"]').val(),
            height: $('input[name="height"]').val(),
            storage_size: $('input[name="storage_size"]').val(),
            screen_size: $('input[name="screen_size"]').val(),
            camera_pixel: $('input[name="camera_pixel"]').val()
        }, function(data) {
            var allDataValid = true;
            for (const result of data) {
                if (result[0] === false) {
                    allDataValid = false;
                    $('#unusual_value_hint').attr('hidden', false);
                    $('#unusual_value_list').append(
                        '<li class="possible_outlier">' + attribute_name_mapping[result[1]] + ': Too ' + result[2] + '</li>'
                    );
                }
            }

            $(':input[type="submit"]').prop('disabled', false);

            if (allDataValid === true) {
                $('#all_data_valid').attr('hidden', false);
            }
        });
        return false;
    });

    function showHideInputs(all, show) {
        for (const attribute of show) {
            $("." + attribute + "_input").show();
        }

        var hide = all.filter(x => !show.includes(x));
        for (const attribute of hide) {
            $("." + attribute + "_input").hide();
        }
    }
});