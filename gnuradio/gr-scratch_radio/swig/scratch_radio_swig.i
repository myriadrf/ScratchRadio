/* -*- c++ -*- */

#define SCRATCH_RADIO_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "scratch_radio_swig_doc.i"

%{
#include "scratch_radio/manc_enc.h"
#include "scratch_radio/manc_dec.h"
#include "scratch_radio/simple_framer.h"
#include "scratch_radio/simple_deframer.h"
#include "scratch_radio/message_source.h"
#include "scratch_radio/message_sink.h"
#include "scratch_radio/ook_modulator.h"
#include "scratch_radio/ook_demodulator.h"
#include "scratch_radio/symbol_sync.h"
#include "scratch_radio/fast_agc_cc.h"
%}


%include "scratch_radio/manc_enc.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, manc_enc);
%include "scratch_radio/manc_dec.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, manc_dec);
%include "scratch_radio/simple_framer.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, simple_framer);
%include "scratch_radio/simple_deframer.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, simple_deframer);
%include "scratch_radio/message_source.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, message_source);
%include "scratch_radio/message_sink.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, message_sink);
%include "scratch_radio/ook_modulator.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, ook_modulator);
%include "scratch_radio/ook_demodulator.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, ook_demodulator);
%include "scratch_radio/symbol_sync.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, symbol_sync);
%include "scratch_radio/fast_agc_cc.h"
GR_SWIG_BLOCK_MAGIC2(scratch_radio, fast_agc_cc);
