from spack import *
import os
import shutil


class XgcDevelCmake(CMakePackage):
    """ XGC tokamak simulation code """
    homepage = "https://bitbucket.org/madams/epsi/overview"
    url = "https://bitbucket.org/madams/epsi/overview"

    version('master',  git='https://github.com/PrincetonUniversity/XGC-Devel.git', branch='master', preferred=True)
    version('kevin',   git='https://github.com/khuck/XGC-Devel.git', branch='master', preferred=False)
    version('commit',  git='https://github.com/PrincetonUniversity/XGC-Devel.git', commit='63eb658c87bab810ff70e6e95add85a4ab61a94b', preferred=False)
    version('effis',   git='https://github.com/suchyta1/XGC-Devel.git', branch='effis-more')


    parallel = False
    cpu_values = ["SKX", "Power9", "SNB"]
    cuda_values = ["Volta70", "Turing75", "Kepler30"]
    xgc_options = ["convert_grid2", "deltaf_mode2", "init_gene_pert", 'col_f_positivity_opt', 'neoclassical_test', "iter_grid", "effis", 'build_testing', "fusion_io"]

    variant('openmp', default=False, description="Build with OpenMP")
    variant('openacc', default=False, description="Build with OpenACC")
    variant('debug', default=False, description="Use debug symbols")
    variant('cuda', default="none", values=cuda_values, description="Build Cuda")
    variant('host_arch', default="none", values=cpu_values, description="CPU optimization")
    for option in xgc_options:
        variant(option, default=False, description='-D{0}'.format(option.upper()))

    depends_on('mpi')
    depends_on('fftw')
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
    conflicts('+openacc', when="cuda=none")

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

    
    def Append(self, line):
        self.makestream.write("\n" + line)


    def cmake_args(self):

        if not self.spec.satisfies("cuda=none"):
            self.binary = 'xgc-es-cpp-gpu'
            #env['NVCC_WRAPPER_DEFAULT_COMPILER'] = self.spec['mpi'].mpicxx
            env['NVCC_WRAPPER_DEFAULT_COMPILER'] = self.compiler.cxx
            cxx = which("nvcc_wrapper").path
        else:
            self.binary = 'xgc-es-cpp'
            cxx = self.spec['mpi'].mpicxx


        opts = [
                "-DCMAKE_CXX_COMPILER={0}".format(cxx),
                "-DCMAKE_Fortran_COMPILER={0}".format(self.spec['mpi'].mpifc),
                "-DXGC_USE_CABANA=ON",
                "-DUSE_SYSTEM_CAMTIMERS=ON",
                "-DUSE_SYSTEM_PSPLINE=ON",
                "-DXGC_USE_ADIOS2=ON"
                ]

        for option in self.xgc_options[:-2]:
            if self.spec.satisfies("+{0}".format(option)):
                opts  += ["-D{0}=ON".format(option.upper())]

        if self.spec.satisfies("+fusion_io"):
            opts += ["-DXGC_USE_FUSION=ON"]

        if self.spec.satisfies("+build_testing"):
            opts += ["-DBUILD_TESTING=ONF"]
        else:
            opts += ["-DBUILD_TESTING=OFF"]
            

        if self.spec.satisfies("%pgi"):
            link_flags = "-pgc++libs"
            if not self.spec.satisfies("cuda=none"):
                link_flags = link_flags + " " + "-Mcuda=cuda{1},cc{0},ptxinfo,maxrregcount:128".format(self.spec.variants['cuda'].value[-2:], self.spec['cuda'].version.up_to(2))
                gpu_fortran_flags = "-Minfo=accel -Mcuda=cuda{1},cc{0}".format(self.spec.variants['cuda'].value[-2:], self.spec['cuda'].version.up_to(2))
                gpu_link_flags = "-Minfo=accel"
                if self.spec.satisfies("+openacc"):
                    gpu_fortran_flags = gpu_fortran_flags + " " + "-ta=tesla:cc{0}".format(self.spec.variants['cuda'].value[-2:])
                    gpu_link_flags = gpu_link_flags + " " + "-ta=tesla:cc{0} -Mnostack_arrays -DUSE_ASYNC".format(self.spec.variants['cuda'].value[-2:])
            else:
                gpu_fortran_flags = ""
                gpu_link_flags = ""

        elif self.spec.satisfies("%gcc"):
            link_flags = ""
            if self.spec.satisfies("+openacc"):
                gpu_fortran_flags = "-fopenacc"
                gpu_link_flags = "-fopenacc -DUSE_ASYNC"
            else:
                gpu_fortran_flags = ""
                gpu_link_flags = ""

        platform = "spack"
        env["XGC_PLATFORM"] = platform
        self.makefile = join_path("CMake", "find_dependencies_{0}.cmake".format(platform))
        self.makestream = open(self.makefile, "w")
        self.Append("set(GPU_Fortran_FLAGS {0})".format(gpu_fortran_flags))
        self.Append("set(LINK_FLAGS {0})".format(link_flags))
        self.Append("set(GPU_LINK_FLAGS {0})".format(gpu_link_flags))
        self.Append("find_package(FFTW3 REQUIRED)")
        self.Append("find_package(LAPACK REQUIRED)")
        self.Append("find_package(PETSC REQUIRED)")
        self.makestream.close()


        self.flagfile = join_path("build", "xgc_flags.mk")
        filter_file('^\s*(XGC_FLAGS\s*\+=.*)', 'XGC_FLAGS += ', self.flagfile)
        filter_file('PATH_SUFFIXES include', 'PATH_SUFFIXES include mod', join_path(self.stage.source_path, 'CMake', 'FindPSPLINE.cmake'))
        filter_file('kokkos', 'Kokkos::kokkos', join_path(self.stage.source_path, 'CMake', 'FindCabana.cmake'))

        if self.spec.satisfies('^cabana @suchyta') or self.spec.satisfies('^cabana @:0.2.99'):
            kfile = join_path(self.stage.source_path, 'CMake', 'FindKokkos.cmake')
            os.remove(kfile)
            shutil.copy(join_path(self.spec['cabana'].prefix, 'FindKOKKOS.cmake'), kfile)
            filter_file("KOKKOS DEFAULT_MSG", "Kokkos DEFAULT_MSG", kfile)
        else:
            filter_file('if\(Kokkos_FOUND\)', 'if(NOT Kokkos_FOUND)', join_path(self.stage.source_path, 'CMake', 'FindKokkos.cmake'))

        filter_file('TARGET kokkos', 'TARGET Kokkos::kokkos', join_path(self.stage.source_path, 'CMakeLists.txt'))
        filter_file('INTERFACE kokkos', 'INTERFACE Kokkos::kokkos', join_path(self.stage.source_path, 'CMakeLists.txt'))
        if not self.spec.satisfies("+openacc"):
            filter_file('XGC_HAVE_OpenACC TRUE', 'XGC_HAVE_OpenACC FALSE', join_path(self.stage.source_path, 'CMakeLists.txt'))

        if self.spec.satisfies('%gcc'):
            filter_file('"PGI"', '"GNU"', join_path(self.stage.source_path, 'CMakeLists.txt'))
            filter_file('__PGI', '__GFORTRAN__', join_path(self.stage.source_path, 'CMakeLists.txt'))
            filter_file('LINKER_LANGUAGE Fortran', 'LINKER_LANGUAGE CXX', join_path(self.stage.source_path, 'CMakeLists.txt'))

        return opts


    def build(self, spec, prefix):
        with working_dir(self.build_directory):
            make(self.binary, parallel=False)


    def install(self, spec, prefix):
        mkdirp(self.prefix.bin)
        install(join_path(self.build_directory, "bin", self.binary), self.prefix.bin)
        install(self.makefile, self.prefix)
        install(self.flagfile, self.prefix)

