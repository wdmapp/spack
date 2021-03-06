from spack import *
import os
import sys
import shutil
import subprocess
import socket


class FusionIo(MakefilePackage):

    homepage = "http://genecode.org/"
    url = "http://genecode.org/"
    parallel = False
    version('master', git='https://github.com/nferraro/fusion-io.git', branch='master')
    variant('doc', default=False, description='Build documentation')
    variant('shared', default=False, description="Shared libraries")

    depends_on('python')
    depends_on('mpi')
    depends_on('lapack')
    depends_on('hdf5 +mpi +fortran')
    depends_on('texlive', when='+doc')


    def setup_environment(self, spack_env, run_env):
        spack_env.set('FIO_ROOT', self.build_directory)
        spack_env.set('FIO_ARCH', 'RHL_x86')
        spack_env.set('FIO_INSTALL_DIR', self.prefix)
        spack_env.set('PYTHON', which('python').path)


    def edit(self, spec, prefix):
        makefile = join_path("install", "make.inc.RHL_x86")
        filter_file('^\s*(CC\s*=\s*.*)$',  'CC = {0}'.format(spec['mpi'].mpicc),   makefile)
        filter_file('^\s*(CXX\s*=\s*.*)$', 'CXX = {0}'.format(spec['mpi'].mpicxx), makefile)
        filter_file('^\s*(F90\s*=\s*.*)$', 'F90 = {0}'.format(spec['mpi'].mpifc),  makefile)
        filter_file('^\s*(INCLUDE\s*=\s*.*)$', '#INCLUDE = ', makefile)
        filter_file('^\s*(LAPACKS\s*=\s*.*)$', 'LAPACK = {0}'.format(spec['lapack'].libs), makefile)
        
        if spec.satisfies('%gcc'):
            filter_file('^\s*(LIBS\s*=\s*.*)$', 'LIBS = -lgfortran', makefile)
        else:
            filter_file('^\s*(LIBS\s*=\s*.*)$', 'LIBS = ', makefile)
            if spec.satisfies('%pgi'):
                filter_file('^\s*(CFLAGS\s*=\s*.*)$', 'CFLAGS = -fpic', makefile)
                filter_file('^\s*(F90FLAGS\s*=\s*.*)$', 'F90FLAGS = -r8 -fpic', makefile)

        if spec.satisfies("-doc"):
            makefile = "makefile"
            filter_file('^\s*(alldirs\s*=\s*.*)$', 'alldirs = $(libs) $(bins) examples', makefile)


    def build(self, spec, prefix):
        if spec.satisfies("+shared"):
            make("shared")
        else:
            make()
