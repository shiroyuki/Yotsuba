'''
CMS framework for software development project.

Routing map:
    GET/*       /           homepage
    POST        /*          create/update a page (dynamic, auth)
    GET         /*/edit     editor for the page (dynamic, auth)
    GET         /*          display the page, response error or create a new page (dynamic)
    DELETE      /*          delete the page (dynamic, auth)
    GET         /*/toc      table of content

@author: Juti Noppornpitak
'''
import re

from yotsuba3.core import base
from yotsuba3.core import graph
from yotsuba3.lib import tori
from yotsuba3.lib import aria

import yotsuba

detect_Pygments = True
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
except:
    detect_Pygments = False

PACKAGE_VERSION = 1.0

class registeredPage:
    index = 'index'

class registeredMode:
    editContent = 'edit'
    listPageHierarchy = 'toc'

class Page(graph.Vertex):
    pass

class Tsumekusa(tori.BaseInterface):
    '''
    CMS framework for software development project.
    
    This is a local plugin for Yotsuba's Tori Framework.
    '''
    useStaticFile = True
    __name = None
    __templates = None
    __sitemap = None
    __JSCodeRendering = """
        <script type="text/javascript">
            $(document).ready(function() {
                $("code[lang]").each(function (index) {
                    var targetElement = this;
                    var makeRenderingRequest = true;
                    
                    $(this).parents().each( function() {
                        if (this.tagName == "CODE" && $(this).attr("lang") != "") {
                            makeRenderingRequest = false;
                            return false;
                        }
                        return true;
                    });
                    
                    if (makeRenderingRequest) {
                        setTimeout(function() {
                            makeAJAXRenderingRequest(targetElement, index);
                        }, 200);
                    } else {
                        /*console.log("One code block didn't get rendered");*/
                    }
                });
            });
            function makeAJAXRenderingRequest(elem, index) {
                var targetID = "hlcode_" + index;
                var targetLang = $(elem).attr("lang");
                var targetCode = $(elem).html();
                $(elem).addClass(targetID);
                $(elem).css("color","#000");
                $(elem).animate({paddingLeft:10}, 500);
                $(elem).html('<span style="font-family: Arial;">Rendering...</span>');
                $.post(
                    "${projectBaseURI}/do/syntaxHighlight",
                    {
                        lang: targetLang,
                        code: targetCode
                    }, function (localResponse) {
                        var localTarget = $("." + targetID);
                        localTarget.find("span").html("Done");
                        localTarget.find("span").animate(
                            {
                                paddingLeft: 100,
                                opacity: 0
                            }, 500, function() {
                                localTarget.replaceWith(localResponse);
                            } /* Post-processing */
                        ); /* Animation */
                    } /* Callback */
                );
            }
        </script>
    """
    
    def __init__(self, name, templates, feedURL = None, sitemap = None, cacheDuration = -1):
        self.name, self.__templates, self.__feedURL = name.strip(), templates, feedURL
        self.sitemap = self.drawSitemap(sitemap)
        self.__JSCodeRendering = self.localRender(self.__JSCodeRendering)
        self.__cacheDuration = cacheDuration
        super(tori.BaseInterface, self).__init__()
    
    def do(self, command, **kwargs):
        '''
        Local web APIs mainly for utilities and AJAX operations.
        '''
        
        if detect_Pygments and command == "syntaxHighlight":
            code = kwargs['code']
            lang = kwargs['lang']
            lexer = get_lexer_by_name(lang)
            output = u"<style type=\"text/css\">%s</style>\n\n%s" % (HtmlFormatter().get_style_defs('.highlight'), highlight(code, lexer, HtmlFormatter(linenos = True)))
            return output
        
    do.exposed = True
    
    def default(self, *paths):
        cacheBlockName = "%s/%s" % (self.name, '/'.join(paths))
        if self.isGET() and self.cache(cacheBlockName) is not None:
            return self.cache(cacheBlockName)
        
        # Response context
        responseContext = None
        
        # Disable editor mode by default
        editorCalled = False
        
        # Page mode: reading, editing, overview (TOC)
        pageMode = len(paths) > 1 and paths[-1] or None
        if pageMode not in [registeredMode.editContent, registeredMode.listPageHierarchy]:
            pageMode = None # Assume the reading mode
        
        # Get the whole request path (in array bit) without the page mode
        path = len(paths) == 0 and registeredPage.index or '/'.join(pageMode == None and paths or paths[:-1])
        
        # Breadcrumb
        breadcrumb = []
        requestedPath = None
        if len(paths) > 0:
            urlpath = []
            requestedPath = '/'.join(paths[1:])
            for p in paths:
                urlpath.append(p)
                currentPath = '/'.join(urlpath)
                p = self.convertToFullName(p)
                breadcrumb.append({
                    'URL': currentPath,
                    'Full name': p,
                    'Short name': self.convertToShortName(p)
                })
            del urlpath
        
        currentPage = len(breadcrumb) > 0 and breadcrumb[-1] or None
        
        pageObject = self.getPageObject(path)
        backupPageObject = self.getBackupPageObject(path)
        
        if self.isGET() and pageMode == None:
            isIndexPage = path == registeredPage.index
            doPageExisted = isIndexPage or pageObject is not None or backupPageObject is not None
            
            # General information
            generalInformation = {
                'breadcrumb':  breadcrumb,
                'currentPage': currentPage
            }
            
            # [General procedure]
            # 1. Retrieve the subpages (1 level deep) if necessary
            # 2. Render the page object by prioritizing the (HTML) sources in the following order:
            #   1. Database entry
            #   2. Flat file from archive
            #   3. Flat file from template
            
            # Prioritize the one in the database first.
            if pageObject is not None and not self.useStaticFile:
                pass
            # Prioritize the one in the database first.
            if pageObject is not None and self.useStaticFile:
                # Initialize data
                templateID = "default" # templateID
                subpages = None # list of subpages
                pathToPageObject = self.getAbsolutePathToPageObject(path) # path to the page object
                preProcessedPageData = yotsuba.fs.read(pathToPageObject) # pre-processed page data
                
                # Look for requirements
                local_flags = re.search("<!--\s*require\s*([a-zA-Z0-9\-\+_]+)\s*-->", preProcessedPageData)
                
                if local_flags is not None:
                    # If detect the traversal flag for subpages, do it.
                    if 'subpages' in local_flags.groups():
                        subpages = []
                        possibleDirectory = self.removeExtension(pathToPageObject)
                        
                        if yotsuba.fs.exists(possibleDirectory):
                            rawSubpages = yotsuba.fs.browse(possibleDirectory, True)['files']
                            for p in rawSubpages:
                                p = re.sub("^" + possibleDirectory + "/", "", p)
                                p = self.removeExtension(p)
                                if p == "index":
                                    continue
                                subpages.append((self.convertToFullName(p), p))
                        generalInformation['subpages'] = subpages
                    
                    # If detect the traversal flag for neighbours, do it.
                    if 'neighbours' in local_flags.groups():
                        neighbours = []
                        possibleDirectory = re.sub("/[^/]+$", "", self.removeExtension(pathToPageObject))
                        
                        if yotsuba.fs.exists(possibleDirectory):
                            rawSubpages = yotsuba.fs.browse(possibleDirectory, True)['files']
                            for p in rawSubpages:
                                p = re.sub("^" + possibleDirectory + "/", "", p)
                                p = self.removeExtension(p)
                                if p == "index":
                                    continue
                                neighbours.append((self.convertToFullName(p), p))
                        generalInformation['neighbours'] = neighbours
                    
                    # If require syntax highlighting, add the JS code
                    if 'syntax_highlight' in local_flags.groups():
                        preProcessedPageData += self.__JSCodeRendering
                
                # Determine if it needs a special template
                local_flags = re.search("<!--\s*template\s*(?P<templateID>\W+)\s*-->", preProcessedPageData)
                if local_flags is not None:
                    local_templateID = local_flags.group("templateID")
                    if local_templateID in self.__templates:
                        templateID = local_templateID
                
                responseContext = self.localRender(preProcessedPageData, **generalInformation)
                responseContext = self.localRender(self.__templates[templateID], responseContext = responseContext, **generalInformation)
            elif backupPageObject is not None:
                if self.__feedURL is not None:
                    type, url = self.__feedURL.split(":", 2)
                    type = type.lower()
                    if type == "rss":
                        generalInformation['newsfeeds'] = aria.Feeds.makeFromRSSFeed(self.__feedURL, cacheLocation = tori.path['session'])
                    else:
                        generalInformation['newsfeeds'] = aria.Feeds()
                
                responseContext = self.localRender(backupPageObject, **generalInformation)
            
            if not doPageExisted and self.isAdmin() and False:
                editorCalled = True
                
        elif self.isGET() and pageMode in registeredMode.editContent:
            editorCalled = True
            
        elif self.isGET() and pageMode == registeredMode.listPageHierarchy:
            responseContext = tori.UserInterface.response("Table of content (index mode) requested")
            
        elif self.isPOST():
            responseContext = tori.UserInterface.response("Creating/updating called")
            
        elif self.isDELETE():
            responseContext = tori.UserInterface.response("Creating/updating called")
            
        # endif
        
        if editorCalled:
            responseContext = self.loadEditor(pageMode, '/'.join(len(paths) > 1 and paths[1:-1] or []))
        elif not editorCalled and responseContext is None:
            self.respondStatus(404)
        else:
            self.cache(cacheBlockName, responseContext, self.__cacheDuration)
        
        return responseContext
    default.exposed = True
    
    def drawSitemap(self, sitemap, parentLocation = None):
        if base.isList(sitemap):
            baseRelativeURI = ''
            currentLocation = None
            
            if parentLocation is None:
                currentLocation = graph.Vertex("root")
                currentLocation.relativeURI = baseRelativeURI
            else:
                currentLocation = parentLocation
                baseRelativeURI = parentLocation.relativeURI
            
            prevPage = None
            for page in sitemap:
                if base.isList(page):
                    self.drawSitemap(page, prevPage)
                else:
                    pageName = base.isTuple(page) and page[0] or page
                    pageShortName = base.isTuple(page) and page[1].strip() or self.convertToShortName(pageName)
                    
                    # Page: reference
                    pageRef = graph.Vertex(self.convertToFullName(pageName))
                    
                    # Page: direct link
                    pageRef.directLink = re.search("^https?://", pageShortName) and page[1] or None
                    
                    # Page: relative link
                    if pageShortName == '/':
                        pageRef.relativeURI = ''
                    else:
                        pageRef.relativeURI = re.search("^/", pageShortName) and pageShortName or (baseRelativeURI == '' and pageShortName or baseRelativeURI + '/' + pageShortName)
                    
                    prevPage = pageRef
                    currentLocation.makeEdgeTo(pageRef)
            
            return currentLocation
        return None
    
    def getRelativePathToPageObject(self, path):
        if len(self.name) > 0:
            relativePathToPageObjectFile = self.name + "/" + path + ".html"
        else:
            relativePathToPageObjectFile = path + ".html"
        return relativePathToPageObjectFile
    
    def getAbsolutePathToArchive(self):
        return tori.basePath + '/' + tori.settings['Tsumekusa:Archive']
    
    def getAbsolutePathToPageObject(self, path):
        return self.getAbsolutePathToArchive() + "/" + self.getRelativePathToPageObject(path)
    
    def getPageObject(self, path):
        '''
        Get the page object from the archive folder.
        '''
        retvar = None
        if self.useStaticFile:
            pathToPageObjectFile = self.getAbsolutePathToPageObject(path)
            retvar = yotsuba.fs.exists(pathToPageObjectFile) and True or None
        return retvar
    
    def getBackupPageObject(self, path):
        '''
        Get the backup page object from the template folder.
        '''
        retvar = None
        relativePathToPageObjectFile = self.getRelativePathToPageObject(path)
        pathToPageObjectFile = tori.path['template'] + "/" + relativePathToPageObjectFile
        retvar = yotsuba.fs.exists(pathToPageObjectFile) and relativePathToPageObjectFile or None
        return retvar
    
    def loadEditor(self, mode, parentHierarchy):
        mode = mode != registeredMode.editContent and "New page" or "Edit page"
        return ''
    
    def localRender(self, filename, **kwargs):
        return self.render(
            filename,
            projectName = self.convertToFullName(self.name),
            projectShortName = self.convertToShortName(self.name),
            projectBaseURI = self.getProjectBaseURI(),
            sitemap = self.sitemap,
            **kwargs
        )
    
    def removeExtension(self, path):
        return re.sub("\.html$", "", path)
    
    def getProjectBaseURI(self):
        return tori.baseURI + '/' + self.convertToShortName(self.name)
    
    def convertToFullName(self, name):
        name = re.sub("_", " ", name)
        return name
    
    def convertToShortName(self, name):
        name = re.sub(" ", "_", name)
        return name
