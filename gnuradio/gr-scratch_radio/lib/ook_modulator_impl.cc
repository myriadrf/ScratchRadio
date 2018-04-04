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
#include <gnuradio/gr_complex.h>
#include "ook_modulator_impl.h"

namespace gr {
  namespace scratch_radio {

    ook_modulator::sptr
    ook_modulator::make(int baud_rate, int sample_rate)
    {
      return gnuradio::get_initial_sptr
        (new ook_modulator_impl(baud_rate, sample_rate));
    }

    /*
     * The private constructor
     */
    ook_modulator_impl::ook_modulator_impl(int baud_rate, int sample_rate)
      : gr::block("ook_modulator",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(gr_complex)))
    {
      d_baud_rate = baud_rate;
      d_sample_rate = sample_rate;
      d_nco_count = sample_rate;
      d_current_sample = 0.0;
    }

    /*
     * Our virtual destructor.
     */
    ook_modulator_impl::~ook_modulator_impl()
    {
    }

    void
    ook_modulator_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = 1 + noutput_items * d_baud_rate / d_sample_rate;
    }

    int
    ook_modulator_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const uint8_t *in = (const uint8_t *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];
      int in_i = 0;
      int out_i = 0;

      while ((in_i < ninput_items[0]) && (out_i < noutput_items)) {
        int next_nco_count = d_nco_count + d_baud_rate;

        // Repeat current sample output for the symbol period.
        if (next_nco_count < d_sample_rate) {
          out[out_i++] = gr_complex (d_current_sample, 0.0);
        }

        // Linear interpolation between old and new sample values.
        else {
          float old_sample = d_current_sample;
          d_current_sample = (in[in_i++] == 1) ? 1.0 : 0.0;
          next_nco_count -= d_sample_rate;
          float interp_value = (d_current_sample * next_nco_count +
            old_sample * (d_baud_rate - next_nco_count)) / d_baud_rate;
          out[out_i++] = gr_complex (interp_value, 0.0);
        }
        d_nco_count = next_nco_count;
      }

      // Tell runtime system how many input items we consumed on
      // each input stream.
      consume_each (in_i);

      // Tell runtime system how many output items we produced.
      return out_i;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

