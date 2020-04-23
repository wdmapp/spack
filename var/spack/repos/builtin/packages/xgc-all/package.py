from spack import *
import os
import sys
import shutil
import subprocess
import socket


class XgcAll(CMakePackage):
    """ XGC tokamak simulation code """
    homepage = "https://bitbucket.org/madams/epsi/overview"
    url = "https://bitbucket.org/madams/epsi/overview"

    #version('master',  git='https://github.com/PrincetonUniversity/XGC-Devel.git', branch='master')
    version('master',  git='https://github.com/suchyta1/XGC-Devel.git', branch='effis')
    version('suchyta', git='https://github.com/suchyta1/XGC-Devel.git', branch='effis-core-edge')
    version('gabriele', git='https://code.ornl.gov/eqs/xgc-coupling.git', branch='master')
    version('gitlab', git='https://code.ornl.gov/eqs/xgc-coupling.git', branch='effis')


    variant('couple', default="none", description='Spatial coupling', values=["gene", "xgc-core", "xgc-edge", "none"])
    variant('effis', default=False, description='EFFIS support')
    variant('openmp', default=True, description="Build with OpenMP")
    variant('gpu', default=False, description="Build GPU")
    variant('fusion_io', default=False, description="Use fusion-io")

    xgc_options = ["convert_grid2", "deltaf_mode2", "init_gene_pert", 'col_f_positivity_opt', 'build_testing', 'neoclassical_test']
    for option in xgc_options:
        variant(option, default=False, description='-D{0}'.format(option.upper()))


    depends_on('mpi')
    depends_on('fftw')
    depends_on('parmetis')
    depends_on('metis +real64')
    depends_on('hdf5 +mpi +fortran +hl')

    depends_on('googletest', when="+build_testing")
    depends_on('fusion-io', when="+fusion_io")

    depends_on('adios2 -python')
    depends_on("adios +fortran")
    depends_on('effis@kittie', when="@suchyta,gabriele +effis")
    depends_on('effis', when="@gitlab,master +effis")
    conflicts('effis@kittie', when="@gitlab,master")

    depends_on('petsc -complex -superlu-dist @3.7.0:3.7.99',  when="@gabriele,gitlab,suchyta,master")
    #depends_on('petsc -complex -superlu-dist', when="@master")
    depends_on('pspline', when="@gabriele,gitlab,suchyta")
    depends_on('camtimers +openmp', when="@gabriele,gitlab,suchyta +openmp")
    depends_on('camtimers -openmp', when="@gabriele,gitlab,suchyta -openmp")

    #depends_on('cuda', when='+gpu')
    #depends_on('cuda', when="@master +gpu")

    depends_on('kokkos-cmake@develop +serial', when="@master")
    depends_on('kokkos-cmake@develop +openmp', when="@master +openmp")
    depends_on('kokkos-cmake@develop +serial +openmp +cuda +enable_lambda gpu_arch=Volta70', when="@master +gpu")

    depends_on('cabana@develop +serial', when="@master")
    depends_on('cabana@develop +openmp', when="@master +openmp")
    depends_on('cabana@develop +cuda', when="@master +gpu")

    conflicts("@gabriele", when="+gpu")
    conflicts("@gitlab", when="+gpu")

    parallel = False


    def edit(self, spec, prefix):
        self.flagfile = os.path.join("build", "xgc_flags.mk")
        filter_file('^\s*(FC\s*=\s*.*)$',  'FC = {0}'.format(spec['mpi'].mpifc), self.makefile)
        filter_file('^\s*(FC\s*:=\s*.*)$', 'FC = {0}'.format(spec['mpi'].mpifc), self.makefile)
        filter_file('^\s*(CC\s*=\s*.*)$', 'CC = {0}'.format(spec['mpi'].mpicc), self.makefile)
        filter_file('^\s*(LD\s*=\s*.*)$', 'LD = {0}'.format(spec['mpi'].mpifc), self.makefile)

        filter_file('^\s*(ADIOS2_DIR\s*\?=.*)$', 'ADIOS2_DIR = ', self.makefile)
        filter_file('^\s*(ADIOS2_INC\s*=.*)$',   'ADIOS2_INC = ', self.makefile)
        filter_file('^\s*(ADIOS2_LIB\s*=.*)$',   'ADIOS2_LIB = ', self.makefile)

        if spec.satisfies("+effis"):
            filter_file('^\s*(ADIOS_INC\s*=.*)$', 'ADIOS_INC = -I{2} -I{0} -I{0}/adios2/fortran -I{1}'.format(spec['adios2'].prefix.include, spec['adios'].prefix.include, spec['effis'].prefix.include), self.makefile)
            filter_file('^\s*(ADIOS_LIB\s*=.*)$', 'ADIOS_LIB = $(shell adios_config -f -l) -L{1} -lkittie_f -L{0} -ladios2 -ladios2_f'.format(spec['adios2'].prefix.lib, spec['effis'].prefix.lib), self.makefile)
        elif spec.satisfies("^adios2@2.4.0:"):
            filter_file('^\s*(ADIOS_INC\s*=.*)$', 'ADIOS_INC = -I{0} -I{0}/adios2/fortran -I{1}'.format(spec['adios2'].prefix.include, spec['adios'].prefix.include), self.makefile)
            filter_file('^\s*(ADIOS_LIB\s*=.*)$', 'ADIOS_LIB = $(shell adios_config -f -l)  -L{0} -ladios2 -ladios2_f'.format(spec['adios2'].prefix.lib), self.makefile)
        else:
            filter_file('^\s*(ADIOS_INC\s*=.*)$', 'ADIOS_INC = -I{0} -I{0}/fortran -I{1}'.format(spec['adios2'].prefix.include, spec['adios'].prefix.include), self.makefile)
            filter_file('^\s*(ADIOS_LIB\s*=.*)$', 'ADIOS_LIB = $(shell adios_config -f -l)  -L{0} -ladios2 -ladios2_f'.format(spec['adios2'].prefix.lib), self.makefile)

        filter_file('^\s*(PETSC_DIR\s*=.*)$',   'PETSC_DIR = {0}'.format(spec['petsc'].prefix), self.makefile)
        filter_file('^\s*(PETSC_DIR\s*\?=.*)$', 'PETSC_DIR = {0}'.format(spec['petsc'].prefix), self.makefile)
        filter_file('^\s*(PETSC_LIB\s*=.*)$', 'LIB = ${PETSC_KSP_LIB}', self.makefile)

        filter_file('^\s*(CAMTIMERS_INC\s*=.*)$', 'CAMTIMERS_INC = -I{0}'.format(spec['camtimers'].prefix.include), self.makefile)
        filter_file('^\s*(CAMTIMERS_LIB\s*=.*)$', 'CAMTIMERS_LIB = -L{0} -ltimers'.format(spec['camtimers'].prefix.lib), self.makefile)

        filter_file('^\s*(FFTW_INC\s*=.*)$', 'FFTW_INC = -I{0}'.format(spec['fftw'].prefix.include), self.makefile)
        filter_file('^\s*(FFTW_LIB\s*=.*)$', 'FFTW_LIB = -L{0} -lfftw3'.format(spec['fftw'].prefix.lib), self.makefile)

        filter_file('^\s*(HDF5_INC\s*=.*)$', 'HDF5_INC = -I{0}'.format(spec['hdf5'].prefix.include), self.makefile)
        filter_file('^\s*(HDF5_LIB\s*=.*)$', 'HDF5_LIB = -L{0} -lhdf5_fortran -lhdf5'.format(spec['hdf5'].prefix.lib), self.makefile)

        filter_file('^\s*(PSPLINE_INC\s*=.*)$', 'PSPLINE_INC = -I{0}'.format(spec["pspline"].prefix.include), self.makefile)
        filter_file('^\s*(PSPLINE_LIB\s*=.*)$', 'PSPLINE_LIB = -L{0} -lpspline'.format(spec["pspline"].prefix.lib), self.makefile)

        if not spec.satisfies('^cray-libsci'):
            filter_file('^\s*(LAPACK_INC\s*=.*)$', 'LAPACK_INC = -I{0}'.format(spec['lapack'].prefix.include), self.makefile)
            filter_file('^\s*(LAPACK_LIB\s*=.*)$', 'LAPACK_LIB = -L{0} -llapack -lblas'.format(spec['lapack'].prefix.lib), self.makefile)

        if spec.satisfies('couple=gene'):
            filter_file('^\s*(spatial_couple\s*=.*)', "spatial_couple = yes", self.makefile)
            filter_file('^\s*(with_gene\s*=.*)', "with_gene = yes", self.makefile)
            filter_file('^\s*(side\s*=.*)', "side = edge", self.makefile)
        elif spec.satisfies('couple=xgc-core'):
            filter_file('^\s*(spatial_couple\s*=.*)', "spatial_couple = yes", self.makefile)
            filter_file('^\s*(with_gene\s*=.*)', "with_gene = no", self.makefile)
            filter_file('^\s*(side\s*=.*)', "side = edge", self.makefile)
        elif spec.satisfies('couple=xgc-edge'):
            filter_file('^\s*(spatial_couple\s*=.*)', "spatial_couple = yes", self.makefile)
            filter_file('^\s*(with_gene\s*=.*)', "with_gene = no", self.makefile)
            filter_file('^\s*(side\s*=.*)', "side = core", self.makefile)
        elif spec.satisfies('couple=none'):
            filter_file('^\s*(spatial_couple\s*=.*)', "spatial_couple = no", self.makefile)
            filter_file('^\s*(with_gene\s*=.*)', "with_gene = no", self.makefile)
            filter_file('^\s*(side\s*=.*)', "side = edge", self.makefile)

        filter_file('^\s*(adios2\s*=.*)', "adios2 = yes", self.makefile)
        if spec.satisfies('+effis'):
            filter_file('^\s*(effis\s*=.*)', "effis = yes", self.makefile)


    @when("@suchyta +openmp %gcc")
    def compiler_based(self):
        filter_file('^\s*(MOD_DIR_OPT\s*=.*)$', 'MOD_DIR_OPT = -J', self.makefile)
        filter_file('^\s*(FFLAGS\s*=.*)$', 'FFLAGS = -O3 -fPIC -ffree-line-length-0 -fopenmp', self.makefile)

    @when("@suchyta +openmp %pgi")
    def compiler_based(self):
        filter_file('^\s*(MOD_DIR_OPT\s*=.*)$', 'MOD_DIR_OPT = -module', self.makefile)
        filter_file('^\s*(FFLAGS\s*=.*)$', 'FFLAGS = -fast -D__PGI -fpic -mp', self.makefile)

    @when("@suchyta -openmp %gcc")
    def compiler_based(self):
        filter_file('^\s*(MOD_DIR_OPT\s*=.*)$', 'MOD_DIR_OPT = -J', self.makefile)
        filter_file('^\s*(FFLAGS\s*=.*)$', 'FFLAGS = -O3 -fPIC -ffree-line-length-0', self.makefile)

    @when("@suchyta -openmp %pgi")
    def compiler_based(self):
        filter_file('^\s*(MOD_DIR_OPT\s*=.*)$', 'MOD_DIR_OPT = -module', self.makefile)
        filter_file('^\s*(FFLAGS\s*=.*)$', 'FFLAGS = -fast -D__PGI -fpic', self.makefile)


    @when("@suchyta +gpu")
    def setup_environment(self, spack_env, run_env):
        if self.spec.satisfies("%gcc"):
            raise ValueError("GPU compilation requires PGI")
        spack_env.set("XGC_PLATFORM", "summit.coupling")
        self.makefile = os.path.join("build", "make.inc.summit.coupling")

    @when("@suchyta +gpu")
    def cmake(self, spec, prefix):
        self.edit(spec, prefix)
        self.compiler_based()
        filter_file('^\s*(CXX\s*=\s*.*)$', 'CXX = {0}'.format(spec['mpi'].mpicxx), self.makefile)
        filter_file('^\s*(PSPLINE_INC\s*=.*)$', 'PSPLINE_INC = -I{0}/mod'.format(spec["pspline"].prefix), self.makefile)
        filter_file('^\s*(XGC_FLAGS\s*\+=\s*-DITER_GRID)', 'XGC_FLAGS += -DDELTAF_MODE2 -DITER_GRID', self.flagfile)
        #filter_file('-acc', '-fopenacc', self.makefile)

    @when("@suchyta +gpu")
    def build(self, spec, prefix):
        make('xgc1-es-gpu', parallel=False)

    @when("@suchyta +gpu")
    def install(self, spec, prefix):
        binary = "xgc-es-gpu"
        mkdirp(self.prefix.bin)
        install(os.path.join(self.stage.source_path, "xgc_build", binary), self.prefix.bin)
        install(self.makefile, os.path.join(self.prefix.bin))


    @when("@suchyta -gpu")
    def setup_environment(self, spack_env, run_env):
        spack_env.set("XGC_PLATFORM", "generic")
        self.makefile = os.path.join("build", "make.inc.generic")

    @when("@suchyta -gpu")
    def cmake(self, spec, prefix):
        self.edit(spec, prefix)
        self.compiler_based()
        filter_file('^\s*(CXX\s*=\s*.*)$', 'CXX = {0}'.format(spec['mpi'].mpicxx), self.makefile)
        filter_file('^\s*(PSPLINE_INC\s*=.*)$', 'PSPLINE_INC = -I{0}/mod'.format(spec["pspline"].prefix), self.makefile)
        filter_file('^\s*(XGC_FLAGS\s*\+=\s*-DITER_GRID)', 'XGC_FLAGS += -DDELTAF_MODE2 -DITER_GRID', self.flagfile)

    @when("@suchyta -gpu")
    def build(self, spec, prefix):
        make('xgc1-es', parallel=False)

    @when("@suchyta -gpu")
    def install(self, spec, prefix):
        binary = "xgc-es"
        mkdirp(self.prefix.bin)
        install(os.path.join("xgc_build", binary), self.prefix.bin)
        install(self.makefile, os.path.join(self.prefix.bin))


    '''
    @when("@master +openmp %gcc")
    def compiler_based(self):
        filter_file('^\s*(MOD_DIR_OPT\s*=.*)$', 'MOD_DIR_OPT = -J', self.makefile)
        filter_file('^\s*(FFLAGS\s*=.*)$', 'FFLAGS = -O3 -fPIC -ffree-line-length-0 -fopenmp', self.makefile)

    @when("@master +openmp %pgi")
    def compiler_based(self):
        filter_file('^\s*(MOD_DIR_OPT\s*=.*)$', 'MOD_DIR_OPT = -module', self.makefile)
        filter_file('^\s*(FFLAGS\s*=.*)$', 'FFLAGS = -fast -D__PGI -fpic -mp', self.makefile)


    @when("@master +gpu")
    def setup_environment(self, spack_env, run_env):
        spack_env.set("XGC_PLATFORM", "summit")
        """
        if self.spec.satisfies("%gcc"):
            raise ValueError("GPU compilation requires PGI")
        """
        self.makefile = os.path.join("build", "make.inc.summit")

    @when("@master +gpu")
    def cmake(self, spec, prefix):
        self.edit(self.spec, prefix)
        self.compiler_based()
        filter_file('^\s*(PSPLINE_INC\s*=.*)$', 'PSPLINE_INC = -I{0}'.format(spec[self.pspline].prefix.include), self.makefile)
        filter_file('^\s*(XGC_FLAGS\s*\+=\s*-DITER_GRID)', 'XGC_FLAGS += -DDELTAF_MODE2 -DITER_GRID', self.flagfile)
        filter_file('^\s*(CXX\s*=.*)$', 'CXX = $(KOKKOS_SRC_DIR)/bin/nvcc_wrapper --verbose', self.makefile)
        filter_file('^\s*(NVCC_WRAPPER_DEFAULT_COMPILER\s*=.*)$', "NVCC_WRAPPER_DEFAULT_COMPILER = {0}".format(spec['mpi'].mpicxx), self.makefile)
        #filter_file('^\s*(NVCC_WRAPPER_DEFAULT_COMPILER\s*=.*)$', "NVCC_WRAPPER_DEFAULT_COMPILER = {0}".format("/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-9.1.0/spectrum-mpi-10.3.0.1-20190611-2juhkwlddpdydl2yasmuia2slpev6fl5/bin/mpicc"), self.makefile)

    @when("@master +gpu")
    def build(self, spec, prefix):
        make('xgc-es-cab', parallel=False)
        #make('xgc-es-gpu', parallel=False)

    @when("@master +gpu")
    def install(self, spec, prefix):
        binary = "xgc-es-cab"
        #binary = "xgc-es-gpu"
        mkdirp(self.prefix.bin)
        install(os.path.join("xgc_build", binary), self.prefix.bin, binary)
        install(self.makefile, os.path.join(self.prefix.bin))
    '''

    def CMakeOption(self, option, args):
        if self.spec.satisfies('+{0}'.format(option)):
            args += ["-D{0}=ON".format(option.upper())]
        elif self.spec.satisfies('-{0}'.format(option)):
            args += ["-D{0}=OFF".format(option.upper())]


    @when("@master")
    def setup_environment(self, spack_env, run_env):
        spack_env.set("XGC_PLATFORM", "generic")
        """
        if self.spec.satisfies("+gpu"):
            #spack_env.set('NVCC_WRAPPER_DEFAULT_COMPILER', self.spec['mpi'].mpicxx)
            spack_env.set('NVCC_WRAPPER_DEFAULT_COMPILER', 'g++')
        """

    @when("@master")
    def cmake_args(self):
        #filter_file('include\(find_dependencies', 'MESSAGE(STATUS ${XGC_PLATFORM})\ninclude(find_dependencies', join_path(self.stage.source_path, 'CMakeLists.txt'))
        #filter_file('INTERFACE kokkos', 'INTERFACE OpenMP::OpenMP_CXX', join_path(self.stage.source_path, 'CMakeLists.txt'))

        filter_file('if\(Kokkos_FOUND\)', 'if(NOT Kokkos_FOUND)', join_path(self.stage.source_path, 'CMake', 'FindKokkos.cmake'))
        filter_file('kokkos', 'Kokkos::kokkos', join_path(self.stage.source_path, 'CMake', 'FindCabana.cmake'))

        filter_file('TARGET kokkos', 'TARGET Kokkos::kokkos', join_path(self.stage.source_path, 'CMakeLists.txt'))
        filter_file('INTERFACE kokkos', 'INTERFACE Kokkos::kokkos', join_path(self.stage.source_path, 'CMakeLists.txt'))
        #filter_file('INTERFACE kokkos', 'INTERFACE OpenMP::OpenMP_CXX -std=c++11', join_path(self.stage.source_path, 'CMakeLists.txt'))

        args = ['-DCMAKE_Fortran_COMPILER={0}'.format(self.spec['mpi'].mpifc)]

        if self.spec.satisfies("+gpu"):
            if self.spec.satisfies('%gcc'):
                filter_file('"PGI"', '"GNU"', join_path(self.stage.source_path, 'CMakeLists.txt'))
                filter_file('__PGI', '__GFORTRAN__', join_path(self.stage.source_path, 'CMakeLists.txt'))
                filter_file('XGC_HAVE_OpenACC TRUE', 'XGC_HAVE_OpenACC FALSE', join_path(self.stage.source_path, 'CMakeLists.txt'))
            """
            elif self.spec.satisfies('%pgi'):
                filter_file('"PGI"', '"GNU"', join_path(self.stage.source_path, 'CMakeLists.txt'))
                #filter_file('LINKER_LANGUAGE Fortran', 'OUTPUT_NAME ${exe}', join_path(self.stage.source_path, 'CMakeLists.txt'))
                args += ['-DCMAKE_LINKER=gfortran']
                args += ['-DCMAKE_Fortran_LINK_EXECUTABLE=<CMAKE_LINKER> <FLAGS> <CMAKE_CXX_LINK_FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES>']
                #args += ['-DCMAKE_CXX_LINK_EXECUTABLE=<CMAKE_LINKER> <FLAGS> <CMAKE_CXX_LINK_FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES>']
            """
            args += ['-DCMAKE_CXX_COMPILER={0}'.format(join_path(self.spec['kokkos-cmake'].prefix.bin, 'nvcc_wrapper'))]

        else:
            args += ['-DCMAKE_CXX_COMPILER={0}'.format(self.spec['mpi'].mpicxx)]

        if self.spec.satisfies('+effis'):
            args += ["-DEFFIS=ON"]

        """
        if self.spec.satisfies('+convert_grid2'):
            args += ["-DCONVERT_GRID2=ON"]
        elif self.spec.satisfies('-convert_grid2'):
            args += ["-DCONVERT_GRID2=OFF"]
        """

        for option in self.xgc_options:
            self.CMakeOption(option, args)

        #filter_file('CONVERT_GRID2', "", os.path.join('XGC_core', 'CMakeLists.txt'))  # I don't have an appropriate file to configure with yet

        return args

    @when("@master")
    def install(self, spec, prefix):
        mkdirp(self.prefix.bin)
        install(join_path(self.build_directory, "bin", "xgc-es-cpp"), self.prefix.bin)
        if self.spec.satisfies("+gpu"):
            install(join_path(self.build_directory, "bin", "xgc-es-cpp-gpu"), self.prefix.bin)


    @when("@gabriele,gitlab -gpu")
    def setup_environment(self, spack_env, run_env):
        self.makefile = os.path.join("Makefile.theta")

    @when("@gabriele,gitlab -gpu")
    def cmake(self, spec, prefix):
        self.edit(spec, prefix)
        filter_file('^\s*(PSPLINE_INC\s*=.*)$', 'PSPLINE_INC = -I{0}/mod'.format(spec["pspline"].prefix), self.makefile)

        if self.spec.satisfies("%pgi"):
            filter_file('-J', '-module', self.makefile)
            filter_file("-ffree-line-length-none", "", self.makefile)

        if self.spec.satisfies("-openmp"):
            filter_file("-fopenmp", "", self.makefile)
        elif self.spec.satisfies("%pgi"):
            filter_file("-fopenmp", "-mp", self.makefile)

    @when("@gabriele,gitlab -gpu")
    def build(self, spec, prefix):
        make('-f', self.makefile, 'es', parallel=False)

    @when("@gabriele,gitlab -gpu")
    def install(self, spec, prefix):
        mkdirp(self.prefix.bin)
        binary = "xgc-es"
        install(os.path.join(binary), self.prefix.bin)
        install("coupling_core_edge.F90", self.prefix.bin)
