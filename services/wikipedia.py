import urllib2
import logging
import lxml.html as lxml

log = logging.getLogger(__name__)

"""
Return the HTML of the first few <p>'s (preceding the TOC)
of the wikipedia article at the given URL, with:

* links converted from relative to absolute against the given url
* target='_blank' attribute added to links
* strip out superscript citations (like [1])
"""
def get_summary(url):
    req = urllib2.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7")
    log.info('[wiki] hitting ' + url)
    handle = urllib2.urlopen(req)
    page = lxml.parse(handle).getroot()
    bodyContent = page.cssselect('#bodyContent div.mw-content-ltr')[0]
    bodyContent.make_links_absolute()
    for a in bodyContent.cssselect('a'):
        a.attrib['target'] = '_blank'
    for citation in bodyContent.cssselect('sup.reference'):
        citation.drop_tree()
    summary = ''
    for child in bodyContent.getchildren():
        if child.cssselect('table.toc'):
            break
        elif child.tag == 'p':
            summary = summary + lxml.tostring(child)
    fishy = (url != handle.geturl()) or 'Category:Disambiguation' in lxml.tostring(page)
    return summary, fishy

