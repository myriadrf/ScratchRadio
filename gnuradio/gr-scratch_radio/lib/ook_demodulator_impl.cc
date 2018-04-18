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
#include "ook_demodulator_impl.h"

namespace gr {
  namespace scratch_radio {

    ook_demodulator::sptr
    ook_demodulator::make(int baud_rate, int sample_rate)
    {
      return gnuradio::get_initial_sptr
        (new ook_demodulator_impl(baud_rate, sample_rate));
    }

    /*
     * The private constructor
     */
    ook_demodulator_impl::ook_demodulator_impl(int baud_rate, int sample_rate)
      : gr::sync_block("ook_demodulator",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(float)))
    {
      d_symbol_avg_period = (3*sample_rate) / (4*baud_rate);
      d_offset_avg_period = d_symbol_avg_period * 10;
      d_symbol_acc_value = 0.0;
      d_offset_acc_value = 0.0;
      set_history(d_symbol_avg_period + d_offset_avg_period + 1);
    }

    /*
     * Our virtual destructor.
     */
    ook_demodulator_impl::~ook_demodulator_impl()
    {
    }

    int
    ook_demodulator_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      float *out = (float *) output_items[0];

      for (int i = 0; i < noutput_items; i++) {
        int old_offset_i = i;
        int old_sample_i = old_offset_i + d_offset_avg_period;
        int new_sample_i = old_sample_i + d_symbol_avg_period;

        float abs_input_sample = abs(in[new_sample_i]);
        float abs_old_symbol_sample = abs(in[old_sample_i]);
        float abs_old_offset_sample = abs(in[old_offset_i]);

        d_symbol_acc_value += abs_input_sample - abs_old_symbol_sample;
        d_offset_acc_value += abs_old_symbol_sample - abs_old_offset_sample;

        float symbol_value = d_symbol_acc_value / d_symbol_avg_period;
        symbol_value -= d_offset_acc_value / d_offset_avg_period;
        out[i] = symbol_value;
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

