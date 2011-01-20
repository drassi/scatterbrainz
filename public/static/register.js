$(function() {
    $.getJSON('/logout_handler');
    $('#submit').one('click', handle);
});

function handle() {
    $.getJSON('/create', {
        login : $('#login').val(),
        pass : $('#password').val(),
        code : $('#code').val()
    }, function(data) {
        if (data['success']){
            $('form').submit();
        } else {
            alert(data['msg']);
            $('#submit').one('click', handle);
        }
    });
}

