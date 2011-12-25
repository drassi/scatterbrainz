$(document).ready(function(){

    $.ajaxSetup({ cache: false });

    $('#ajaxProgress').ajaxStart(function() { $(this).show(); })
                      .ajaxStop(function() { $(this).hide(); });

    /**
     * tablesorter and jquery UI sortable BS
     */

    $('#playlist').tablesorter();
    $('#playlistbody').sortable({ axis: 'y', opacity: 0.6,
        containment: 'parent',
        items: 'tr',
        placeholder: 'placeholder',
        distance: 15,
        tolerance: 'pointer'
    });
    $(".jp-playlist").droppable({
        drop: function(event, ui) {
            var browsenode = ui.draggable;
            if (browsenode.hasClass('browsenode')) {
                addToPlaylist(browsenode.attr('id'), event.originalEvent.target);
            } else {
                return;
            }
        }
    });
    
    $('li[rel=Playlist]').livequery(onTreeNodeCreate);
    $('li[rel=Album]').livequery(onTreeNodeCreate);
    treeNodeCreateEvent = document.createEvent('Event');
    treeNodeCreateEvent.initEvent('treeNodeCreateEvent', true, true);
 
    $('#browser').tree({
        data : { 
            async : true,
            type : 'json',
            opts : {
                url : '/hello/treeBrowseAJAX'
            }
        },
        callback : { 
            beforedata : function (n, t) {
                return { id : $(n).attr("id") || 'init' };
            },
            onrgtclk : function (a, b, c) {
                $('#treeContextMenu').css({'left': c.pageX - 11, 'top': c.pageY - 11}).show();
                return false;
            }
        },
        ui : {
            theme_name : 'default'
        },
        plugins : {
            hotkeys : { }
        },
        types : {
            'default' : {
                clickable	: true,
                renameable	: false,
                deletable	: false,
                creatable	: false,
                draggable	: false,
                max_children	: -1,
                max_depth	: -1,
                valid_children	: 'all',
                icon : {
                    image : false,
                    position : false
                }
            },
            'Artist': {
                icon: {
                    image: '/static/icons/artist.gif'
                }
            },
            'Album': {
                icon: {
                    image: '/static/icons/cd2small.gif'
                }
            },
            'Track': {
                icon: {
                    image: '/static/icons/note2small.jpg'
                }
            }
        }
    });

    /**
     * make browser nodes draggable w/ jquery ui live shit
     */
    $('li.browsenode').live("mouseover", function() {
        node = $(this);
        if (!node.data("init")) {
            node.data("init", true);
            node.draggable({
                opacity: 0.7,
                appendTo: '#playlistbody',
                cursorAt: {left: -1, top: -1},
                helper: function(event) {
                    return $('<span>').text(event.target.text);
                },
                distance: 15
            });
        }
    });
    
    $('li.browsenode[rel=Track]').live('dblclick', function () {
        var self = $(this);
        addToPlaylist(self.attr('id'));
    });

    /**
        * jplayer playlist BS
        */

    var global_lp = 0;
    $("#jquery_jplayer")
    .jPlayer( {
        ready: function () {
            $('.song').live('dblclick', play);
        }
    })
    .jPlayer("onSoundComplete", playListNextAndScrobble)
    .jPlayer("onProgressChange", function(lp,ppr,ppa,pt,tt) {
        var lpInt = parseInt(lp);
        var ppaInt = parseInt(ppa);
        global_lp = lpInt;

        $('#loaderBar').progressbar('option', 'value', lpInt);
        $('#sliderPlayback').slider('option', 'value', ppaInt);

    });
    
    audio = $('#jquery_jplayer').data('jPlayer.config').audio;

    $("#prev").click(playListPrev);
    $("#next").click(playListNext);
    $("#play").click(function() {
        if (!$('.playing').length && $('.song').length) {
            playRow($('.song:first'));
        } else if ($('.playing').length) {
            $('#play').hide();
            $('#pause').show();
            $("#jquery_jplayer").jPlayer("play");
        }
    });
    $("#pause").click(function() {
        $('#play').show();
        $('#pause').hide();
        $("#jquery_jplayer").jPlayer("pause");
    });

    $("#volume-min").click( function() {
        audio.muted = false;
        $("#volume-max").toggle();
        $("#volume-min").toggle();
    });

    $("#volume-max").click( function() {
        audio.muted = true;
        $("#volume-max").toggle();
        $("#volume-min").toggle();
    });

    $("#player_progress_ctrl_bar a").live( "click", function() {
        $("#jquery_jplayer").jPlayer("playHead", this.id.substring(3)*(100.0/global_lp));
        return false;
    });

    // Slider
    $('#sliderPlayback').slider({
        max: 100,
        range: 'min',
        animate: true,
        slide: function(event, ui) {
            $("#jquery_jplayer").jPlayer("playHead", ui.value*(100.0/global_lp));
        }
    });

    $('#sliderVolume').slider({
        value : 80,
        max: 100,
        range: 'min',
        animate: true,
        slide: function(event, ui) {
            $("#jquery_jplayer").jPlayer("volume", ui.value);
        }
    });

    $('#loaderBar').progressbar();


    //hover states on the static widgets
    $('#dialog_link, ul#icons li').hover(
        function() { $(this).addClass('ui-state-hover'); },
        function() { $(this).removeClass('ui-state-hover'); }
    );

    /**
     * Playlist interaction, shift click, ctrl click, del, etc
     */
    $('.song').live('click', function(e) {
        $('.jp-playlist').focus();
        var self = $(this);
        var lastselected = $('.lastSelected');
        if (lastselected.length > 0) {
            if (e.shiftKey) {
                if (self.prevAll('.lastSelected').length > 0) {
                    self.prevUntil('.lastSelected').addClass('selected');
                } else {
                    self.nextUntil('.lastSelected').addClass('selected');
                }
                $('.lastSelected').removeClass('lastSelected');
                self.addClass('selected').addClass('lastSelected');
                return true;
            } else if (e.ctrlKey) {
                self.toggleClass('selected').addClass('lastSelected');
                return true;
            }
        }
        $('.selected').removeClass('selected');
        $('.lastSelected').removeClass('lastSelected');
        self.addClass('selected').addClass('lastSelected');
        return true;
    });

    $('.jp-playlist').bind('keydown', 'ctrl+a', function() {
        $('.song').addClass('selected');
        return false;
    });

    $('.jp-playlist').bind('keydown', 'del', function() {
        var next = $('.selected:last').next('tr');
        var prev = $('.selected:first').prev('tr');
        $('.selected').not('.playing').remove();
        if (next.length) {
            next.addClass('selected').addClass('lastSelected');
        } else if (prev.length) {
            prev.addClass('selected').addClass('lastSelected');
        }
        return false;
    });

    $('.jp-playlist').bind('keydown', 'down', function() {

        var next = $('.lastSelected').next();
        if (next.length > 0) {
            $('.selected').removeClass('selected').removeClass('lastSelected');
        next.addClass('selected').addClass('lastSelected');
        scrollTo(next, $('.jp-playlist'));
        }

        return false;
    });

    $('.jp-playlist').bind('keydown', 'up', function() {
        var prev = $('.lastSelected').prev();
        if (prev.length > 0) {
            $('.selected').removeClass('selected').removeClass('lastSelected');
            prev.addClass('selected').addClass('lastSelected');
            scrollTo(prev, $('.jp-playlist'));
        }
        return false;
    });

    /**
     * Dispatch clicks to fake floating table header over to real table header
     */
    $('#playlistHeadTable th.artist').click(function() {
        $('#playlist th.artist').click();
    });
    $('#playlistHeadTable th.title').click(function() {
        $('#playlist th.title').click();
    });
    $('#playlistHeadTable th.album').click(function() {
        $('#playlist th.album').click();
    });
    $('#playlistHeadTable th.tracknum').click(function() {
        $('#playlist th.tracknum').click();
    });
    $('#playlistHeadTable th.length').click(function() {
        $('#playlist th.length').click();
    });
    $('#playlistHeadTable th.bitrate').click(function() {
        $('#playlist th.bitrate').click();
    });
    
    /**
     * Playlist functions
     */
    $('#playlistControlSave').click(savePlaylist);
    $('#playlistControlClear').click(clearPlaylist);
    $('#playlistControlTruncatePlayed').click(truncatePlayed);
    $('#playlistControlTruncateUnplayed').click(truncateUnplayed);
    $('#playlistControlRandomize').click(randomizePlaylist);

    /**
     * initialize search
     */
    $('#searchInput').keydown(function(e) {
        if(e.keyCode == 13) {
            searchHandler();
        } else if (e.keyCode == 27) {
            ditchSearch();
        }
    });

    $('#ditchSearch').click(ditchSearch)
        .button({
            icons: {
                primary: 'ui-icon-circle-close'
            },
            text: false
        });

    $('#goSearch').click(searchHandler)
        .button({
            icons: {
                primary: 'ui-icon-circle-triangle-e'
            },
            text: false
        });

    $(window).resize(windowResize);

    $("#playMode").button({
        icons: {
            primary: 'ui-icon-refresh',
            secondary: 'ui-icon-triangle-1-s'
        }
    });

    $('#playModeMenu').buttonset();

    $('#playMode').click(function() {
        $('#playModeMenu').toggle();
    });
    
    $('#playModeMenu input').click(function() {
        $("#playMode .ui-button-text").text($(this).next().text());
        $('#playModeMenu').hide();
    });
    
    $('#playModeContainer').mouseleave(function() {
        $('#playModeMenu').hide();
    });
    
    $('#arepeat').button();
    $('#brepeat').button();
    $('#cancelrepeat').button();
    $('#arepeat').click(function() {
        $(document).data('arepeat', audio.currentTime);
        $(this).hide();
        $('#brepeat').show();
    });
    $('#brepeat').click(function() {
        var a = $(document).data('arepeat');
        var b = audio.currentTime;
        audio.currentTime = a;
        var interval = setInterval(function(){
            if (audio.currentTime > b) {
                audio.currentTime = a;
                console.log('repeat '+a+' '+b);
            }
        }, 50);
        $(document).data('abrepeatinterval', interval);
        $(this).hide();
        $('#cancelrepeat').show();
    });
    $('#cancelrepeat').click(function() {
        clearInterval($(document).data('abrepeatinterval'));
        $(this).hide();
        $('#arepeat').show();
    });
    
    setTimeout(function() {
        $("body").splitter({
            'sizeLeft' : true,
            'cursor'   : 'col-resize'
        });
        $(window).resize();
    }, 100);
    
    var idsearch = window.location.href.match(/id=.*\/\d+/);
    if (idsearch != null) {
        var id = idsearch[0].split('=')[1];
        $.getJSON(
            '/hello/getTracksAJAX',
            {'id': id},
            function(data) {
                addToPlaylistThenPlayCallback(data);
            }
        );
    }
    
    /** Shop **/
    $('form#shopSearchForm').submit(shopSearchSubmit);
    
    screenMappings = {
        'playlistNav' : {'selector' : $('.browsePane, #browsePaneSplitter')},
        'nowPlayingNav' : {'selector' : $('#nowPlayingContainer')},
        'artistNav' : {'selector' : $('#artistBrowserContainer')
                     , 'callback' : openArtistNav},
        'shopNav' : {'selector' : $('#shopContainer')
                    , 'callback' : refreshShopStatus}
    };
    
    $('div#navigation button.screen').click(function() {
        switchWindow($(this), true);
    });
    
    $('button#logout').click(function() {
        window.location = '/logout_handler';
    });
    
    $('a.artistLink').live('click', clickArtistLink);
    
    $('.albumToggle').change(toggleAlbumVisibility);
    $('#albumCheckbox').data('type', 'Album');
    $('#epCheckbox').data('type', 'EP');
    $('#liveCheckbox').data('type', 'Live');
    $('#compilationCheckbox').data('type', 'Compilation');
    $('#otherCheckbox').data('type', 'Other');
    
    $('.playAlbumButton').live('click', playAlbumHandler);
    $('.queueAlbumButton').live('click', queueAlbumHandler);
    $('.searchAlbumButton').live('click', searchAlbumHandler);
    
    $('span.shopAlbumSearchLink').live('click', searchForShopAlbum);
    
    /* Initialize playlists */
    $('div#switchBrowseMode').children('div').click(switchBrowseModeHandler);
    initializePlaylistTree();

    /* Create events for scrobbler */
    startPlayEvent = document.createEvent('Event');
    startPlayEvent.initEvent('startPlayEvent', true, true);
    endPlayEvent = document.createEvent('Event');
    endPlayEvent.initEvent('endPlayEvent', true, true);

    $('#treeContextMenu').hover(function() { }, function() { $(this).hide(); });

});

function switchWindow(self, runCallback) {
    if (!self.hasClass('selectedNav')) {
        var selected = $('.selectedNav');
        selected.removeClass('selectedNav');
        self.addClass('selectedNav');
        var windowOut = screenMappings[selected.attr('id')]
        windowOut['selector'].fadeOut();
        var windowIn = screenMappings[self.attr('id')];
        windowIn['selector'].fadeIn();
        if (runCallback && 'callback' in windowIn) {
            windowIn['callback']();
        }
        windowResize();
    }
}

function windowResize(target) {
    $(document).data('windowHeightPx', $(window).height());
    $(document).data('windowWidthPx', $(window).width());
    var elements = $(".expandHeightToFitBrowser");
    for (var i=0; i<elements.length; i++) {
        expandHeightToFitBrowser($(elements[i]));
    }
}

function expandHeightToFitBrowser(element) {
    var elementTopPx = element.offset().top;
    var elementOffsetPx = element.attr('expandHeightOffsetPx');
    var elementHeightPx = $(document).data('windowHeightPx') - elementTopPx - elementOffsetPx;
    element.height(elementHeightPx);
}

function scrollTo(e, c) {

    if (!e) {
        return;
    }

    var eTop = e.offset().top;
    var eBottom = eTop + e.height();
    var cTop = c.offset().top;
    var cBottom = cTop + c.height();

    if ((eBottom > cBottom) || (eTop < cTop)) {
        if (eBottom > cBottom) {
            var scrollTop = c.attr('scrollTop') + (eBottom - cBottom) + 'px';
        } else if (eTop < cTop) {
            var scrollTop = c.attr('scrollTop') - (cTop - eTop) + 'px';
        }
        c.stop();
        c.animate({scrollTop: scrollTop}, 100);
    }

}

function scrollToBottom(c) {
    c.animate({scrollTop: c.attr('scrollHeight') + 'px'}, 500);
}

function scrollToTop(c) {
    c.animate({scrollTop: '0px'}, 500);
}

function addToPlaylist(id, target) {
    $(document).data('playlistDropTarget', target);
    $.getJSON(
        '/hello/getTracksAJAX',
        {'id': id},
        ($('.playing').length == 0) ? addToPlaylistThenPlayCallback : addToPlaylistCallback
    );
}

function addToPlaylistCallback(data) {
    var insertText = '';
    $.each(data, function(count, trackJSON) {
        insertText += '<tr id="track_'+trackJSON['id']+'" class="song" href="'
            +trackJSON['filepath']+'">'
        + '<td class="artist">'+trackJSON['artist']+'</td>'
        + '<td class="title">'+trackJSON['title']+'</td>'
        + '<td class="album">'+trackJSON['album']+'</td>'
        + '<td class="tracknum">'+trackJSON['tracknum']+'</td>'
        + '<td class="length">'+trackJSON['length']+'</td>'
        + '<td class="bitrate">'+trackJSON['bitrate']+'</td>'
        + '</tr>';
    });
    var dropTarget = $(document).data('playlistDropTarget');
    if (dropTarget && dropTarget.tagName == 'TD') {
        $(dropTarget).parent().after(insertText);
    } else {
        $("#playlistbody").append(insertText);
    }
    $('#playlist thead th').unbind('click');
    $('#playlist').tablesorter();
}

function addToPlaylistThenPlayCallback(data) {
    var last = $('.song:last');
    addToPlaylistCallback(data);
    if (last.length) {
        playRow(last.next());
    } else {
        playRow($('.song:first'));
    }
}

function searchHandler() {
    var searchStr = $('#searchInput').attr('value').trim();
    if (searchStr == "") {
        ditchSearch();
    } else {
        search(searchStr);
    }
}

function search(searchStr) {
    $.getJSON(
        '/hello/searchAJAX',
        {'search' : searchStr},
        searchCallback
    );
}

function searchCallback(results) {
    $('#browser').hide();
    $('#searchBrowser').show();
    $('#searchBrowser').tree({
        data : {
            async : true,
            type : 'json',
            opts : {
                url : '/hello/treeBrowseAJAX'
            }
        },
        callback : { 
            // Make sure static is not used once the tree has loaded for the first time
            onload : function (t) { 
                t.settings.data.opts.static = false; 
            },
            // Take care of refresh calls - n will be false only when the whole tree is refreshed or loaded of the first time
            beforedata : function (n, t) {
                if(n == false) t.settings.data.opts.static = results;
                return { id : $(n).attr("id") || 'init' };
            }
        },
        ui : {
            theme_name : 'default'
        },
        plugins : {
            hotkeys : { }
        },
        types : {
            'default' : {
                clickable	: true,
                renameable	: false,
                deletable	: false,
                creatable	: false,
                draggable	: false,
                max_children	: -1,
                max_depth	: -1,
                valid_children	: 'all',
                icon : {
                    image : false,
                    position : false
                }
            },
            'Artist': {
                icon: {
                    image: '/static/icons/artist.gif'
                }
            },
            'Album': {
                icon: {
                    image: '/static/icons/cd2small.gif'
                }
            },
            'Track': {
                icon: {
                    image: '/static/icons/note2small.jpg'
                }
            }
        }
    });
}

function onTreeNodeCreate() {
    var self = $(this);
    if (self.attr('rel') == 'Playlist') {
        self.prepend($('<span>').addClass('albumYear').text(self.attr('owner')));
    } else if (self.attr('rel') == 'Album') {
        self.prepend($('<span>').addClass('albumYear').text(self.attr('year')));
    }
    document.dispatchEvent(treeNodeCreateEvent);
}

function onPlaylistTreeLoad(thing, node) {
    console.log($('li[rel=Playlist]'));
    $.each($(node).find('li[rel=Playlist]'), function() {
        var self = $(this);
        self.prepend($('<span>').addClass('albumYear').text(self.attr('owner')));
        console.log('done');
    });
}

function ditchSearch() {
    $('#searchInput').attr('value', '');
    $('#browser').show();
    $('#searchBrowser').hide();
}

String.prototype.trim = function() {
    return this.replace(/^\s+|\s+$/g,"");
}


function playRow(row) {
    scrobbleEnd();
    $('.playing').removeClass('playing');
    $("#jquery_jplayer").jPlayer("setFile", row.attr('href')).jPlayer("play");
    row.addClass('playing');
    var artist = row.find('.artist').text();
    var title = row.find('.title').text();
    var min = Number(row.find('.length').text().split(':')[0]);
    var sec = Number(row.find('.length').text().split(':')[1]);
    var duration = min * 60 + sec;
    setDocumentTitle(artist + ' - ' + title);
    populatePlayingTrackInfo(row);
    $('#play').hide();
    $('#pause').show();
    $('#scrobbleArtist').text(artist);
    $('#scrobbleTrack').text(title);
    $('#scrobbleDuration').text(duration);
    document.dispatchEvent(startPlayEvent);
}
function scrobbleEnd() {
    if ($('.playing').length) {
        document.dispatchEvent(endPlayEvent);
    }
}

function setDocumentTitle(title) {
    document.title = title;
}

function stop() {
    scrobbleEnd();
    $('.playing').removeClass('playing');
    $("#jquery_jplayer").jPlayer("stop");
    $("#jquery_jplayer").jPlayer("setFile", '');
}

function play() {
    playRow($(this));
}

function playlistNextPrev(next) {
    var playing = $('.playing');
    if (playing.length) {
        if (next) {
            if (playing.next().hasClass('song')) {
                playRow(playing.next());
            } else if ($('#playlistRepeat').attr('checked')) {
                $('.song:first').dblclick();
            } else if ($('#playlistRandomTrack').attr('checked')) {
                nextRandomTrack();
            } else if ($('#playlistRandomAlbum').attr('checked')) {
                nextRandomAlbum();
            } else if ($('#playlistSimilarTrack').attr('checked')) {
                nextSimilarTrack(playing.attr('id'));
            } else if ($('#playlistRooTrack').attr('checked')) {
                nextRooTrack();
            } else if ($('#playlistRooAlbum').attr('checked')) {
                nextRooAlbum();
            } else {
                $('#play').show();
                $('#pause').hide();
                stop();
            }
        } else {
            if (playing.prev().hasClass('song')) {
                playRow(playing.prev());
            } else {
                $('#play').show();
                $('#pause').hide();
                stop();
            }
        }
    }
}

function playListPrev() {
    playlistNextPrev(false);
}

function playListNext() {
    playlistNextPrev(true);
}

function playListNextAndScrobble() {
    playListNext();
}

function savePlaylist() {
    var playlistName = prompt('Enter playlist name:\n\n' +
                              '* Re-saving a playlist created by you will overwrite it\n' +
                              '* Re-saving a playlist as empty will delete it');
    if (!playlistName) {
        return;
    }
    var trackids = $.map($('tr.song'), function(e) {return $(e).attr('id');});
    var trackidjson = JSON.stringify(trackids);
    $.post(
        '/hello/savePlaylistAJAX',
        {'name' : playlistName,
         'trackids' : trackidjson},
        reinitializePlaylistTree
    );
}

function clearPlaylist() {
    $('#playlistbody').children().not('.playing').remove();
}

function truncatePlayed() {
    $('tr.playing').prevAll().remove();
}

function truncateUnplayed() {
    $('tr.playing').nextAll().remove();
}

function randomizePlaylist() {
    $('#playlistbody').shuffle();
}

function nextRandomTrack() {
    $.getJSON(
        '/hello/randomTrackAJAX',
        {},
        playAJAXCallback
    );
}

function nextRandomAlbum() {
    $.getJSON(
        '/hello/randomAlbumAJAX',
        {},
        playAJAXCallback
    );
}

function nextSimilarTrack(id) {
    $.getJSON(
        '/hello/similarTrackAJAX',
        {'id':id},
        playAJAXCallback
    );
}

function nextRooTrack(id) {
    $.getJSON(
        '/hello/randomRooTrackAJAX',
        {},
        playAJAXCallback
    );
}

function nextRooAlbum(id) {
    $.getJSON(
        '/hello/randomRooAlbumAJAX',
        {},
        playAJAXCallback
    );
}

function playAJAXCallback(data) {
    var last = $('.song:last');
    $(document).data('playlistDropTarget', null);
    addToPlaylistThenPlayCallback(data);
}

function populatePlayingTrackInfo(row) {
    var artist = row.children('td.artist').text();
    $('#playingArtist').text(artist);
    $('#playingArtist').attr('title', artist);
    $('#nowPlayingArtistHeader').html(artist);
    var album = row.children('td.album').text();
    $('#playingAlbum').text(album);
    $('#playingAlbum').attr('title', album);
    $('#nowPlayingAlbumHeader').text(album);
    var track = row.children('td.title').text();
    $('#playingTrack').text(track);
    $('#playingTrack').attr('title', track);
    $('#nowPlayingTrackHeader').text(track);
    var trackid = row.attr('id');
    $.getJSON(
        '/hello/getAlbumArtAJAX',
        {'trackid': trackid},
        function(data) {
            if ('albumArtURL' in data) {
                $('img.albumArt').attr('src', data['albumArtURL']);
                $('a.albumArt').attr('href', data['albumArtURL']);
                $('a#nowPlayingAlbumArtImageLink').fancybox();
            } else {
                $('img.albumArt').removeAttr('src');
                $('img.albumArt.dashboardIcon').attr('src', '/static/icons/vinyl.png');
                $('#nowPlayingAlbumArtImage').attr('src', '/static/icons/coverunavailable.jpg');
                $('a.albumArt').removeAttr('href');
            }
        }
    );
    $.getJSON(
        '/hello/getLyricsAJAX',
        {'trackid': trackid},
        function(data) {
            if ('lyrics' in data) {
                $('#nowPlayingTrackLyrics').html(data['lyrics']);
            } else {
                $('#nowPlayingTrackLyrics').html('');
            }
            expandHeightToFitBrowser($('#nowPlayingTrackLyrics'));
        }
    );
    $.getJSON(
        '/hello/getArtistImagesAJAX',
        {'trackid': trackid},
        populateNowPlayingArtistImages
    );
    $.getJSON(
        '/hello/getAlbumInfoAJAX',
        {'trackid': trackid},
        function(data) {
            $('#nowPlayingAlbumInfo').empty();
            if ('wikipedia' in data) {
                $('#nowPlayingAlbumInfo').append($('<a>').attr('target','_blank')
                                                         .attr('href',data['wikipedia'])
                                                         .append($('<img>').addClass('linkicon')
                                                                           .attr('src','/static/icons/wiki.png')));
            }
            if ('musicbrainz' in data) {
                $('#nowPlayingAlbumInfo').append($('<a>').attr('target','_blank')
                                                         .attr('href',data['musicbrainz'])
                                                         .append($('<img>').addClass('linkicon')
                                                                           .attr('src','/static/icons/mb.png')));
            }
            if ('amazon' in data) {
                $('#nowPlayingAlbumInfo').append($('<a>').attr('target','_blank')
                                                         .attr('href',data['amazon'])
                                                         .append($('<img>').addClass('linkicon')
                                                                           .attr('src','/static/icons/amazon.png')));
            }
            if ('summary' in data) {
                $('#nowPlayingAlbumSummary').html(data['summary']);
            } else {
                $('#nowPlayingAlbumSummary').html('');
            }
            expandHeightToFitBrowser($('#nowPlayingAlbumSummary'));
        }
    );
    $.getJSON(
        '/hello/getArtistInfoAJAX',
        {'trackid': trackid},
        populateNowPlayingArtistInfo
    );
}

function openArtistNav() {
    var nowPlayingTrack = $('.playing');
    if (!nowPlayingTrack.length) {
        return;
    }
    var trackid = nowPlayingTrack.attr('id');
    $.getJSON(
        '/hello/getArtistFromTrackAJAX',
        {'trackid': trackid},
        populateArtistNavCallback
    );
}

function populateArtistNavCallback(data) {
    if ('mbid' in data) {
        populateArtistNav(data['mbid']);
    }
}
    
function populateArtistNav(artistMbid) {
    $.getJSON(
        '/hello/getArtistImagesAJAX',
        {'mbid': artistMbid},
        populateArtistBrowserArtistImages
    );
    $.getJSON(
        '/hello/getArtistInfoAJAX',
        {'mbid': artistMbid},
        populateArtistBrowserArtistInfo
    );
    $.getJSON(
        '/hello/getSimilarArtistsAJAX',
        {'mbid': artistMbid},
        populateArtistBrowserSimilarArtists
    );
    $.getJSON(
        '/hello/getAlbumsAndRelationshipsForArtistAJAX',
        {'mbid': artistMbid},
        populateArtistBrowserAlbumsRelationships
    );
}

function populateNowPlayingArtistImages(data) {
    populateArtistImages($('#nowPlayingArtistImageContainer'), data);
}

function populateArtistBrowserArtistImages(data) {
    populateArtistImages($('#artistBrowserArtistImageContainer'), data);
}

function populateArtistImages(container, data) {
    container.empty();
    if ('images' in data && data['images'].length > 0) {
        container.append(
            $('<a href="'+data['images'][0][1]+'" rel="artist">')
                .append('<img class="nowPlayingArtistImage" src="'+data['images'][0][1]+'">')
                .fancybox({speedIn : '100'}));
        for (var i=1; i<data['images'].length; i++) {
            container.append(
                $('<a href="'+data['images'][i][1]+'" rel="artist" style="display: none;">')
                    .fancybox({speedIn : '100'}));
        }
    } else {
        container.append(
            $('<img class="nowPlayingArtistImage" src="/static/icons/artistimageunavailable.jpg">')
        );
    }
}

function populateNowPlayingArtistInfo(data) {
    populateArtistInfo($('#nowPlayingArtistHeader'), $('#nowPlayingArtistInfo'), $('#nowPlayingArtistBio'), data);
}

function populateArtistBrowserArtistInfo(data) {
    populateArtistInfo($('#artistBrowserArtistHeader'), $('#artistBrowserArtistInfo'), $('#artistBrowserArtistBio'), data);
}

function populateArtistInfo(artistHeader, infoContainer, bioContainer, data) {
    artistHeader.empty();
    var credit = data['credit'];
    for (var i=0; i<credit.length;i++) {
        var c = credit[i];
        if ('mbid' in c) {
            artistHeader.append($('<a>').addClass('artistLink')
                                        .text(c['text'])
                                        .data('mbid', c['mbid']));
        } else {
            artistHeader.append(c['text']);
        }
    }
    infoContainer.empty();
    if ('wikipedia' in data) {
        infoContainer.append($('<a>').attr('target','_blank')
                                                  .attr('href',data['wikipedia'])
                                                  .append($('<img>').addClass('linkicon')
                                                                    .attr('src','/static/icons/wiki.png')));
    }
    if ('musicbrainz' in data) {
        infoContainer.append($('<a>').attr('target','_blank')
                                                  .attr('href',data['musicbrainz'])
                                                  .append($('<img>').addClass('linkicon')
                                                                    .attr('src','/static/icons/mb.png')));
    }
    if ('youtube' in data) {
        infoContainer.append($('<a>').attr('target','_blank')
                                                  .attr('href',data['youtube'])
                                                  .append($('<img>').addClass('linkicon')
                                                                    .attr('src','/static/icons/yt.png')));
    }
    if ('official' in data) {
        infoContainer.append($('<a>').attr('target','_blank')
                                                  .attr('href',data['official'])
                                                  .append($('<img>').addClass('linkicon')
                                                                    .attr('src','/static/icons/official.png')));
    }
    if ('bio' in data) {
        bioContainer.html(data['bio']);
    } else {
        bioContainer.html('');
    }
    expandHeightToFitBrowser(bioContainer);
}

function clickArtistLink() {
    var self = $(this);
    var mbid = self.data('mbid');
    populateArtistNav(mbid);
    switchWindow($('button#artistNav'), false);
}

function populateArtistBrowserSimilarArtists(data) {
    var sartists = data['similar'];
    $('#artistBrowserSimilarArtistsList').empty();
    for (var i=0; i<sartists.length; i++) {
        var sartist = sartists[i];
        var a = $('<a>').addClass('artistLink').data('mbid', sartist['mbid']).text(sartist['name']);
        var artist = $('<div>').append(a);
        if (sartist['local']) {
            artist.addClass('bold');
        }
        $('#artistBrowserSimilarArtistsList').append(artist);
    }
}

function populateArtistBrowserAlbumsRelationships(data) {

    var list = $('#artistBrowserRelationships');
    list.empty();
    if ('relationships' in data) {
        var relationships = data['relationships'];
        for (var i=0;i<relationships.length;i++) {
            var relationship = relationships[i];
            var text = relationship['text'];
            list.append('<b>' + text + '</b>');
            var rdata = relationship['data'];
            for (var j=0;j<rdata.length;j++) {
                var li = $('<li>').addClass('artistRelationship');
                var relationship = rdata[j];
                for (var k=0;k<relationship.length;k++) {
                    var r = relationship[k];
                    if ('mbid' in r) {
                        li.append($('<a>').addClass('artistLink')
                                          .text(r['text'])
                                          .data('mbid', r['mbid']));
                    } else {
                        li.append(r['text']);
                    }
                }
                list.append(li);
            }
        }
    }

    var albums = data['albums'];
    $('#artistBrowserAlbumList').empty();
    var albumCount = 0, epCount = 0, liveCount = 0, compilationCount = 0, otherCount = 0;
    for (var i=0; i<albums.length; i++) {
        var album = albums[i];
        var t = album['type'];
        var e = $('<div>').addClass('artistAlbum')
                          .addClass('albumType' + t)
                          .append($('<span>').addClass('albumTitle').text(album['name']))
                          .append($('<span>').addClass('albumYear2').text(album['year']))
                          .append($('<span>').addClass('albumType').text(t))
                          .data('mbid', album['mbid']);
        var checkbox;
        if (t == 'Album') {
            albumCount++;
            checkbox = $('#albumCheckbox');
        } else if (t == 'EP') {
            epCount++;
            checkbox = $('#epCheckbox');
        } else if (t == 'Live') {
            liveCount++;
            checkbox = $('#liveCheckbox');
        } else if (t == 'Compilation') {
            compilationCount++;
            checkbox = $('#compilationCheckbox');
        } else {
            otherCount++;
            checkbox = $('#otherCheckbox');
        }
        
        if (!checkbox.is(':checked')) {
            e.hide();
        }
        
        var buttons = $('<span>').addClass('albumButtons');
        if (album['local']) {
            e.addClass('bold');
            buttons.append($('<span>').addClass('ui-icon ui-icon-play playAlbumButton'))
                   .append($('<span>').addClass('ui-icon ui-icon-clock queueAlbumButton'));
        } else {
            buttons.append($('<span>').addClass('ui-icon ui-icon-search searchAlbumButton'));
        }
        
        e.append(buttons);
        $('#artistBrowserAlbumList').append(e);
    }
    $('#albumCount').text(albumCount);
    $('#epCount').text(epCount);
    $('#liveCount').text(liveCount);
    $('#compilationCount').text(compilationCount);
    $('#otherCount').text(otherCount);
    expandHeightToFitBrowser($('#artistBrowserAlbumList'));
}

function toggleAlbumVisibility() {
    var self = $(this);
    var type = self.data('type');
    var albums;
    if (type == 'Other') {
        albums = $('.artistAlbum').not('.albumTypeAlbum').not('.albumTypeEP').not('.albumTypeLive').not('.albumTypeCompilation');
    } else {
        albums = $('.albumType' + type);
    }
    if (self.is(':checked')) {
        albums.show();
    } else {
        albums.hide();
    }
}

function playAlbumHandler() {
    var mbid = $(this).parent().parent().data('mbid');
    $.getJSON(
        '/hello/getTracksAJAX',
        {'id': 'Album_' + mbid},
        addToPlaylistThenPlayCallback
    );
}

function queueAlbumHandler() {
    var mbid = $(this).parent().parent().data('mbid');
    $.getJSON(
        '/hello/getTracksAJAX',
        {'id': 'Album_' + mbid},
        addToPlaylistCallback
    );
}

function searchAlbumHandler() {
    var artist = $('#artistBrowserArtistHeader').text();
    var albumname = $(this).parents('.artistAlbum').children('.albumTitle').text();
    var year = $(this).parents('.artistAlbum').children('.albumYear2').text();
    var type = $(this).parents('.artistAlbum').children('.albumType').text();
    var mbid = $(this).parents('.artistAlbum').data('mbid');
    var album = {'artist' : artist, 'album' : albumname, 'year' : year, 'type' : type, 'mbid' : mbid};
    var e = $('<div>').addClass('artistAlbum')
                      .append($('<span>').addClass('shopAlbumArtist').text(album['artist']).attr('title', album['artist']))
                      .append($('<span>').addClass('shopAlbumAlbum').text(album['album']).attr('title', album['album']))
                      .append($('<span>').addClass('shopAlbumYear').text(album['year']))
                      .append($('<span>').addClass('shopAlbumType').text(album['type']))
                      .append($('<span>').addClass('shopAlbumSearchLink').text('Search').data('mbid', album['mbid']));
    $('div#shopSearchResults').empty();
    $('div#shopSearchResults').append(e);
    $('div#shopSearchResults').find('span.shopAlbumSearchLink:first').click();
    switchWindow($('button#shopNav'), true);
}

function shopSearchSubmit() {
    $('span#shopSearchStatus').text('Searching...');
    $.getJSON(
        '/hello/searchShopAJAX',
        {'artist': $('input#shopSearchArtist').attr('value'),
         'album': $('input#shopSearchAlbum').attr('value'),
         'mbid' : ''},
        showShopSearchResults
    );
    return false;
}

function showShopSearchResults(data) {
    var numlocal = data['numlocal'];
    var truncated = data['truncated'];
    var albums = data['albums'];
    $('div#shopSearchResults').empty();
    for (var i=0; i<albums.length; i++) {
        var album = albums[i];
        var e = $('<div>').addClass('artistAlbum')
                          .append($('<span>').addClass('shopAlbumArtist').text(album['artist']).attr('title', album['artist']))
                          .append($('<span>').addClass('shopAlbumAlbum').text(album['album']).attr('title', album['album']))
                          .append($('<span>').addClass('shopAlbumYear').text(album['year']))
                          .append($('<span>').addClass('shopAlbumType').text(album['type']))
                          .append($('<span>').addClass('shopAlbumSearchLink').text('Search').data('mbid', album['mbid']));
        $('div#shopSearchResults').append(e);
    }
    $('span#shopSearchStatus').text('');
}

function searchForShopAlbum() {
    $('span#shopSearchStatus').text('Searching...');
    var mbid = $(this).data('mbid');
    $.getJSON(
        '/hello/searchShopAlbumAJAX',
        {'mbid' : mbid},
        showShopAlbumSearchResults
    );
}

function showShopAlbumSearchResults(data) {
    if (data['success']) {
        $('span#shopSearchStatus').text('Success!');
    } else {
        $('span#shopSearchStatus').text('Not found, sorry.');
    }
    setTimeout(function() {
        $('span#shopSearchStatus').text('');
    }, 2000);
}

function refreshShopStatus() {
    if ($('div#shopContainer').is(':visible')) {
        $.getJSON(
            '/hello/checkDownloadStatusesAJAX',
            {},
            showShopStatuses
        );
    }
}

function showShopStatuses(data) {

    var downloads = data['downloads'];
    
    $('div#shopDownloading').empty();
    for (var i=0; i<downloads.length; i++) {
        var album = downloads[i];
        var pct = album['percent'] + '%';
        var e = $('<div>').addClass('artistAlbum')
                          .append($('<span>').addClass('shopAlbumArtist').text(album['artist']).attr('title', album['artist']))
                          .append($('<span>').addClass('shopAlbumAlbum').text(album['album']).attr('title', album['album']))
                          .append($('<span>').addClass('shopAlbumYear').text(album['year']))
                          .append($('<span>').addClass('shopAlbumType').text(album['type']))
                          .append($('<span>').addClass('shopAlbumPercent').text(pct))
                          .append($('<span>').addClass('shopAlbumProgress').width(pct))
                          .data('mbid', album['mbid']);
        $('div#shopDownloading').append(e);
    }
    
    var done = data['done'];
    $('div#shopDone').empty();
    for (var i=0; i<done.length; i++) {
        var album = done[i];
        var buttons = $('<span>').addClass('albumButtons')
                                 .append($('<span>').addClass('ui-icon ui-icon-play playAlbumButton'))
                                 .append($('<span>').addClass('ui-icon ui-icon-clock queueAlbumButton'));
        var e = $('<div>').addClass('artistAlbum').addClass('bold')
                          .append($('<span>').addClass('shopAlbumDoneArtist').text(album['artist']).attr('title', album['artist']))
                          .append($('<span>').addClass('shopAlbumDoneAlbum').text(album['album']).attr('title', album['album']))
                          .append($('<span>').addClass('shopAlbumDoneYear').text(album['year']).attr('title', album['year']))
                          .append($('<span>').addClass('shopAlbumDoneType').text(album['type']).attr('title', album['type']))
                          .append(buttons)
                          .append($('<span>').addClass('shopAlbumDoneUser').text(album['user']).attr('title', album['user']))
                          .data('mbid', album['mbid']);
        $('div#shopDone').append(e);
    }
    
    setTimeout(refreshShopStatus, 10000);
}

function switchBrowseModeHandler() {
    $('div.selectedBrowseMode').removeClass('selectedBrowseMode');
    $(this).addClass('selectedBrowseMode');
    if ($(this).attr('id') == 'playlistModeButton') {
        $('div#browseContainer').hide();
        $('div#playlistContainer').show();
    } else {
        $('div#browseContainer').show();
        $('div#playlistContainer').hide();
    }
    $(window).resize();
}

function initializePlaylistTree() {
    $('#playlistBrowser').tree({
        data : { 
            async : true,
            type : 'json',
            opts : {
                url : '/hello/playlistBrowseAJAX'
            }
        },
        callback : { 
            beforedata : function (n, t) {
                return { id : $(n).attr("id") || 'init' };
            }
            
        },
        ui : {
            theme_name : 'default'
        },
        plugins : {
            hotkeys : { }
        },
        types : {
            'default' : {
                clickable	: true,
                renameable	: false,
                deletable	: false,
                creatable	: false,
                draggable	: false,
                max_children	: -1,
                max_depth	: -1,
                valid_children	: 'all',
                icon : {
                    image : false,
                    position : false
                }
            },
            'Playlist': {
                icon: {
                    image: '/static/icons/artist.gif'
                }
            },
            'Track': {
                icon: {
                    image: '/static/icons/note2small.jpg'
                }
            }
        }
    });
}

function reinitializePlaylistTree() {
    $('#playlistBrowser').tree('destroy').empty();
    initializePlaylistTree();
}

(function($){
  $.fn.shuffle = function() {
    return this.each(function(){
      var items = $(this).children();
      return (items.length)
        ? $(this).html($.shuffle(items))
        : this;
    });
  }
 
  $.shuffle = function(arr) {
    for(
      var j, x, i = arr.length; i;
      j = parseInt(Math.random() * i),
      x = arr[--i], arr[i] = arr[j], arr[j] = x
    );
    return arr;
  }
})(jQuery);

