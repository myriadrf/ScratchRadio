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
#include "manc_dec_impl.h"

namespace gr {
  namespace scratch_radio {

    manc_dec::sptr
    manc_dec::make(bool invert)
    {
      return gnuradio::get_initial_sptr
        (new manc_dec_impl(invert));
    }

    /*
     * The private constructor
     */
    manc_dec_impl::manc_dec_impl(bool invert)
      : gr::block("manc_dec",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(uint8_t)))
    {
      d_invert = invert;
      d_out_of_sync = true;
      d_do_decode = true;
      d_start_bit = 0xFF;
    }

    /*
     * Our virtual destructor.
     */
    manc_dec_impl::~manc_dec_impl()
    {
    }

    void
    manc_dec_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = noutput_items * 2;
    }

    int
    manc_dec_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const uint8_t *in = (const uint8_t *) input_items[0];
      uint8_t *out = (uint8_t *) output_items[0];
      int in_i = 0;
      int out_i = 0;

      while ((in_i < ninput_items[0]) && (out_i < noutput_items)) {
        uint8_t input_bit = in[in_i];
        in_i += 1;

        // If the decoder is out of sync, search for a transition.
        if (d_out_of_sync) {
          if (d_start_bit == 0xFF) {
            d_start_bit = input_bit;
          }
          else if (d_start_bit != input_bit) {
            d_out_of_sync = false;
            d_do_decode = false;
          }
        }

        // Store the first bit of each coding pair.
        else if (!d_do_decode) {
          d_do_decode = true;
          d_start_bit = input_bit;
        }

        // Slip the decoder on invalid bit pairs.
        else if (d_start_bit == input_bit) {
          d_out_of_sync = true;
          d_start_bit = 0xFF;
        }

        // Store the decoded bit to the output buffer. Default is to
        // decode a rising edge as '1'.
        else {
          if (!d_invert)
            out[out_i] = input_bit;
          else
            out[out_i] = d_start_bit;
          d_do_decode = false;
          out_i += 1;
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
