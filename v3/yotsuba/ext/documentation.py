# -*- encoding: utf-8 -*-
import re

from yotsuba.core import graph
from yotsuba.core import mt
from yotsuba.lib import kotoba
from yotsuba.lib import tori

class Node(graph.Vertex):
    def __init__(self, name, type=None, doc=None, version=None, params=None):
        super(Node, self).__init__(name)
        self.version = version
        self.type = type
        self.doc = doc
        self.params = []
        if params: self.params.extend(params)
    
    def actual_name(self):
        return re.split('\.', self.name)[-1]
    
    def readable_params(self):
        return ', '.join(self.params)
    
    def readable_type(self):
        if type(self.type) is str: return self.type
        t = str(self.type)
        t = re.split("'", t)[1]
        if t == 'type':
            t = 'class'
        elif t in ['instancemethod', 'method_descriptor']:
            t = 'method'
        return t
    
    def documentation(self):
        if not self.doc: return ''
        doc = self.doc.strip()
        lines = []
        raw_lines = re.split('\n', doc)
        for line in raw_lines:
            if not line.strip():
                lines.append('</p><p>')
            else:
                s = '\*([\w_\.]+)\*'
                m = re.search(s, line)
                while m:
                    line = re.sub('\*%s\*' % m.group(1), '<b>%s</b>' % m.group(1), line)
                    m = re.search(s, line)
                lines.append(line)
        return ''.join(lines)

def package_scanner():
    targets = {
        'graph': graph,
        'mt': mt,
        'kotoba': kotoba,
        'tori': tori
    }
    
    packages = []
    
    omit = dir(object)
    
    coverage_current_score = 0
    coverage_total_score = 0
    
    for name, ref in targets.iteritems():
        coverage_total_score += 1
        
        ver = ref.__version__
        doc = ref.__doc__
        
        if doc: coverage_current_score += 1
        
        packages.append(Node(name, 'package', doc, ver))
        
        try:    sub_modules = ref.__scan_only__
        except: sub_modules = dir(ref)
        for sub_module in sub_modules:
            otype = None
            odoc = None
            if type(sub_module) is tuple:
                otype = sub_module[1]
                try:    odoc = sub_module[2]
                except: odoc = None
                sub_module = sub_module[0]
            
            if sub_module in omit: continue
            if sub_module[0] == '_': continue
            
            m = {'name': '%s.%s' % (name, sub_module)}
            m['type'] = otype and otype or eval("type(%s)" % m['name'])
            m['doc'] = odoc and odoc or eval("%s.__doc__" % m['name'])
            
            m = Node(**m)
            
            sref = eval(m.name)
            
            if m.readable_type() == 'module': continue
            
            if m.readable_type() == 'function':
                m.params = eval("%(n)s.__code__.co_varnames[0:%(n)s.__code__.co_argcount]" % {'n':m.name})
            
            if m.readable_type() == 'class':
                try:
                    m.params = eval("%(n)s.__init__.im_func.__code__.co_varnames[1:%(n)s.__init__.im_func.__code__.co_argcount]" % {'n':m.name})
                except:
                    pass
                
                try:    lv2_modules = sref.__scan_only__
                except: lv2_modules = dir(sref)
                for lv2_module in lv2_modules:
                    otype = None
                    odoc = None
                    if type(lv2_module) is tuple:
                        otype = lv2_module[1]
                        try:    odoc = lv2_module[2]
                        except: odoc = None
                        lv2_module = lv2_module[0]
                    
                    if lv2_module in omit: continue
                    if lv2_module[0] == '_': continue
                    if re.search("^[A-Z_]+$", lv2_module): continue
                    
                    sm = {'name': '%s.%s' % (m.name, lv2_module)}
                    sm['type'] = otype and otype or eval("type(%s)" % sm['name'])
                    sm['doc'] = odoc and odoc or eval("%s.__doc__" % sm['name'])
                    
                    sm = Node(**sm)
                    
                    if sm.readable_type() == 'function':
                        sm.params = eval("%(n)s.__code__.co_varnames[0:%(n)s.__code__.co_argcount]" % {'n':sm.name})
                    
                    if sm.readable_type() == 'instancemethod':
                        sm.params = eval("%(n)s.im_func.__code__.co_varnames[1:%(n)s.im_func.__code__.co_argcount]" % {'n':sm.name})
                    
                    if sm.doc: coverage_current_score += 1
                    
                    m.make_edge_to(sm)
                    
                    coverage_total_score += 1
            
            if m.doc: coverage_current_score += 1
            
            packages[-1].make_edge_to(m)
            
            coverage_total_score += 1
        
        coverage_ratio = float(coverage_current_score) / coverage_total_score
        
    return coverage_ratio, packages