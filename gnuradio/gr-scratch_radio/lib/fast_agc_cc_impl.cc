/* -*- c++ -*- */
/* 
 * Copyright 2018 <+YOU OR YOUR COMPANY+>.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "fast_agc_cc_impl.h"

#include <cmath>

#define ESTIMATOR_ALPHA 0.947543636291
#define ESTIMATOR_BETA  0.392485425092

namespace gr {
  namespace scratch_radio {

    fast_agc_cc::sptr
    fast_agc_cc::make(float rate, float reference, float gain, float max_gain)
    {
      return gnuradio::get_initial_sptr
        (new fast_agc_cc_impl(rate, reference, gain, max_gain));
    }

    /*
     * The private constructor
     */
    fast_agc_cc_impl::fast_agc_cc_impl(float rate, float reference, float gain, float max_gain)
      : gr::sync_block("fast_agc_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex)))
    {
	  d_rate = rate;
	  d_reference = reference;
	  d_gain = gain;
	  d_max_gain = max_gain;
	}

    /*
     * Our virtual destructor.
     */
    fast_agc_cc_impl::~fast_agc_cc_impl()
    {
    }

    int
    fast_agc_cc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      for (int i = 0; i < noutput_items; i++) {
		
		// Use existing gain for current input sample.
		gr_complex input = in[i];
		float scaled_re = d_gain * input.real();
		float scaled_im = d_gain * input.imag();
		out[i] = gr_complex (scaled_re, scaled_im);
		
		// Use the 'Alpha * Max + Beta * Min' magnitude estimator to 
		// avoid executing a floating point square root on every sample!
		float abs_re = abs (scaled_re);
		float abs_im = abs (scaled_im);
		float max = (abs_re > abs_im) ? abs_re : abs_im;
		float min = (abs_re > abs_im) ? abs_im : abs_re;
		float mag_in = ESTIMATOR_ALPHA * max + ESTIMATOR_BETA * min;
		d_gain += d_rate * (d_reference - mag_in);
		
		// Limit gain if required.
		if ((d_max_gain > 0.0) && (d_gain > d_max_gain))
		  d_gain = d_max_gain;  
	  }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

