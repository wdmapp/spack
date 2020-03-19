# GENE spack package file

from spack import *
import os


def InstallCopy(filename, outdir):
    install(filename, os.path.join(outdir, filename))


class Camtimers(MakefilePackage):
    """ Timing library based on GPTL, using in XGCe """

    homepage = "https://bitbucket.org/madams/epsi/overview"
    url = "https://bitbucket.org/madams/epsi/overview"
    version('wdmapp', git='https://github.com/wdmapp/camtimers.git', branch='master')

    variant('openmp', default=True, description='Use openmp')
    depends_on('mpi')
    """
    variant('papi', default=True, description='Require PAPI')
    depends_on('papi', when="+papi")
    """

    def setup_environment(self, spack_env, run_env):
        self.machine = 'spack'


    def edit(self, spec, prefix):
        pwd = os.getcwd()

        # Copy camtimers makefile
        if spec.satisfies("@xgc"):
            self.camdir = os.path.join(pwd, 'libs', 'camtimers')
        elif spec.satisfies("@wdmapp"):
            self.camdir = pwd

        self.camfile = os.path.join(self.camdir, 'MAKEFILES', "Makefile.osx".format(self.machine))
        if spec.satisfies("+openmp"):
            if spec.satisfies("%gcc"):
                filter_file('^\s*(FC\s*:=\s*.*)$', 'FC = {0} -fopenmp'.format(spec['mpi'].mpifc), self.camfile)
                filter_file('^\s*(CC\s*:=\s*.*)$', 'CC = {0} -fopenmp'.format(spec['mpi'].mpicc), self.camfile)
            elif spec.satisfies("%pgi"):
                filter_file('^\s*(FC\s*:=\s*.*)$', 'FC = {0} -mp'.format(spec['mpi'].mpifc), self.camfile)
                filter_file('^\s*(CC\s*:=\s*.*)$', 'CC = {0} -mp'.format(spec['mpi'].mpicc), self.camfile)
        else:
            filter_file('^\s*(FC\s*:=\s*.*)$', 'FC = {0}'.format(spec['mpi'].mpifc), self.camfile)
            filter_file('^\s*(CC\s*:=\s*.*)$', 'CC = {0}'.format(spec['mpi'].mpicc), self.camfile)

        filter_file('^\s*(FREEFLAGS\s*:=\s*.*)$', '#FREEFLAGS += ', self.camfile)
        filter_file('^\s*(FIXEDFLAGS\s*:=\s*.*)$', '#FIXEDFLAGS += ', self.camfile)

        """
        filter_file('^\s*(CPPDEF\s*\+=\s*.*)$', '#CPPDEF += ', self.camfile)
        if not spec.satisfies("+papi"):
            filter_file("-DHAVE_PAPI", "-UHAVE_PAPI", self.camfile)
        """


    def build(self, spec, prefix):
        with working_dir(self.camdir):
            make("--makefile={0}".format(self.camfile), parallel=False)


    def install(self, spec, prefix):
        mkdirp(prefix.lib)
        mkdirp(prefix.include)
        with working_dir(self.camdir):
            InstallCopy("private.h", prefix.include)
            InstallCopy("gptl.h", prefix.include)
            InstallCopy("gptl.inc", prefix.include)
            InstallCopy("perf_mod.mod", prefix.include)
            InstallCopy("libtimers.a", prefix.lib)

