from spack import *
import os
import sys
import shutil


class Kittie(CMakePackage):
    """Code Coupling framework"""

    homepage = "https://github.com/suchyta1/kittie"
    url = homepage
    #version('develop', git='https://github.com/suchyta1/kittie.git', branch='monitor', preferred=True)
    version('develop', git='https://github.com/suchyta1/kittie.git', branch='develop', preferred=True)
    version('master',  git='https://github.com/suchyta1/kittie.git', branch='master',  preferred=False)

    variant("mpi", default=True, description="Use MPI")
    variant("fine-time", default=False, description="Finer timing")
    variant("python-prefix", default=True, description="Build into own prefix")
    variant("shared", default=True, description="Build shared library")
    variant("touch", default=False, description="Use explicit touch")

    depends_on('mpi', when="+mpi")
    depends_on('cmake')
    depends_on('adios2')

    depends_on('yaml-cpp')
    depends_on('py-pyyaml')
    depends_on('py-numpy')
    depends_on('py-mpi4py', when="+mpi")
    
    extends('python')
    depends_on('python@2.7:', type=('build', 'run'))
    #depends_on('savanna@develop', when="^python@3:")
    depends_on('codar-cheetah@develop', when="^python@3:")

    def cmake_args(self):
        args = []

        if self.spec.satisfies('+python-prefix'):
            args.append("-DPYTHON_PREFIX=ON")
        else:
            args.append("-DPYTHON_PREFIX=OFF")

        if self.spec.satisfies('+fine-time'):
            args.append("-DFINE_TIME=ON")

        if not self.spec.satisfies('+mpi'):
            args.append("-DUSE_MPI=OFF")
        else:
            args.append("-DCMAKE_CXX_COMPILER={0}".format(self.spec['mpi'].mpicxx))
            args.append("-DCMAKE_C_COMPILER={0}".format(self.spec['mpi'].mpicc))
            args.append("-DCMAKE_Fortran_COMPILER={0}".format(self.spec['mpi'].mpifc))

        if self.spec.satisfies("+shared"):
            args.append("-DBUILD_SHARED_LIBS:BOOL=ON")

        if self.spec.satisfies("+touch"):
            filter_file("touch = False", "touch = True", os.path.join(os.path.join('src', 'Python', 'kittie', 'kittie.py')))
            filter_file("touch = \.false\.", "touch = .true.", os.path.join(os.path.join('src', 'Fortran', 'kittie_internal.F90')))
        if self.spec.satisfies("^adios2@:2.3.99"):
            filter_file("OldStep = False", "OldStep = True", os.path.join(os.path.join('src', 'Python', 'kittie', 'kittie.py')))

        return args


    def install(self, spec, prefix):
        with working_dir(self.build_directory):
            make('install')
            """
            reader = os.path.join("examples", "simple", "Cpp", "reader-kittie.cpp")
            shutil.copy(reader, prefix.examples.simple.Cpp)
            reader = os.path.join("examples", "simple", "Fortran", "reader-kittie.F90")
            shutil.copy(reader, prefix.examples.simple.Fortran)
            """

