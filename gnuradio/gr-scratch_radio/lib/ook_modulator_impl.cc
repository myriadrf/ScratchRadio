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

#include <ctime>
#include <cmath>
#include <gnuradio/io_signature.h>
#include <gnuradio/gr_complex.h>
#include "ook_modulator_impl.h"

namespace gr {
  namespace scratch_radio {

    ook_modulator::sptr
    ook_modulator::make(int baud_rate, int sample_rate, int mod_freq)
    {
      return gnuradio::get_initial_sptr
        (new ook_modulator_impl(baud_rate, sample_rate, mod_freq));
    }

    /*
     * The private constructor
     */
    ook_modulator_impl::ook_modulator_impl(int baud_rate, int sample_rate, int mod_freq)
      : gr::block("ook_modulator",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(gr_complex)))
    {
      d_sample_rate = sample_rate;
      d_sample_count = 0;
      d_current_symbol = 0;
      d_timestamp = 0;
      d_first_call = true;

      // Build the table of modulated symbol samples.
      d_symbol_length = sample_rate / baud_rate;
      d_sample_table = new gr_complex [d_symbol_length];
      double mod_factor = double (mod_freq) * 2 * 3.141592653589793 / double (sample_rate);
      for (int i = 0; i < d_symbol_length; i++) {
        double theta = i * mod_factor;
        d_sample_table[i] = gr_complex (float (sin (theta)) / 2, - float (cos (theta)) / 2);
      }
    }

    /*
     * Our virtual destructor.
     */
    ook_modulator_impl::~ook_modulator_impl()
    {
      delete[] d_sample_table;
    }

    void
    ook_modulator_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = noutput_items * d_symbol_length;
    }

    int
    ook_modulator_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      struct timespec ts_now;
      const uint8_t *in = (const uint8_t *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];
      int in_i = 0;
      int out_i = 0;

      // Perform basic output rate limiting to prevent transmit buffer
      // bloat. This approach should be replaced by proper output buffer
      // latency management when possible. Stalls on idle cycles only.
      if (d_first_call) {
        d_first_call = false;
        clock_gettime (CLOCK_MONOTONIC, &ts_now);
        d_timestamp = (int64_t) ts_now.tv_sec * 1000000000 + ts_now.tv_nsec;
      }
      if (in[0] == 0xFF) {
        int64_t now;
        clock_gettime (CLOCK_MONOTONIC, &ts_now);
        now = (int64_t) ts_now.tv_sec * 1000000000 + ts_now.tv_nsec;
        if ((d_timestamp - now) > (OUTPUT_LATENCY * 1000000)) {
          consume_each (1);
          return 0;
        }
      }

      while ((in_i < ninput_items[0]) && (out_i < noutput_items)) {

        // Modulate current symbol value to IF.
        if (d_current_symbol != 0) {
          out[out_i++] = d_sample_table[d_sample_count];
        } else {
          out[out_i++] = gr_complex (0.0, 0.0);
        }

        // Get next symbol value.
        d_sample_count += 1;
        if (d_sample_count >= d_symbol_length) {
          d_current_symbol = (in[in_i++] == 1) ? 1 : 0;
          d_sample_count = 0;
        }
      }

      // Update timestamp based on number of samples generated.
      d_timestamp += ((int64_t) out_i * 1000000000 / d_sample_rate);

      // Tell runtime system how many input items we consumed on
      // each input stream.
      consume_each (in_i);

      // Tell runtime system how many output items we produced.
      return out_i;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

