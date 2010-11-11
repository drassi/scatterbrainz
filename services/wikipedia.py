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
    req.add_header("User-Agent", "Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.11 Safari/534.10")
    log.info('[wiki] hitting ' + url)
    page = lxml.parse(urllib2.urlopen(req)).getroot()
    bodyContent = page.cssselect('#bodyContent')[0]
    bodyContent.make_links_absolute()
    for a in bodyContent.cssselect('a'):
        a.attrib['target'] = '_blank'
    for citation in bodyContent.cssselect('sup.reference'):
        citation.drop_tree()
    summary = ''
    for child in bodyContent.getchildren():
        if child.tag == 'p':
            summary = summary + lxml.tostring(child)
        if child.tag == 'table' and 'class' in child.attrib and child.attrib['class'] == 'toc':
            break
    return summary

