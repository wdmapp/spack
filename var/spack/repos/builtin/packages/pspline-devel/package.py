# GENE spack package file

from spack import *
import os
import sys


class PsplineDevel(MakefilePackage):
    """ (Fortran) Spline interpolation package """

    homepage = "http://w3.pppl.gov/ntcc/PSPLINE/"

    version('wdmapp', git="https://github.com/wdmapp/pspline.git", branch="master")

    parallel = False
    #depends_on('netcdf-fortran')
    depends_on('mpi')               # I'm not positive this needs MPI
    #depends_on('python')


    def setup_dependent_environment(self, spack_env, run_env, dependent_spec):
        spack_env.set('PSPLINE_DIR', self.prefix)


    def build(self, spec, prefix):
        filter_file('include ALL_ARCH.mk', '#include ALL_ARCH.mk', "Makefile")
        make("FC={0}".format(spec['mpi'].mpifc), parallel=False)

        """
        with working_dir(os.path.join(os.getcwd(), 'backup')):
            #filter_file('^-include', '#-include', "Makefile")
            #filter_file('^include', '#include', "Makefile")
            make("FC={0}".format(spec['mpi'].mpifc), "FC90={0}".format(spec['mpi'].mpifc), parallel=False)
        """


    def install(self, spec, prefix):
        mkdirp(self.prefix.lib)
        install("libpspline.a", self.prefix.lib)

        mkdirp(self.prefix.include)
        mkdirp(self.prefix.mod)
        files = os.listdir("./")
        for filename in files:
            if filename.endswith(".mod"):
                install(filename, self.prefix.mod)

        """
        with working_dir(os.path.join(os.getcwd(), 'backup')):
            make("FC={0}".format(spec['mpi'].mpifc), "FC90={0}".format(spec['mpi'].mpifc), "install", parallel=False)
        """
