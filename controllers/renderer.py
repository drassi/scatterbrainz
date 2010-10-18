from urllib import pathname2url

def minsec(sec):
    return "%d:%02d" % (sec / 60, sec % 60)

def filepath(track):
    return pathname2url(('/music/' + track.filepath).encode('utf-8'))

def artist(track):
    return track.id3artist
    
def title(track):
    return track.id3title

def album(track):
    return track.id3album

def tracknum(track):
    return track.getTrackNum() or ''

def length(track):
    return minsec(track.mp3length)

def bitrate(track):
    return track.mp3bitrate / 1000
