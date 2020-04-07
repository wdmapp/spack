from spack import *
import os
import sys
import shutil
import subprocess
import socket


class GeneAll(MakefilePackage):

    homepage = "http://genecode.org/"
    url = "http://genecode.org/"

    version('gabriele', git='https://code.ornl.gov/eqs/gene-coupling.git', branch='ecp+xgc')
    version('gitlab', git='https://code.ornl.gov/eqs/gene-coupling.git', branch='effis')

    variant('couple', default="none", description='Spatial coupling', values=["xgc-edge"])
    variant('gptl', default=False, description='Use GPTL timing')
    variant('adios2', default=False, description='ADIOS2 support')
    variant('effis', default=False, description='EFFIS support')


    # "Usual" dependencies
    depends_on('fftw')
    depends_on('scalapack')
    depends_on('mpi')
    depends_on('petsc +complex')
    depends_on('python')

    parallel = True

    depends_on('hdf5 @:1.8.19 +mpi +fortran +hl')
    depends_on('gptl +noomp +nonano', when="+gptl")

    depends_on("adios +fortran")
    depends_on("adios2", when="+adios2")

    depends_on("effis@kittie", when="@gabriele +effis")
    depends_on("effis", when="@gitlab +effis")
    conflicts("effis@kittie", when="@gitlab +effis")


    def setup_environment(self, spack_env, run_env):
        spack_env.set('MACHINE', 'spack-suchyta')
        spack_env.set('FFTW_INC', self.spec['fftw'].prefix.include)


    @when("@gabriele,gitlab")
    def edit(self, spec, prefix):
        pwd = os.getcwd()
        self.makefile = os.path.join(pwd, 'makefiles', 'spack-suchyta', 'spack-suchyta.mk')
        self.builddir = os.path.join(pwd, 'build')
        self.rules = os.path.join(pwd, "makefiles", "rules.mk")
        makedir = os.path.dirname(self.makefile)
        if not os.path.exists(makedir):
            os.makedirs(makedir)
        shutil.copy(os.path.join(pwd, "makefiles", "theta", "theta.mk"), self.makefile)

        if (self.compiler.name == "gcc") or (sys.platform == 'darwin'):
            filter_file('^\s*(COMPILER\s*=\s*.*)$', 'COMPILER = gnu', self.makefile)
            filter_file('^\s*(FFLAGS\s*\+=\s*\$\(SET_FORTRAN_STANDARD\))$', "FFLAGS += -g -ggdb -ffree-line-length-0 -Wno-tabs", self.rules)

        elif self.compiler.name == "intel":
            filter_file('^\s*(COMPILER\s*=\s*.*)$', 'COMPILER = intel', self.makefile)
            intelfile = os.path.join(pwd, 'makefiles', 'compilers', 'intel.def')
            with open(intelfile, "r") as infile:
                text = infile.read()
            index = text.find("FC = ifort")
            with open(intelfile, "w") as outfile:
                outfile.write(text[index:])

        filter_file('^\s*(MPFC\s*=\s*.*)$', 'MPFC = {0}'.format(spec['mpi'].mpifc), self.makefile)
        filter_file('^\s*(MPCC\s*=\s*.*)$', 'MPCC = {0}'.format(spec['mpi'].mpicc), self.makefile)
        filter_file('^\s*(MPCXX\s*=\s*.*)$', 'MPCXX = {0}'.format(spec['mpi'].mpicxx), self.makefile)

        #if machine == "theta":
        #filter_file('^\s*(MB_PER_CORE\s*=\s*.*)$', 'MB_PER_CORE = 2500', self.makefile)

        filter_file('^\s*(SLEPC\s*=\s*.*)$', 'FUTILS = no', self.makefile)
        filter_file('^\s*(FUTILS\s*=\s*.*)$', 'FUTILS = yes', self.makefile)
        filter_file('^\s*(LIBS\s*\+=\s*\-L\$\(FFTW_DIR\))', 'LIBS += ', self.makefile)
        filter_file('^\s*(LIBS\s*\+=\s*\$\(HDF5_LIBPATH\)\s*\$\(HDF5_LIBS\))$', 'LIBS += -L$(FUTILSDIR) $(HDF5_LIBS)', self.makefile)

        #$if machine in ['cori', 'theta']:
        #filter_file('^\s*(HDF5_LIBS\s*=\s*.*)$', 'HDF5_LIBS = -lfutils -l:libhdf5hl_fortran.a -l:libhdf5_hl.a -l:libhdf5_fortran.a -l:libhdf5.a -lz -ldl', self.makefile)
        #filter_file('^\s*(HDF5_LIBS\s*=\s*.*)$', 'HDF5_LIBS = -lfutils -l:{0}/lib/libhdf5hl_fortran.a -l:{0}/lib/libhdf5_hl.a -l:{0}/lib/libhdf5_fortran.a -l{0}:/lib/libhdf5.a -lz'.format(spec['hdf5'].prefix), self.makefile)

        if self.spec.satisfies("couple=xgc-edge"):
            filter_file('^\s*(COUPLE_XGC\s*=.*)$', 'COUPLE_XGC = yes', self.makefile)
        else:
            filter_file('^\s*(COUPLE_XGC\s*=.*)$', 'COUPLE_XGC = no', self.makefile)

        if self.spec.satisfies('^netlib-scalapack'):
            filter_file('^\s*(SCALAPACK\s*=\s*.*)$', 'SCALAPACK = yes\n', self.makefile)
            with open(self.makefile, "a") as outfile:
                #outfile.write("LIBS += -lscalapack\n")
                outfile.write("LIBS += -lscalapack -llapack -lblas\n")

        if spec.satisfies('+gptl'):
            with open(self.makefile, "a") as outfile:
                outfile.write("WITH_GPTL = yes\n")
                outfile.write("LIBS += -lgptl\n")
                
        if sys.platform == 'darwin':
            with open(self.makefile, "a") as outfile:
                outfile.write("WITH_CUTILS = no\n")
        else:
            filter_file('^\s*(HDF5_LIBS\s*=\s*.*)$', 'HDF5_LIBS = -lfutils -l:libhdf5hl_fortran.a -l:libhdf5_hl.a -l:libhdf5_fortran.a -l:libhdf5.a -lz -ldl', self.makefile)

        if spec.satisfies('+adios2'):
            filter_file('^\s*(ADIOS2\s*=.*)$', 'ADIOS2 = yes', self.makefile)
            filter_file('^\s*(ADIOS2_DIR\s*=.*)$', "ADIOS2_DIR = {0}".format(spec['adios2'].prefix), self.makefile)

            if spec.satisfies("+effis"):
                filter_file('^\s*(EFFIS\s*=.*)$', 'EFFIS = yes', self.makefile)
                filter_file('^\s*(ADIOS2_LIB\s*=.*)$', "ADIOS2_LIB = -lkittie_f -ladios2 -ladios2_f", self.rules)
                if spec.satisfies("^adios2@2.4.0:"):
                    filter_file('^\s*(ADIOS2_INC\s*=.*)$', "ADIOS2_INC = -I{1} -I{0} -I{0}/adios2/fortran".format(spec['adios2'].prefix.include, spec['effis'].prefix.include), self.rules)
                else:
                    filter_file('^\s*(ADIOS2_INC\s*=.*)$', "ADIOS2_INC = -I{1} -I{0} -I{0}/fortran".format(spec['adios2'].prefix.include, spec['effis'].prefix.include), self.rules)

            else:
                filter_file('^\s*(ADIOS2_LIB\s*=.*)$', "ADIOS2_LIB = -ladios2 -ladios2_f", self.rules)
                if spec.satisfies("^adios2@2.4.0:"):
                    filter_file('^\s*(ADIOS2_INC\s*=.*)$', "ADIOS2_INC = -I{0} -I{0}/adios2/fortran".format(spec['adios2'].prefix.include), self.rules)
                else:
                    filter_file('^\s*(ADIOS2_INC\s*=.*)$', "ADIOS2_INC = -I{0} -I{0}/fortran".format(spec['adios2'].prefix.include), self.rules)

        else:
            filter_file('^\s*(ADIOS2\s*=.*)$', 'ADIOS2 = no', self.makefile)

        self.MakeGene = os.path.join(pwd, "makefile")
        filter_file('\$\(PWD\)', self.builddir, self.MakeGene)
        filter_file('#main', "", self.MakeGene)


    @when("@gabriele,gitlab")
    def build(self, spec, prefix):
        with working_dir(self.builddir, create=True):
            make("--makefile={0}".format(self.MakeGene))


    @when("@gabriele,gitlab")
    def install(self, spec, prefix):
        """ Copy the binary and ADIOS XML file to the install directory """

        outdir = os.path.join(prefix, 'bin')
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        pwd = os.getcwd()
        binary = os.path.join(pwd, "bin", "gene_spack-suchyta")
        shutil.copy(binary, os.path.join(outdir, os.path.basename(binary)))

        coupling = os.path.join("src", "coupling_core_gene.F90")
        shutil.copy(coupling, os.path.join(outdir, os.path.basename(coupling)))
