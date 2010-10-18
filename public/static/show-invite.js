$(function () {
    var code = $('a').text();
    var location = 'http://' + window.location.host + '/register/' + code;
    $('a').attr('href', location).text(location);
});

