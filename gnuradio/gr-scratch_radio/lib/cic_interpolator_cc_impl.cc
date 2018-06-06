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
#include "cic_interpolator_cc_impl.h"

namespace gr {
  namespace scratch_radio {

    cic_interpolator_cc::sptr
    cic_interpolator_cc::make(int int_factor, int cic_stages)
    {
      return gnuradio::get_initial_sptr
        (new cic_interpolator_cc_impl(int_factor, cic_stages));
    }

    /*
     * The private constructor
     */
    cic_interpolator_cc_impl::cic_interpolator_cc_impl(int int_factor, int cic_stages)
      : gr::sync_interpolator("cic_interpolator_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex)), int_factor)
    {
      // Determine the number of bits required to encode the decimation
      // factor, which sets the required bit width extension at each CIC
      // integrator stage.
      int ext_bits;
      for (ext_bits = 0; (int_factor >> ext_bits) > 1; ext_bits++);

      // Based on 64-bit fixed point integrators with 32 fractional bits
      // determine whether the specified decimation factor and number of
      // CIC stages would cause invalid overflow.
      if (ext_bits * cic_stages > 32)
        throw "CIC filter parameters would cause 64-bit overflow.";

      d_int_factor = int_factor;
      d_cic_stages = cic_stages;
      d_integrator_state_re = new int64_t [cic_stages];
      d_integrator_state_im = new int64_t [cic_stages];
      d_comb_state_re = new int64_t [cic_stages];
      d_comb_state_im = new int64_t [cic_stages];

      // Initialise all state to zero.
      double gain_factor = (double) ((int64_t) 1 << 32);
      for (int i = 0; i < cic_stages; i++) {
        d_integrator_state_re[i] = 0;
        d_integrator_state_im[i] = 0;
        d_comb_state_re[i] = 0;
        d_comb_state_im[i] = 0;
        gain_factor *= (double) int_factor;
      }
      d_gain_compensation = (float) ((double) int_factor / gain_factor);
    }

    /*
     * Our virtual destructor.
     */
    cic_interpolator_cc_impl::~cic_interpolator_cc_impl()
    {
      delete[] d_integrator_state_re;
      delete[] d_integrator_state_im;
      delete[] d_comb_state_re;
      delete[] d_comb_state_im;
    }

    int
    cic_interpolator_cc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      for (int i = 0; i < noutput_items / d_int_factor; i++) {

        // The input must be between -1 to +1 for both the real and
        // imaginary parts, so we saturate here to guarantee that.
        gr_complex input = in[i];
        int64_t int_val_re =
          (input.real() > 1.0f) ? ((int64_t) 1 << 32) :
          (input.real() < -1.0f) ? ((int64_t) -1 << 32) :
          (int64_t) (input.real() * (float) ((int64_t) 1 << 32));
        int64_t int_val_im =
          (input.imag() > 1.0f) ? ((int64_t) 1 << 32) :
          (input.imag() < -1.0f) ? ((int64_t) -1 << 32) :
          (int64_t) (input.imag() * (float) ((int64_t) 1 << 32));

        // Implement the cascaded comb stages at the low sample rate.
        for (int j = 0; j < d_cic_stages; j++) {
          int64_t comb_val_re = int_val_re - d_comb_state_re[j];
          int64_t comb_val_im = int_val_im - d_comb_state_im[j];
          d_comb_state_re[j] = int_val_re;
          d_comb_state_im[j] = int_val_im;
          int_val_re = comb_val_re;
          int_val_im = comb_val_im;
        }

        // Implement the cascaded integrator stages at the high sample
        // rate, with zero stuffing after the initial sample value.
        for (int j = 0; j < d_int_factor; j++) {
          if (j != 0) {
            int_val_re = 0.0;
            int_val_im = 0.0;
          }
          for (int k = 0; k < d_cic_stages; k++) {
            int_val_re += d_integrator_state_re[k];
            int_val_im += d_integrator_state_im[k];
            d_integrator_state_re[k] = int_val_re;
            d_integrator_state_im[k] = int_val_im;
          }

          // Convert output back to complex floating point notation.
          out[i*d_int_factor+j] = gr_complex (
            (float) int_val_re * d_gain_compensation,
            (float) int_val_im * d_gain_compensation
          );
        }
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

