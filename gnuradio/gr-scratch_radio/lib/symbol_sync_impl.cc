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
#include "symbol_sync_impl.h"

namespace gr {
  namespace scratch_radio {

    symbol_sync::sptr
    symbol_sync::make(int baud_rate, int sample_rate)
    {
      return gnuradio::get_initial_sptr
        (new symbol_sync_impl(baud_rate, sample_rate));
    }

    /*
     * The private constructor
     */
    symbol_sync_impl::symbol_sync_impl(int baud_rate, int sample_rate)
      : gr::block("symbol_sync",
              gr::io_signature::make(1, 1, sizeof(float)),
              gr::io_signature::make(1, 1, sizeof(uint8_t)))
    {
      d_baud_rate = baud_rate;
      d_sample_rate = sample_rate;
      d_sample_ratio = 1 + sample_rate / baud_rate;
      d_nco_count = sample_rate;
      d_symbol_req = true;
      set_history(2);
    }

    /*
     * Our virtual destructor.
     */
    symbol_sync_impl::~symbol_sync_impl()
    {
    }

    void
    symbol_sync_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = noutput_items * d_sample_ratio;
    }

    int
    symbol_sync_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const float *in = (const float *) input_items[0];
      uint8_t *out = (uint8_t *) output_items[0];
      int in_i = 0;
      int out_i = 0;

      while ((in_i < ninput_items[0] - 1) && (out_i < noutput_items)) {

        // Detect zero crossings when successive samples have a
        // negative product.
        float last_sample = in[in_i++];
        float this_sample = in[in_i];
        if (this_sample * last_sample <= 0) {
          d_nco_count = d_baud_rate / 2;
          d_symbol_req = true;
        } else {
          d_nco_count = d_nco_count + d_baud_rate;
        }

        // Sample data at half the symbol period after detecting a
        // zero crossing and full symbol periods thereafter.
        if (d_nco_count >= d_sample_rate) {
          d_nco_count -= d_sample_rate;
          d_symbol_req = true;
        } else if (d_symbol_req && (d_nco_count >= d_sample_rate / 2)) {
          out[out_i++] = (this_sample < 0) ? 0 : 1;
          d_symbol_req = false;
        }
      }

      // Tell runtime system how many input items we consumed on
      // each input stream.
      consume_each (in_i);

      // Tell runtime system how many output items we produced.
      return out_i;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

