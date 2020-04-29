from spack import *
import os
import sys
import shutil
import subprocess
import socket


class XgcDevel(MakefilePackage):
    """ XGC tokamak simulation code """
    homepage = "https://bitbucket.org/madams/epsi/overview"
    url = "https://bitbucket.org/madams/epsi/overview"

    version('master',  git='https://github.com/PrincetonUniversity/XGC-Devel.git', branch='master', preferred=True)
    version('effis',  git='https://github.com/suchyta1/XGC-Devel.git', branch='effis-more')

    variant('effis', default=False, description='EFFIS support')
    variant('openmp', default=False, description="Build with OpenMP")
    variant('openacc', default=False, description="Build with OpenACC")
    variant('cuda', default=False, description="Build Cuda")
    variant('cpu_arch', default="none", description="CPU architecture")
    variant('gpu_arch', default="none", description="GPU architecture")

    xgc_options = ["convert_grid2", "deltaf_mode2", "init_gene_pert", 'col_f_positivity_opt', 'build_testing', 'neoclassical_test', "fusion_io"]
    for option in xgc_options:
        variant(option, default=False, description='-D{0}'.format(option.upper()))

    depends_on('mpi')
    depends_on('fftw')
    depends_on('parmetis')
    depends_on('metis +real64')
    depends_on('hdf5 +mpi +fortran +hl')
    depends_on('adios2@2.5.0: -python')
    depends_on("adios +fortran")
    depends_on('petsc -complex -superlu-dist @3.7.0:3.7.99')
    #depends_on('petsc -complex -superlu-dist @3.8.0:3.8.99')
    depends_on('lapack')
    depends_on('blas')
    depends_on('pspline')
    depends_on('camtimers-perf')

    depends_on('googletest', when="+build_testing")
    depends_on('fusion-io -shared', when="+fusion_io")
    depends_on('effis', when="+effis")
    conflicts('effis@kittie')

    depends_on('kokkos@develop +serial +aggressive_vectorization cxxstd=c++11')
    depends_on('kokkos@develop +openmp', when="+openmp")
    depends_on('kokkos@develop +cuda +enable_lambda gpu_arch=Volta70', when="+cuda")
    depends_on('kokkos@develop gpu_arch=Volta70', when="+cuda gpu_arch=70")

    depends_on('cabana-devel@develop +serial +mpi')
    depends_on('cabana-devel@develop +openmp', when="+openmp")
    depends_on('cabana-devel@develop +cuda', when="+cuda")


    def Append(self, line):
        self.makestream.write("\n" + line)


    def setup_environment(self, spack_env, run_env):
        self.platform = "spack"
        spack_env.set("XGC_PLATFORM", self.platform)


    def edit(self, spec, prefix):
        flagfile = os.path.join("build", "xgc_flags.mk")
        makefile = os.path.join("build", "make.inc.{0}".format(self.platform))

        opts = ["-DITER_GRID", "-DCAM_TIMERS", "-DADIOS2", "-DFFTW3"]
        for option in self.xgc_options:
            if spec.satisfies("+{0}".format(option)):
                opts  += ["-D{0}".format(option.upper())]
        filter_file('^\s*(XGC_FLAGS\s*\+=.*)', 'XGC_FLAGS += {0}'.format(' '.join(opts)), flagfile)

            
        effis_inc = ""
        effis_lib = ""
        if spec.satisfies("+effis"):
            effis_inc = "-I{0}".format(spec['effis'].prefix.include)
            effis_lib = "-lkittie_f"
            
        if spec.satisfies("+cuda"):
            cxx = which("nvcc_wrapper").path
        else:
            cxx = spec['mpi'].mpicxx


        if spec.satisfies("%gcc"):
            mod = "-J"
            openmp = "-fopenmp"
            #other = '-O3 -fPIC -ffree-line-length-0'
            other = '-fPIC -ffree-line-length-0'
        elif spec.satisfies("%pgi"):
            mod = "-module"
            openmp = "-mp"
            other = '-fast -D__PGI -fpic'
        flags = other
        if spec.satisfies("+openmp"):
            flags = '{0} {1}'.format(flags, openmp)


        self.makestream = open(makefile, "w")
        self.Append("effis = yes")
        self.Append('FC = {0}'.format(spec['mpi'].mpifc))
        self.Append('CC = {0}'.format(spec['mpi'].mpicc))
        self.Append('LD = {0}'.format(spec['mpi'].mpifc))
        self.Append('LD_CAB = {0}'.format(spec['mpi'].mpicxx))
        self.Append('CXX = {0}'.format(cxx))
        self.Append('NVCC_WRAPPER_DEFAULT_COMPILER = {0}'.format(spec['mpi'].mpicxx))
        self.Append('FFLAGS = -g {0}'.format(flags))
        self.Append('MOD_DIR_OPT = {0}'.format(mod))

        self.Append('ADIOS_INC = {2} -I{0} -I{0}/adios2/fortran -I{1}'.format(spec['adios2'].prefix.include, spec['adios'].prefix.include, effis_inc))
        self.Append('ADIOS_LIB = {1} $(shell adios_config -f -l)  -L{0} -ladios2 -ladios2_f'.format(spec['adios2'].prefix.lib, effis_lib))
        self.Append('include {0}/lib/petsc/conf/variables'.format(spec['petsc'].prefix))
        self.Append('PETSC_DIR = {0}'.format(spec['petsc'].prefix))
        self.Append('PETSC_LIB = ${PETSC_KSP_LIB}')
        self.Append('CAMTIMERS_INC = -I{0}'.format(spec['camtimers-perf'].prefix.include))
        self.Append('CAMTIMERS_LIB = -ltimers -ldl')
        self.Append('FFTW_INC = -I{0}'.format(spec['fftw'].prefix.include))
        self.Append('FFTW_LIB = -lfftw3')
        self.Append('HDF5_INC = -I{0}'.format(spec['hdf5'].prefix.include))
        self.Append('HDF5_LIB = -lhdf5_fortran -lhdf5')
        self.Append('PSPLINE_INC = -I{0}/mod'.format(spec["pspline"].prefix))
        self.Append('PSPLINE_LIB = -lpspline')
        self.Append('LAPACK_INC = -I{0} -I{1}'.format(spec['lapack'].prefix.include, spec['blas'].prefix.include))
        self.Append('LAPACK_LIB = {0} {1}'.format(spec['lapack'].libs, spec['blas'].libs))
        
        if spec.satisfies("+fusion_io"):
            self.Append("FUSION_IO_INC = -I{0}".format(spec['fusion-io'].prefix.include))
            self.Append("FUSION_IO_LIB = -lfusionio -lm3dc1 -lm3dc1_fortran -lstdc++")

        self.Append("CABANA_INC = -I{0} -I{1}".format(spec['cabana-devel'].prefix.include, spec['kokkos'].prefix.include))
        self.Append("CABANA_LIB = -lkokkoscore -lhwloc")

        extra = ""
        if spec.satisfies("+openmp"):
            extra = "{0} {1}".format(extra, openmp)
        if not spec.satisfies("cpu_arch=none"):
            extra = "{0} -arch={1}".format(extra, spec.varints['cpu_arch'])
        if spec.satisfies("+cuda"):
            extra = "{0} --expt-extended-lambda".format(extra)
            self.Append("CUDA_REG_COUNT = 128")
            self.Append("NVCC_GCC_PATH = g++")
            self.Append("GPU_ARCH = {0}".format(spec.variants['gpu_arch']))
            
        #self.Append("CAB_CXX_FLAGS = -pedantic -O3 -std=c++11 {0}".format(extra))
        self.Append("CAB_CXX_FLAGS = -pedantic -g -std=c++11 {0}".format(extra))
        self.Append("CAB_FTN_FLAGS = ")
        
        if spec.satisfies("+openacc"):
            self.Append("ACC_FFLAGS = ")
            self.Append("CAB_LINK_FLAGS = ")

        self.makestream.close()


    def build(self, spec, prefix):
        if spec.satisfies("+cuda"):
            self.binary = 'xgc-es-cpp-gpu'
        else:
            self.binary = 'xgc-es-cpp'
        make(self.binary, parallel=False)


    def install(self, spec, prefix):
        mkdirp(self.prefix.bin)
        install(os.path.join(self.stage.source_path, "xgc_build", self.binary), self.prefix.bin)

