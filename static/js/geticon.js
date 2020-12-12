function geticon() {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: "/geticon",
        success: function (result) {
            if (result.icon != null) {
                $('#dropdownMenuButton').attr('src',result.icon+'?timestamp=' + new Date().getTime());
            }
        }
    });
}

$(function(){
    geticon();
})