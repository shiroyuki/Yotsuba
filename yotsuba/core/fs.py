"""
Simple File System API for Yotsuba 3
"""
import os
import cPickle

# SDK.FS > Common Definitions
FILE            = 0
DIRECTORY       = 1
LINK            = 2
READ_NORMAL     = 'r'
READ_BINARY     = 'rb'
READ_PICKLE     = 'pickle::read'
WRITE_NORMAL    = 'w'
WRITE_BINARY    = 'wb'
WRITE_PICKLE    = 'pickle::write'

# Make directory
def mkdir(destpath):
    '''
    Make directory with `os.mkdir` at *destpath*
    
    Return true if no error is found during execution.
    '''
    try:
        os.mkdir(destpath)
        return True
    except:
        return False

# Check the size of file or directory
def size(destpath):
    '''
    Get the size of the content at *destpath*
    '''
    size = int(os.stat(destpath)[6])
    return size

# Friendly Path Identifier
def abspath(destpath, request_relative_path_fixed = False):
    if request_relative_path_fixed:
        return os.path.abspath( os.path.join(os.getcwd(), destpath) )
    else:
        return os.path.abspath( destpath )

# Symbol-instance checker
def check_type(destpath):
    if not os.path.exists(destpath):
        return -1
    if os.path.isfile( abspath( destpath) ) or (os.path.islink( abspath( destpath ) ) and os.path.isfile( abspath( destpath) ) ):
        return FILE
    return DIRECTORY

def exists(destpath):
    return    os.path.exists(destpath)

def readable(destpath):
    return    os.access(os.path.abspath(destpath), os.R_OK)

def writable(destpath):
    return    os.access(os.path.abspath(destpath), os.W_OK)

def executable(destpath):
    return    os.access(os.path.abspath(destpath), os.X_OK)

def isfile(destpath):
    return    check_type(destpath) == FILE

def isdir(destpath):
    return    check_type(destpath) == DIRECTORY

# Browsing Function
def browse(destpath, request_abspath_shown = False):
    # Check if this is a directory
    if not isdir( abspath( destpath ) ) or not readable( abspath(destpath) ):
        return None
    # Get the list of items
    dls = os.listdir(destpath)
    # Classify each item
    files = []
    directories = []
    
    for item in dls:
        if isfile( destpath + '/' + item ):
            if request_abspath_shown:
                files.append(abspath(destpath + '/' + item))
            else:
                files.append(item)
            #end if
        elif isdir( destpath + '/' + item ):
            if request_abspath_shown:
                directories.append(abspath(destpath + '/' + item))
            else:
                directories.append(item)
            #end if
        else:
            pass
        #end if
    files.sort()
    directories.sort()
    return {'files':files, 'directories':directories}

# Reading Function
def read(filename = '', mode = READ_NORMAL):
    '''
    Read file *filename* and return the content
    
    Supported modes:
    
    * READ_NORMAL is to read as a text file using 'r' mode
    * READ_BINARY is to read as a binary file using 'rb' mode
    * READ_PICKLE is to read as a pickle file (serialized object) using 'rb' mode
    '''
    if filename == '':
        # read stdin by default
        return sys.stdin.read()
    if mode == READ_PICKLE:
        # use pickle for reading
        if not size(filename) > 0:
            return None
        data = cPickle.load(open(filename, 'rb'))
        return data

    # This part does not use pickle.
    if not isfile(filename):
        return None
    data = open(filename, mode).read()
    return data

# Writing Function
def write(filename, data, mode = WRITE_NORMAL):
    '''
    Write the *data* to file *filename*
    
    Supported modes:
    
    * WRITE_NORMAL is to write as a text file using 'w' mode
    * WRITE_BINARY is to write as a binary file using 'wb' mode
    * WRITE_PICKLE is to write as a pickle file (serialized object) using 'wb' mode
    '''
    if mode == WRITE_PICKLE:
        try:
            fp = open(filename, 'wb')
            cPickle.dump(data, fp)
            fp.close()
            return True
        except:
            return False

    # This part does not use pickle.
    if isfile(filename):
        os.unlink(filename)
    try:
        fp = open(filename, mode)
        fp.write(data)
        fp.close()
    except:
        return False
    return True

# Removal Function
def remove(destpath):
    if isdir(destpath):
        os.removedirs(destpath)
        return True
    elif isfile(destpath):
        os.unlink(destpath)
        return True
    return False