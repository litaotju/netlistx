# -*- coding: utf-8 -*-
u'''netlistx 包的默认全局logger'''

import logging
import os
import time

__all__ = ["logger"]

#可配置LOG的路径
LOGDIR = os.path.join(os.path.split(__file__)[0], "logfiles")
DEFAULT_LOG = "main%s.log" % time.strftime("%Y%m%d")
#默认的全局logger
logger = logging.getLogger('netlistx.mainlog')

#流log
ch = logging.StreamHandler()
chformatter = logging.Formatter('[%(levelname)s]: %(message)s')  #格式
ch.setFormatter(chformatter)
logger.addHandler(ch)

#文件Log
cwd = os.path.split(__file__)[0]
fh = logging.FileHandler(os.path.join(cwd, "logfiles", DEFAULT_LOG))
fhformatter = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s]: %(message)s')  #格式
fh.setFormatter(fhformatter)
logger.addHandler(fh)

#设置Logger的级别
logger.setLevel(logging.DEBUG)
