from spack import *
import os
import sys
import shutil


class CamtimersPerf(CMakePackage):
    """Camtimers with perfstubs"""

    homepage = "https://github.com/wdmapp/camtimers.git"
    url = homepage

    version('master', git='https://github.com/wdmapp/camtimers.git', branch='master',  preferred=True)
    depends_on('mpi', when="+mpi")
    depends_on('cmake')
