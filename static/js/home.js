function resizeIframe(obj) {
    obj.style.height = 0;
    obj.style.height = obj.contentWindow.document.body.scrollHeight + 10 + 'px';
}

$('#sorted_direction').hide();

$('#sorted_parameter').change(function () {
    var checkValue = $("#sorted_parameter").val();
    if (checkValue == "default") {
        $('#sorted_direction').hide();
    } else {
        $('#sorted_direction').show();
        if (checkValue == "salary") {
            $('#sorted_direction option[value="1"]').text('From high to low');
            $('#sorted_direction option[value="0"]').text('From low to high');
        }
        else if (checkValue == "time") {
            $('#sorted_direction option[value="1"]').text('From latest to oldest');
            $('#sorted_direction option[value="0"]').text('From oldest to latest');
        }
        else if (checkValue == "hot") {
            $('#sorted_direction option[value="1"]').text('From most popular to less popular');
            $('#sorted_direction option[value="0"]').text('From less popular to most popular');
        }
    }


})


$("#submit").click(function () {
    $("#result").html("<font class=\"title_word\">Searching Result</font>" +
        "<div class='holds-the-iframe' style=\"width: 100%;\">");
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "/search",
        data: $("#searchlist").serialize(),
        beforeSend: function (result) {
            $("#result").html("<font class=\"title_word\">Searching Result</font>" +
                "<div class='holds-the-iframe' style=\"width: 100%;\">");
            // "<iframe id='resultpage' src=\"/searchresult/1\" style=\"width: 100%;overflow-y: hidden;\"onload='resizeIframe(this)'></iframe></div>");
        },
        success: function (result) {
            $("#home-tab").removeClass("active");
            $("#home").removeClass("show active");
            $("#seekers-tab").addClass("active");
            $("#seekers").addClass("show active");
            $("#result").html("<font class=\"title_word\">Searching Result</font>" +
                "<div class='holds-the-iframe' style=\"width: 100%;\">" +
                "<iframe id='resultpage' src=\"/searchresult/1\" style=\"width: 100%;overflow-y: hidden;\"onload='resizeIframe(this)'></iframe></div>");
        }
    })
})

$("#submitmore").click(function () {
    $("#result").html("<font class=\"title_word\">Searching Result</font>" +
        "<div class='holds-the-iframe' style=\"width: 100%;\">");
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "/search",
        data: $("#searchmore").serialize(),
        beforeSend: function (result) {
            $("#result").html("<font class=\"title_word\">Searching Result</font>" +
                "<div class='holds-the-iframe' style=\"width: 100%;\">");
            // "<iframe id='resultpage' src=\"/searchresult/1\" style=\"width: 100%;overflow-y: hidden;\"onload='resizeIframe(this)'></iframe></div>");
        },
        success: function (result) {
            $("#result").html("<font class=\"title_word\">Searching Result</font>" +
                "<div class='holds-the-iframe' style=\"width: 100%;\">" +
                "<iframe id='resultpage' src=\"/searchresult/1\" style=\"width: 100%;overflow-y: hidden;\"onload='resizeIframe(this)'></iframe></div>");
        }
    })
})

$("#submitrequest").click(function () {
    $("#seeker_result").html("<font class=\"title_word\">Searching Result</font>" +
        "<div class='holds-the-iframe' style=\"width: 100%;\">");
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "/search_employer",
        data: $("#searchrequest").serialize(),
        beforeSend: function (result) {
            $("#request_result").html("<font class=\"title_word\">Searching Result</font>" +
                "<div class='holds-the-iframe' style=\"width: 100%;\">");
        },
        success: function (result) {
            $("#request_result").html("<font class=\"title_word\">Searching Result</font>" +
                "<div class='holds-the-iframe' style=\"width: 100%;\">" +
                "<iframe id='result_request_page' src=\"/requestresult/1\" style=\"width: 100%;overflow-y: hidden;\"onload='resizeIframe(this)'></iframe></div>");
        }
    })
})