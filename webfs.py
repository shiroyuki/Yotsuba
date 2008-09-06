# Yotsuba CoE WebFS "Web File System"
# (C) 2007 Juti Noppornpitak <juti_n@yahoo.co.jp>
# LGPL License
import core, webec, jfs

core.installed_packages['webfs'] = core.PackageProfile("Juti's Web File System", 0.02, core.PACKAGE_EXPERIMENTAL)

def webfs_save_uploaded_file_at(form_field, upload_dir):
    # Original Author: Noah Spurrier
    # This code depends on WebEC.
    fileitem = None
    try:
        if webec.ipc(form_field) == '': return
        fileitem = webec.ipc(form_field)
        if not fileitem[1]: return
    except:
        form = cgi.FieldStorage()
        if not form.has_key(form_field): return
        fileitem = form[form_field]
        if not fileitem.file: return
    fout = file (os.path.join(upload_dir, fileitem.filename), 'wb')
    while 1:
        chunk = fileitem.file.read(100000)
        if not chunk: break
        fout.write (chunk)
    fout.close()