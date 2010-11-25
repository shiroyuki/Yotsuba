'''
[Deplicated Module]
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

from yotsuba.core import base
from yotsuba.core import graph
from yotsuba.core import fs
from yotsuba.lib import tori
from yotsuba.lib import aria

detect_Pygments = True
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
except:
    detect_Pygments = False

__version__ = 0.99

class RegisteredPage:
    index = 'index'

class RegisteredMode:
    edit_content = 'edit'
    list_page_hierarchy = 'toc'

class Page(graph.Vertex):
    pass

class Tsumekusa(tori.BaseInterface):
    '''
    CMS framework for software development project.

    This is a local plugin for Yotsuba's Tori Framework.
    '''
    use_static_file = True
    __name = None
    __templates = None
    __sitemap = None
    __JS_code_rendering = """
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
                        makeAJAXRenderingRequest(targetElement, index);
                        /*setTimeout(function() {
                            makeAJAXRenderingRequest(targetElement, index);
                        }, 200);*/
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
                $(elem).animate({paddingLeft:10}, 100);
                $(elem).html('<span style="font-family: Arial;">Rendering...</span>');
                $.post(
                    "${project_base_uri}/do/syntaxHighlight",
                    {
                        lang: targetLang,
                        code: targetCode
                    }, function (localResponse) {
                        var localTarget = $("." + targetID);
                        localTarget.replaceWith(localResponse);
                        return;
                        localTarget.find("span").html("Done");
                        localTarget.find("span").animate(
                            {
                                paddingLeft: 100,
                                opacity: 0
                            }, 100, function() {
                                localTarget.replaceWith(localResponse);
                            } /* Post-processing */
                        ); /* Animation */
                    } /* Callback */
                );
            }
        </script>
    """

    def __init__(self, name, templates, sitemap = None, cache_duration = None):
        super(tori.BaseInterface, self).__init__()
        self.name, self.__templates = name.strip(), templates
        self.sitemap = self.draw_sitemap(sitemap)
        self.__JS_code_rendering = self.local_render(self.__JS_code_rendering)
        self.__cache_duration = cache_duration

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
        response_context = None

        # Disable editor mode by default
        editor_called = False

        # Page mode: reading, editing, overview (TOC)
        page_mode = len(paths) > 1 and paths[-1] or None
        if page_mode not in [RegisteredMode.edit_content, RegisteredMode.list_page_hierarchy]:
            page_mode = None # Assume the reading mode

        # Get the whole request path (in array bit) without the page mode
        path = len(paths) == 0 and RegisteredPage.index or '/'.join(page_mode == None and paths or paths[:-1])

        # Breadcrumb
        breadcrumb = []
        requested_path = None
        if len(paths) > 0:
            urlpath = []
            requested_path = '/'.join(paths[1:])
            for p in paths:
                urlpath.append(p)
                current_path = '/'.join(urlpath)
                p = self.convert_to_full_name(p)
                breadcrumb.append({
                    'URL': current_path,
                    'Full name': p,
                    'Short name': self.convert_to_shortname(p)
                })
            del urlpath

        current_page = len(breadcrumb) > 0 and breadcrumb[-1] or None

        page_object = self.get_page_object(path)
        backup_page_object = self.get_backup_page_object(path)

        if self.isGET() and page_mode == None:
            is_index_page = path == RegisteredPage.index
            do_page_existed = is_index_page or page_object is not None or backup_page_object is not None

            # General information
            general_information = {
                'breadcrumb':  breadcrumb,
                'current_page': current_page
            }

            # [General procedure]
            # 1. Retrieve the subpages (1 level deep) if necessary
            # 2. Render the page object by prioritizing the (HTML) sources in the following order:
            #   1. Database entry
            #   2. Flat file from archive
            #   3. Flat file from template

            # Prioritize the one in the database first.
            if page_object is not None and not self.use_static_file:
                pass
            # Prioritize the one in the database first.
            if page_object is not None and self.use_static_file:
                # Initialize data
                templateID = "default" # templateID
                subpages = None # list of subpages
                path_to_page_object = self.get_absolute_path_to_page_object(path) # path to the page object
                pre_processed_page_data = fs.read(path_to_page_object) # pre-processed page data

                # Look for requirements
                local_flags = re.search("<!--\s*require\s*([a-zA-Z0-9\-\+_]+)\s*-->", pre_processed_page_data)
                if local_flags is not None:
                    # If detect the traversal flag for subpages, do it.
                    if 'subpages' in local_flags.groups():
                        subpages = []
                        possible_directory = self.remove_extension(path_to_page_object)

                        if fs.exists(possible_directory):
                            raw_subpages = fs.browse(possible_directory, True)['files']
                            for p in raw_subpages:
                                p = re.sub("^" + possible_directory + "/", "", p)
                                p = self.remove_extension(p)
                                if p == "index" or p[0] == "_":
                                    continue
                                subpages.append((self.convert_to_full_name(p), p))
                        general_information['subpages'] = subpages

                    # If detect the traversal flag for neighbours, do it.
                    if 'neighbours' in local_flags.groups():
                        neighbours = []
                        possible_directory = re.sub("/[^/]+$", "", self.remove_extension(path_to_page_object))

                        if fs.exists(possible_directory):
                            raw_subpages = fs.browse(possible_directory, True)['files']
                            for p in raw_subpages:
                                p = re.sub("^" + possible_directory + "/", "", p)
                                p = self.remove_extension(p)
                                if p == "index" or p[0] == "_":
                                    continue
                                neighbours.append((self.convert_to_full_name(p), p))
                        general_information['neighbours'] = neighbours

                    # If require syntax highlighting, add the JS code
                    if 'syntax_highlight' in local_flags.groups():
                        pre_processed_page_data += self.__JS_code_rendering

                # Determine if it needs a special template
                local_flags = re.search("<!--\s*template\s*([^ ]+)\s*-->", pre_processed_page_data)
                if local_flags is not None:
                    local_templateID = local_flags.groups()[0]
                    if local_templateID in self.__templates:
                        templateID = local_templateID

                response_context = self.local_render(pre_processed_page_data, **general_information)
                response_context = self.local_render(self.__templates[templateID], response_context = response_context, **general_information)
            elif backup_page_object is not None:
                response_context = self.local_render(backup_page_object, **general_information)

            if not do_page_existed and self.isAdmin() and False:
                editor_called = True

        elif self.isGET() and page_mode in RegisteredMode.edit_content:
            editor_called = True

        elif self.isGET() and page_mode == RegisteredMode.list_page_hierarchy:
            response_context = tori.UserInterface.response("Table of content (index mode) requested")

        elif self.isPOST():
            response_context = tori.UserInterface.response("Creating/updating called")

        elif self.isDELETE():
            response_context = tori.UserInterface.response("Creating/updating called")

        # endif

        if editor_called:
            response_context = self.load_editor(page_mode, '/'.join(len(paths) > 1 and paths[1:-1] or []))
        elif not editor_called and response_context is None:
            self.respond_status(404)
        else:
            self.cache(cacheBlockName, response_context, self.__cache_duration)

        return response_context
    default.exposed = True

    def draw_sitemap(self, sitemap, parentLocation = None):
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
                    self.draw_sitemap(page, prevPage)
                else:
                    pageName = base.isTuple(page) and page[0] or page
                    pageShortName = base.isTuple(page) and page[1].strip() or self.convert_to_shortname(pageName)

                    # Page: reference
                    pageRef = graph.Vertex(self.convert_to_full_name(pageName))

                    # Page: direct link
                    pageRef.directLink = re.search("^https?://", pageShortName) and page[1] or None

                    # Page: relative link
                    if pageShortName == '/':
                        pageRef.relativeURI = ''
                    else:
                        pageRef.relativeURI = re.search("^/", pageShortName) and pageShortName or (baseRelativeURI == '' and pageShortName or baseRelativeURI + '/' + pageShortName)

                    prevPage = pageRef
                    currentLocation.make_edge_to(pageRef)

            return currentLocation
        return None

    def get_relative_path_to_page_object(self, path):
        if len(self.name) > 0:
            relativepath_to_page_objectFile = self.name + "/" + path + ".html"
        else:
            relativepath_to_page_objectFile = path + ".html"
        return relativepath_to_page_objectFile

    def get_absolute_path_to_archive(self):
        return tori.base_path + '/' + tori.settings['Tsumekusa:Archive']

    def get_absolute_path_to_page_object(self, path):
        return self.get_absolute_path_to_archive() + "/" + self.get_relative_path_to_page_object(path)

    def get_page_object(self, path):
        '''
        Get the page object from the archive folder.
        '''
        retvar = None
        if self.use_static_file:
            path_to_page_objectFile = self.get_absolute_path_to_page_object(path)
            retvar = fs.exists(path_to_page_objectFile) and True or None
        return retvar

    def get_backup_page_object(self, path):
        '''
        Get the backup page object from the template folder.
        '''
        retvar = None
        relativepath_to_page_objectFile = self.get_relative_path_to_page_object(path)
        path_to_page_objectFile = tori.path['template'] + "/" + relativepath_to_page_objectFile
        retvar = fs.exists(path_to_page_objectFile) and relativepath_to_page_objectFile or None
        return retvar

    def load_editor(self, mode, parentHierarchy):
        mode = mode != RegisteredMode.edit_content and "New page" or "Edit page"
        return ''

    def local_render(self, filename, **kwargs):
        kwargs['project_name'] = self.convert_to_full_name(self.name)
        kwargs['project_short_name'] = self.convert_to_shortname(self.name)
        kwargs['project_base_uri'] = self.get_project_base_URI()
        kwargs['sitemap'] = self.sitemap
        kwargs['direct_rendering'] = False
        
        return self.render(filename, **kwargs)

    def remove_extension(self, path):
        return re.sub("\.html$", "", path)

    def get_project_base_URI(self):
        return tori.base_uri + '/' + self.convert_to_shortname(self.name)

    def convert_to_full_name(self, name):
        name = re.sub("_", " ", name)
        return name

    def convert_to_shortname(self, name):
        name = re.sub(" ", "_", name)
        return name
