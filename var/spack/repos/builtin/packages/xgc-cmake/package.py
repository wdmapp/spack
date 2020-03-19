from spack import *
import os
import shutil


class XgcCmake(CMakePackage):
    """ XGC tokamak simulation code """
    parallel = False
    homepage = "https://bitbucket.org/madams/epsi/overview"
    url = "https://bitbucket.org/madams/epsi/overview"

    version('test', git='https://github.com/suchyta1/XGC-Devel.git', branch='effis-twod')

    variant("effis",  default=False, description='EFFIS support')
    variant("adios2", default=True,  description='Enable ADIOS-2')
    variant("tests",  default=True,  description='Build tests')
    variant("convert_grid2", default=False,  description='CONVERT_GRID2')

    depends_on('mpi')
    depends_on('fftw')
    #depends_on('petsc -complex +superlu-dist @3.7.0:3.7.8')
    #depends_on('petsc -complex -superlu-dist @3.7.0:3.7.8')
    #depends_on('petsc -complex -superlu-dist @3.7.0:3.10.99')
    depends_on('petsc -complex -superlu-dist @3.7.0:3.7.99')
    depends_on('parmetis')
    depends_on('metis +real64')
    #depends_on('superlu-dist@:5.2.2')
    depends_on('hdf5 +mpi +fortran +hl')
    depends_on("adios")
    #depends_on("dataspaces")

    conflicts("effis",   when="-adios2")
    depends_on('adios2', when="+adios2")
    depends_on('kittie', when="+effis")


    def cmake_args(self):
        args = []
        if self.spec.satisfies('+effis'):
            args += ["-DEFFIS=ON"]
        if self.spec.satisfies('-tests'):
            args += ["-DBUILD_TESTING=OFF"]

        if self.spec.satisfies('-convert_grid2'):
            args += ["-DCONVERT_GRID2=OFF"]
            filter_file('CONVERT_GRID2', "", os.path.join('XGC_core', 'CMakeLists.txt'))  # I don't have an appropriate file to configure with yet

        return args


    def install(self, spec, prefix):
        for outdir in [self.prefix.XGC1, self.prefix.XGCa]:
            if not os.path.exists(outdir):
                os.makedirs(outdir)

        with working_dir(self.build_directory):
            shutil.copy(os.path.join('XGCa', 'xgca'),    self.prefix.XGCa)
            shutil.copy(os.path.join('XGC1', 'xgc1-es'), self.prefix.XGC1)

            """
            shutil.copy(os.path.join('XGC1', 'diagnosis-kittie.F90'), self.prefix.XGC1)
            shutil.copy(os.path.join('XGC_core', 'adios2_comm_mod-kittie.F90'), self.prefix.XGC1)
            """

