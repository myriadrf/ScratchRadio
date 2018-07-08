# Copyright 2011,2012,2016 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

########################################################################
# Setup library
########################################################################
include(GrPlatform) #define LIB_SUFFIX

include_directories(${Boost_INCLUDE_DIR})
link_directories(${Boost_LIBRARY_DIRS})

list(APPEND scratch_radio_sources
    manc_enc_impl.cc
    manc_dec_impl.cc
    simple_framer_impl.cc
    simple_deframer_impl.cc
    message_source_impl.cc
    message_sink_impl.cc
    ook_modulator_impl.cc
    ook_demodulator_impl.cc
    symbol_sync_impl.cc
    fast_agc_cc_impl.cc
)

set(scratch_radio_sources "${scratch_radio_sources}" PARENT_SCOPE)
if(NOT scratch_radio_sources)
	MESSAGE(STATUS "No C++ sources... skipping lib/")
	return()
endif(NOT scratch_radio_sources)

add_library(gnuradio-scratch_radio SHARED ${scratch_radio_sources})
target_link_libraries(gnuradio-scratch_radio ${Boost_LIBRARIES} ${GNURADIO_ALL_LIBRARIES})
set_target_properties(gnuradio-scratch_radio PROPERTIES DEFINE_SYMBOL "gnuradio_scratch_radio_EXPORTS")

if(APPLE)
    set_target_properties(gnuradio-scratch_radio PROPERTIES
        INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
    )
endif(APPLE)

########################################################################
# Install built library files
########################################################################
include(GrMiscUtils)
GR_LIBRARY_FOO(gnuradio-scratch_radio RUNTIME_COMPONENT "scratch_radio_runtime" DEVEL_COMPONENT "scratch_radio_devel")

########################################################################
# Build and register unit test
########################################################################
include(GrTest)

include_directories(${CPPUNIT_INCLUDE_DIRS})

list(APPEND test_scratch_radio_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/test_scratch_radio.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/qa_scratch_radio.cc
)

add_executable(test-scratch_radio ${test_scratch_radio_sources})

target_link_libraries(
  test-scratch_radio
  ${GNURADIO_RUNTIME_LIBRARIES}
  ${Boost_LIBRARIES}
  ${CPPUNIT_LIBRARIES}
  gnuradio-scratch_radio
)

GR_ADD_TEST(test_scratch_radio test-scratch_radio)

########################################################################
# Print summary
########################################################################
message(STATUS "Using install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "Building for version: ${VERSION} / ${LIBVER}")

