# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *
import shutil
import os


class KokkosCmake(CMakePackage):
    """Kokkos implements a programming model in C++ for writing performance
    portable applications targeting all major HPC platforms."""

    homepage = "https://github.com/kokkos/kokkos"
    url      = "https://github.com/kokkos/kokkos/archive/2.03.00.tar.gz"
    git      = "https://github.com/kokkos/kokkos.git"

    version('develop', branch='develop')
    version('master', branch='master')
    version('3.1.00', sha256='b935c9b780e7330bcb80809992caa2b66fd387e3a1c261c955d622dae857d878')
    version('2.9.00', sha256='e0621197791ed3a381b4f02c78fa529f3cff3abb74d52157b4add17e8aa04bc4')
    version('2.8.00', sha256='1c72661f2d770517bff98837001b42b9c677d1df29f7493a1d7c008549aff630')
    version('2.7.24', sha256='a308a80ea1488f4c18884b828ce7ae9f5210b9a6b2f61b208d875084d8da8cb0')
    version('2.7.00',  sha256='01595996e612ef7410aa42fa265a23101cfe1b6993fa9810ca844db5c89ad765')
    version('2.5.00',  sha256='ea232594bf746abb99ae2aafaeef5d07adc089968010a62a88aaa892106d9476')
    version('2.04.11', sha256='f2680aee0169f6cbbec38410f9c80bf8a160435f6a07769c1e9112da8b9349a0')
    version('2.04.04', sha256='5bac8ddc2fac9bc6e01dd40f92ca6cbbb346a25deca5be2fec71acf712d0d0c7')
    version('2.04.00', sha256='b04658d368986df207662a7a37c1ad974c321447bc2c2b5b696d7e9ee4481f34')
    version('2.03.13', sha256='002748bdd0319d5ab82606cf92dc210fc1c05d0607a2e1d5538f60512b029056')
    version('2.03.05', sha256='b18ddaa1496130ff3f675ea9ddbc6df9cdf378d53edf96df89e70ff189e10e1d')
    version('2.03.00', sha256='722bea558d8986efee765ac912febb3c1ce289a8e9bdfef77cd0145df0ea8a3d')
    version('2.02.15', sha256='6b4a7f189f0341f378f950f3c798f520d2e473b13435b137ff3b666e799a076d')
    version('2.02.07', sha256='7b4ac81021d6868f4eb8e2a1cb92ba76bad9c3f197403b8b1eac0f11c983247c')

    variant('debug', default=False, description="Build debug version of Kokkos")

    variant('serial', default=True, description="enable Serial backend (default)")
    variant('pthreads', default=False, description="enable Pthreads backend")
    variant('qthreads', default=False, description="enable Qthreads backend")
    variant('cuda', default=False, description="enable Cuda backend")
    variant('openmp', default=False, description="enable OpenMP backend")
    variant('librt', default=False, description="enable librt")

    # Compilation options
    variant('pic', default=False,
            description="enable position independent code (-fPIC flag)")

    # Kokkos options
    variant('aggressive_vectorization', default=False,
            description="set aggressive_vectorization Kokkos option")
    variant('disable_profiling', default=False,
            description="set disable_profiling Kokkos option")
    variant('disable_dualview_modify_check', default=False,
            description="set disable_dualview_modify_check Kokkos option")
    variant('enable_profile_load_print', default=False,
            description="set enable_profile_load_print Kokkos option")
    variant('compiler_warnings', default=False,
            description="set compiler_warnings Kokkos option")
    variant('disable_deprecated_code', default=False,
            description="set disable_deprecated_code Kokkos option")
    variant('enable_eti', default=False,
            description="set enable_eti Kokkos option")

    # CUDA options
    variant('force_uvm', default=False,
            description="set force_uvm Kokkos CUDA option")
    variant('use_ldg', default=False,
            description="set use_ldg Kokkos CUDA option")
    variant('rdc', default=False,
            description="set rdc Kokkos CUDA option")
    variant('enable_lambda', default=False,
            description="set enable_lambda Kokkos CUDA option")
    variant('hwloc', default=False,
            description="enable HWLOC")

    gpu_values = ('Kepler30', 'Kepler32', 'Kepler35', 'Kepler37',
                  'Maxwell50', 'Maxwell52', 'Maxwell53',
                  'Pascal60', 'Pascal61',
                  'Volta70', 'Volta72', 'Turing75')

    # C++ standard variant
    variant('cxxstd', default='none',
            values=('c++11', 'c++14', 'c++17', 'c++1y', 'c++1z', 'c++2a', '11'),
            multi=False,
            description='set cxxstandard Kokkos option')

    # Host architecture variant
    variant(
        'host_arch',
        default='none',
        values=('AMDAVX', 'ARMv80', 'ARMv81', 'ARMv8-ThunderX',
                'Power7', 'Power8', 'Power9',
                'WSM', 'SNB', 'HSW', 'BDW', 'SKX', 'KNC', 'KNL'),
        description='Set the host architecture to use'
    )

    # GPU architecture variant
    variant(
        'gpu_arch',
        default='none',
        values=gpu_values,
        description='Set the GPU architecture to use'
    )

    # Checks on Kokkos version and Kokkos options
    conflicts('+aggressive_vectorization', when='@:2.0.99',)
    conflicts('+disable_profiling', when='@:2.0.99',)
    conflicts('+disable_dualview_modify_check', when='@:2.03.04',)
    conflicts('+enable_profile_load_print', when='@:2.03.04',)
    conflicts('+compiler_warnings', when='@:2.03.14',)
    conflicts('+disable_deprecated_code', when='@:2.5.99',)
    conflicts('+enable_eti', when='@:2.6.99',)

    # Check that we haven't specified a gpu architecture
    # without specifying CUDA
    for p in gpu_values:
        conflicts('gpu_arch={0}'.format(p), when='~cuda',
                  msg='Must specify CUDA backend to use a GPU architecture.')

    # Check that we haven't specified a Kokkos CUDA option
    # without specifying CUDA
    conflicts('+force_uvm', when='~cuda',
              msg='Must enable CUDA to use force_uvm.')
    conflicts('+use_ldg', when='~cuda',
              msg='Must enable CUDA to use use_ldg.')
    conflicts('+rdc', when='~cuda',
              msg='Must enable CUDA to use rdc.')
    conflicts('+enable_lambda', when='~cuda',
              msg='Must enable CUDA to use enable_lambda.')

    # Check that we haven't asked for a GPU architecture that
    # the revision of kokkos does not support
    conflicts('gpu_arch=Volta70', when='@:2.5.99')
    conflicts('gpu_arch=Volta72', when='@:2.5.99')
    conflicts('gpu_arch=Turing75', when='@:2.5.99')

    # conflicts on kokkos version and cuda enabled
    # see kokkos issue #1296
    # https://github.com/kokkos/kokkos/issues/1296
    conflicts('+cuda', when='@2.5.00:2.7.00',
              msg='Kokkos build system has issue (#1296) when CUDA enabled'
              ' in version 2.5.00 through 2.7.00.')

    # Specify that v1.x is required as v2.x has API changes
    depends_on('hwloc@:1', when="+hwloc")
    depends_on('qthreads', when='+qthreads')
    depends_on('cuda', when='+cuda')

    # According to documentation and trial and error, GPU build is only stable with certain GCC versions and maybe Intel
    #conflicts('%pgi', when="+cuda")
    parallel = False


    def cmake_args(self):

        if self.spec.satisfies('+cuda'):
            env['NVCC_WRAPPER_DEFAULT_COMPILER'] = self.compiler.cxx
            args = ['-DCMAKE_CXX_COMPILER={0}'.format(join_path(self.stage.source_path, 'bin', 'nvcc_wrapper'))]
        else:
            args = ['-DCMAKE_CXX_COMPILER={0}'.format(env['CXX'])]

        if self.spec.variants['gpu_arch'].value != 'none':
            args += ['-DKokkos_ARCH_{0}=ON'.format(self.spec.variants['gpu_arch'].value.upper())]
        if self.spec.variants['host_arch'].value != 'none':
            args += ['-DKokkos_ARCH_{0}=ON'.format(self.spec.variants['host_arch'].value.upper())]

        if self.spec.satisfies('+serial'):
            args += ['-DKokkos_ENABLE_SERIAL=ON']
        if self.spec.satisfies('+openmp'):
            args += ['-DKokkos_ENABLE_OPENMP=ON']
        if self.spec.satisfies('+pthreads'):
            args += ['-DKokkos_ENABLE_PTHREAD=ON']
        if self.spec.satisfies('+qthreads'):
            args += ['-DKokkos_ENABLE_QTHREADS=ON']
        if self.spec.satisfies('+cuda'):
            args += ['-DKokkos_ENABLE_CUDA=ON']
        if self.spec.satisfies('+librt'):
            args += ['-DKokkos_ENABLE_LIBRT=ON']

        if self.spec.variants['cxxstd'].value != 'none':
            args += ['-DKokkos_CXX_STANDARD={0}'.format(self.spec.variants['cxxstd'].value)]
        if self.spec.satisfies('+pic'):
            args += ['-DBUILD_SHARED_LIBS=ON']
        if self.spec.satisfies('+debug'):
            args += ['-DKokkos_ENABLE_DEBUG=ON']

        if self.spec.satisfies('+force_uvm'):
            args += ['-DKokkos_ENABLE_CUDA_UVM=ON']
        if self.spec.satisfies('+use_ldg'):
            args += ['-DKokkos_ENABLE_CUDA_LDG_INTRINSIC=ON']
        if self.spec.satisfies('+rdc'):
            args += ['-Dkokkos_ENABLE_CUDA_RELOCATABLE_DEVICE_CODE=ON']
        if self.spec.satisfies('+enable_lambda'):
            args += ['-DKokkos_ENABLE_CUDA_LAMBDA=ON']

        if self.spec.satisfies('+hwloc'):
            args +=  ['-DKokkos_ENABLE_HWLOC=ON']
        if self.spec.satisfies('+aggressive_vectorization'):
            args += ['-DKokkos_ENABLE_AGGRESSIVE_VECTORIZATION=ON']
        if self.spec.satisfies('+disable_profiling'):
            args += ['-DKokkos_ENABLE_PROFILING=OFF']
        if self.spec.satisfies('+enable_profile_load_print'):
            args += ['-DKokkos_ENABLE_PROFILING_LOAD_PRINT=ON']
        if self.spec.satisfies('+compiler_warnings'):
            args += ['-DKokkos_ENABLE_COMPILER_WARNINGS=ON']
        if self.spec.satisfies('+enable_eti'):
            args += ['-DKokkos_ENABLE_ETI=ON']

        if self.spec.satisfies('+disable_dualview_modify_check'):
            args += ['-DKokkos_ENABLE_DEBUG_DUALVIEW_MODIFY_CHECK=OFF']
        else:
            args += ['-DKokkos_ENABLE_DEBUG_DUALVIEW_MODIFY_CHECK=ON']

        if self.spec.satisfies('+disable_deprecated_code'):
            args += ['-DKokkos_ENABLE_DEPRECATED_CODE=OFF']
        else:
            args += ['-DKokkos_ENABLE_DEPRECATED_CODE=ON']

        return args

