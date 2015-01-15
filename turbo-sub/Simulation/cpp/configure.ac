#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.68])
AC_INIT([simulator], [1.1], [petergao@berkeley.edu])
AM_INIT_AUTOMAKE(simulator, 1.1)
AC_CONFIG_HEADERS([config.h])

# Checks for programs.
AC_PROG_CXX
CFLAGS="-g -O3 -std=c++0x"
AC_PROG_CC
AC_PROG_CPP
AC_PROG_MAKE_SET

# Checks for libraries.

# Checks for header files.
AC_CHECK_HEADERS([float.h stdint.h stdlib.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_HEADER_STDBOOL
AC_TYPE_INT32_T
AC_TYPE_UINT32_T
AC_TYPE_UINT64_T

# Checks for library functions.

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
