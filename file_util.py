# -*- coding: utf-8 -*- #

import os
def vm_files(dir):
    '''返回特定目录下的全部vm或者v file
    '''
    for eachFile in os.listdir(dir):
        if os.path.splitext(eachFile)[1] in ['.v','.vm']:
            yield eachFile
