$(function () {
    var code = $('a').text();
    var location = window.location.protocol + '//' + window.location.host + '/register/' + code;
    $('a').attr('href', location).text(location);
});

