var loc = 0;
$(document).ready(function () {
        $("#log").hide();
        $("#needradio :radio").change(function () {
            var value = $(this).val();
            if (value == 0) {
                $("#log").hide();
            } else {
                $("#log").show();
            }
        });

        $("#log2").hide();
        $("#needradio2 :radio").change(function () {
            var value = $(this).val();
            if (value == 0) {
                $("#log2").hide();
            } else {
                $("#log2").show();
            }
        });});
$("#header").attr("src", $("#header").attr("src")+"?timestamp=" + new Date().getTime());
 $("#unloadHeader").fileinput({
        showPreview: false,
        showUpload: false,
        showCancel:false,
        elErrorContainer: '#kartik-file-errors',
        allowedFileExtensions: ["jpg","png","gif"],
        maxFileSize: 3000,
    });


$("#unloadHeader").change(function (e) {
        for (var i = 0; i < e.target.files.length; i++) {
            var file = e.target.files.item(i);
            var type = file.type;
            type = type.substring(0, type.indexOf('/'));
            if (type != 'image') {
                window.alert("Please select a JPG | GIF | PNG format image.");
                return;
            }
            var freader = new FileReader();
            freader.readAsDataURL(file);
            freader.onload = function (e) {
                var src = e.target.result;
                $("#header").attr("src", src);
            }
        }
    });

$('#verify_loc').click(function () {
    var location = $('#location').val();
    $.ajax({
        type: "post",
        dataType: "json",
        url: "/verify_location",
        data: {'location': location},
        success: function (result) {
            loc = result.result;
            if (loc == null) {
                alert('The address validation failed, please add post code or other details.');
            }
            if (loc.length == 1) {
                $('#location').val(result.result[0]);
            } else {
                $('#hint').html('');
                $('#hint').append('Select your location:');
                var i = 0;
                for (i; i < result.result.length; i++) {
                    $('#hint').append('<li class="list-item">' +
                        '<a name="loc" href="javascript:void(0);">' + result.result[i] + '</a></li>');
                }
                $('a[name="loc"]').click(function () {
                    $('#location').val($(this).text());
                })
            }
        }
    });
});

function sub_loc() {
    var location = $('#location').val();
    if (loc == 0) {
        alert("Please verify your address.");
        return 1;
    } else if (loc == null || $.inArray(location, loc) == -1) {
        alert("Please enter a valid address.");
        return 1;
    }
    return 0;
}


$('#subpost', parent.document).click(function () {
    if (sub_loc()) {
        $("html,body").animate({scrollTop: $("#location").offset().top});
        return false;
    } else {
        var pos_name = $("#pos_name").val();
        $.ajax({
            type: "POST",
            dataType: "json",
            url: "/post",
            data: $('#formPost').serialize(),
            success: function (result) {
                if (result.state == "success") {
                    window.alert("Submit Successfully");
                    document.getElementById("formPost").reset();
                    $('#closepost', parent.document).click();
                    window.parent.location.reload();

                } else {
                    window.alert("Fail to submit, please try again");
                }
            }
        });
    }
});


$("#subProfile").click(function () {
    var data = new FormData($("#formPro")[0]);
    if (sub_loc()) {
        return false;
    } else {
        $.ajax({
            type: "post",
            dataType: "json",
            url: "/updateprofile",
            // data: $('#formPro').serialize(),
            data: data,
            processData: false,
            contentType: false,
            success: function (result) {
                if (result.state == "success") {
                    window.alert("Submit Successfully");
                    geticon();
                    $('#hint').html('');
                } else {
                    window.alert("Fail to submit, please try again");
                }
            },
            error: function (result) {
                window.alert(result);
            }
        });
    }
});

$('#resumes-tab').click(function () {
    $('#resumetable').attr('src', $('#resumetable').attr('src'));
})

$('#offers-tab').click(function () {
    $('#offerstable').attr('src', $('#offerstable').attr('src'));
})
