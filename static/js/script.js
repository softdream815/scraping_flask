$(document).ready(function(){
    $.ajax({
        // Uncomment the following to send cross-domain cookies:
        //xhrFields: {withCredentials: true},
        url: "/ocr",
        context: $('#fileform')[0]
    })
    .always(function () {
        console.log("progressing")
    })
    .done(function (result) {
        $("#upload_image").attr("src", result );
        console.log("done", result);
    });
})