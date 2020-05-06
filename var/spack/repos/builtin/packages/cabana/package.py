# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Cabana(CMakePackage):
    """The Exascale Co-Design Center for Particle Applications Toolkit
    """
    homepage = "https://github.com/ECP-copa/Cabana"
    git      = "https://github.com/ECP-copa/Cabana.git"
    url      = "https://github.com/ECP-copa/Cabana/archive/0.1.0.tar.gz"

    version('develop', branch='master')
    version('0.3.0', sha256='fb67ab9aaf254b103ae0eb5cc913ddae3bf3cd0cf6010e9686e577a2981ca84f')
    version('0.1.0', sha256='3280712facf6932b9d1aff375b24c932abb9f60a8addb0c0a1950afd0cb9b9cf')
    version('0.1.0-rc0', sha256='73754d38aaa0c2a1e012be6959787108fec142294774c23f70292f59c1bdc6c5')

    variant('openmp', default=False, description="enable OpenMP backend")
    variant('mpi', default=False, description="enable MPI")
    variant('cuda', default=False, description="enable Cuda")

    depends_on("mpi", when="+mpi")
    depends_on("cmake@3.9:", type='build')

    depends_on("kokkos-cmake +serial +aggressive_vectorization cxxstd=11")
    depends_on("kokkos-cmake +openmp", when="+openmp")
    depends_on("kokkos-cmake +cuda", when="+cuda")


    def cmake_args(self):
        options = [
            '-DCabana_ENABLE_TESTING=ON',
            '-DCMAKE_POLICY_DEFAULT_CMP0074=NEW'
            ]
        if self.spec.satisfies('+mpi'):
            options += ["-DCabana_ENABLE_MPI=ON"]

        if self.spec.satisfies("+cuda"):
            #env['NVCC_WRAPPER_DEFAULT_COMPILER'] = self.compiler.cxx
            #env['NVCC_WRAPPER_DEFAULT_COMPILER'] = self.spec['mpi'].mpicxx
            env['NVCC_WRAPPER_DEFAULT_COMPILER'] = 'g++'
            options += ['-DCMAKE_CXX_COMPILER={0}'.format(join_path(self.spec['kokkos-cmake'].prefix.bin, 'nvcc_wrapper'))]
            """
            if self.spec.satisfies("+mpi"):
                options += ['-DMPI_CXX_COMPILER={0}'.format(self.spec['mpi'].mpicxx)]
            """
        elif self.spec.satisfies("+mpi"):
            options += ['-DCMAKE_CXX_COMPILER={0}'.format(self.spec['mpi'].mpicxx)]
        else:
            options += ['-DCMAKE_CXX_COMPILER={0}'.format(env['CXX'])]

        return options
