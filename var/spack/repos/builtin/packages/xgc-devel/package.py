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
    version('commit',  git='https://github.com/PrincetonUniversity/XGC-Devel.git', commit='63eb658c87bab810ff70e6e95add85a4ab61a94b', preferred=False)
    version('effis',  git='https://github.com/suchyta1/XGC-Devel.git', branch='effis-more')

    variant('effis', default=False, description='EFFIS support')
    variant('openmp', default=False, description="Build with OpenMP")
    variant('openacc', default=False, description="Build with OpenACC")
    variant('debug', default=False, description="Use debug symbols")

    cuda_values = ["Volta70", "Turing75", "Kepler30"]
    variant('cuda', default="none", values=cuda_values, description="Build Cuda")

    cpu_values = ["SKX", "Power9", "SNB"]
    variant('host_arch', default="none", values=cpu_values, description="CPU optimization")

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
    depends_on('lapack')
    depends_on('blas')
    depends_on('pspline')
    depends_on('camtimers-perf')

    depends_on('googletest', when="+build_testing")
    depends_on('fusion-io -shared', when="+fusion_io")
    depends_on('effis', when="+effis")
    conflicts('effis@kittie')

    kokkos = "kokkos"
    if kokkos == "kokkos-cmake":
        depends_on('{0} +serial +aggressive_vectorization cxxstd=11'.format(kokkos))
    else:
        depends_on('{0} +serial +aggressive_vectorization cxxstd=c++11'.format(kokkos))
    depends_on('cabana +mpi')
    depends_on('{0} +openmp'.format(kokkos), when="+openmp")
    depends_on('cabana +openmp', when="+openmp")

    for value in cuda_values:
        when = "cuda={0}".format(value)
        depends_on('{0} +cuda +enable_lambda gpu_arch={1}'.format(kokkos, value), when=when)
        depends_on('cabana +cuda', when=when)
        depends_on('cuda', when=when)

    for value in cpu_values:
        when = "host_arch={0}".format(value)
        depends_on('{0} {1}'.format(kokkos, when), when=when)

    
    def AddDebugOpt(self, flags, opt):
        if not self.spec.satisfies("+debug"):
            flags = '{0} {1}'.format(flags, opt)
        else:
            flags = '{0} -g'.format(flags)
        return flags


    def Append(self, line):
        self.makestream.write("\n" + line)


    def edit(self, spec, prefix):
        platform = "spack"
        env["XGC_PLATFORM"] = platform

        flagfile = os.path.join("build", "xgc_flags.mk")
        makefile = os.path.join("build", "make.inc.{0}".format(platform))
        rulefile = os.path.join("build", "rules.mk")
        corefile = os.path.join("XGC_core", "cpp", "Makefile")

        #opts = ["-DITER_GRID", "-DCAM_TIMERS", "-DADIOS2", "-DFFTW3"]
        opts = ["-DCAM_TIMERS", "-DADIOS2", "-DFFTW3"]
        for option in self.xgc_options:
            if spec.satisfies("+{0}".format(option)):
                opts  += ["-D{0}".format(option.upper())]
        filter_file('^\s*(XGC_FLAGS\s*\+=.*)', 'XGC_FLAGS += {0}'.format(' '.join(opts)), flagfile)
        filter_file('\$\(CABANA_INC\)\s*\$\(PREFIX\)', '$(CABANA_INC) -I$(PREFIX)', corefile)

            
        effis_inc = ""
        effis_lib = ""
        if spec.satisfies("+effis"):
            effis_inc = "-I{0}".format(spec['effis'].prefix.include)
            effis_lib = "-lkittie_f"
            
        if not spec.satisfies("cuda=none"):
            #env['CUDAROOT'] = spec['cuda'].prefix
            if self.spec.satisfies('%gcc'):
                env['NVCC_WRAPPER_DEFAULT_COMPILER'] = self.compiler.cxx
            elif self.spec.satisfies('%pgi'):
                env['NVCC_WRAPPER_DEFAULT_COMPILER'] = spec['mpi'].mpicxx
            #cxx = which("nvcc_wrapper").path
            cxx = join_path(self.spec[self.kokkos].prefix, '../', 'bin', 'nvcc_wrapper')
        else:
            cxx = spec['mpi'].mpicxx


        if spec.satisfies("%gcc") or spec.satisfies("%clang"):
            mod = "-J"
            openmp = "-fopenmp"
            other = '-fPIC -ffree-line-length-0'
            opt = '-03'
        elif spec.satisfies("%pgi"):
            mod = "-module"
            openmp = "-mp"
            other = ' -D__PGI -fpic'
            opt = '-fast'
        flags = other
        flags = self.AddDebugOpt(flags, opt)
        if spec.satisfies("+openmp"):
            flags = '{0} {1}'.format(flags, openmp)


        self.makestream = open(makefile, "w")
        if spec.satisfies("+effis"):
            self.Append("effis = yes")

        self.Append('FFLAGS = {0}'.format(flags))
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
            #self.Append("FUSION_IO_LIB = -lfusionio -lm3dc1 -lm3dc1_fortran -lstdc++")
            self.Append("FUSION_IO_LIB = -lfusionio -lm3dc1 -lm3dc1_fortran")

        self.Append("CABANA_INC = -I{0}/ -I{1}/".format(spec['cabana'].prefix.include, spec[self.kokkos].prefix.include))
        if spec.satisfies("^{0}@:2.9.99".format(self.kokkos)):
            cab = "-lkokkos"
        else:
            cab = "-lkokkoscore"
        if not spec.satisfies("cuda=none"):
            cab = "-L{0}/lib64 {1}".format(spec['cuda'].prefix, cab)
            cab = "{0} -lcuda -lcudart".format(cab)
        if spec.satisfies("%pgi"):
            cab = "{0} -pgc++libs".format(cab)
        self.Append("CABANA_LIB = {0}".format(cab))
        #self.Append("CABANA_LIB = {0} -lstdc++".format(cab))
        #self.Append("CABANA_LIB = {0} -lhwloc".format(cab))


        cxx_flags = ""
        acc = ""
        cab = ""

        if spec.satisfies("+openmp"):
            cxx_flags = "{0} {1}".format(cxx_flags, openmp)
            filter_file('-DUSE_CAB_OMP=0', '-DUSE_CAB_OMP=1', rulefile)
        elif spec.satisfies("cuda=none"):
            filter_file('-DUSE_CAB_OMP=1', '-DUSE_CAB_OMP=0', rulefile)
            filter_file('-DUSE_ARRAY_REPLICATION', '-UUSE_ARRAY_REPLICATION', rulefile)
        if not spec.satisfies("cuda=none"):
            cxx_flags = "{0} --expt-extended-lambda -arch=sm_{1}".format(cxx_flags, spec.variants['cuda'].value[-2:])
            if spec.satisfies("%pgi"):
                acc = "{0} -Minfo=accel -Mnostack_arrays -Mcuda=cuda10.1,cc{1}".format(acc, spec.variants['cuda'].value[-2:])
                cab = "{0} -Minfo=accel -Mnostack_arrays -Mcuda=cuda10.1,cc{1}".format(cab, spec.variants['cuda'].value[-2:])
                cxx_flags = "{0} -Minfo=accel -Mnostack_arrays".format(cab, spec.variants['cuda'].value[-2:])
        cxx_flags = self.AddDebugOpt(cxx_flags, opt)
            
        if spec.satisfies("+openacc"):
            if spec.satisfies("%gcc"):
                #acc = "{0} -fopenacc -DUSE_ASYNC".format(acc)
                cab = "{0} -fopenacc".format(cab)
                #cxx_flags = "{0} -fopenacc".format(cxxflags)
            elif spec.satisfies("%pgi"):
                #acc = "{0} -acc".format(acc)
                cab = "{0} -acc".format(cab)
                #cxx_flags = "{0} -acc".format(cxx_flags)
                if not spec.satisfies("cuda=none"):
                    #acc = "{0} -ta=nvidia:cc{1},ptxinfo,maxrregcount:128".format(acc, spec.variants['cuda'].value[-2:])
                    cab = "{0} -ta=nvidia:cc{1}".format(cab, spec.variants['cuda'].value[-2:])
                    #cxx_flags = "{0} -ta=nvidia:cc{1}".format(cxx_flags, spec.variants['cuda'].value[-2:])

        self.Append("CAB_CXX_FLAGS = -pedantic -std=c++11 {0}".format(cxx_flags))
        self.Append("CAB_FTN_FLAGS = {0}".format(cab))
        self.Append("ACC_FFLAGS = {0}".format(acc))
        self.Append("CAB_LINK_FLAGS = {1} {0}".format(acc, cab))


        self.Append('FC = {0}'.format(spec['mpi'].mpifc))
        self.Append('CC = {0}'.format(spec['mpi'].mpicc))
        self.Append('LD = {0}'.format(spec['mpi'].mpifc))
        self.Append('CXX = {0}'.format(cxx))
        if spec.satisfies('%gcc'):
            self.Append('LD_CAB = {0}'.format(spec['mpi'].mpicxx))
        elif spec.satisfies('%pgi'):
            self.Append('LD_CAB = {0}'.format(spec['mpi'].mpifc))

        self.makestream.close()


    def build(self, spec, prefix):
        if not spec.satisfies("cuda=none"):
            self.binary = 'xgc-es-cpp-gpu'
        else:
            self.binary = 'xgc-es-cpp'
        make(self.binary, parallel=False)


    def install(self, spec, prefix):
        mkdirp(self.prefix.bin)
        install(os.path.join(self.stage.source_path, "xgc_build", self.binary), self.prefix.bin)

