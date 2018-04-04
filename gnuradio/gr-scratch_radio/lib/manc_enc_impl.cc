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
#include "manc_enc_impl.h"

namespace gr {
  namespace scratch_radio {

    manc_enc::sptr
    manc_enc::make(bool invert)
    {
      return gnuradio::get_initial_sptr
        (new manc_enc_impl(invert));
    }

    /*
     * The private constructor
     */
    manc_enc_impl::manc_enc_impl(bool invert)
      : gr::sync_interpolator("manc_enc",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(uint8_t)), 2)
    {
      d_invert = invert;
    }

    /*
     * Our virtual destructor.
     */
    manc_enc_impl::~manc_enc_impl()
    {
    }

    int
    manc_enc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      // Specify buffer data types.
      const uint8_t* in = (const uint8_t*) input_items[0];
      uint8_t* out = (uint8_t*) output_items[0];
      int i;

      for (i = 0; i < noutput_items/2; i++) {

        // Insert idle bits if required.
        if (in[i] == 0xFF) {
          out[2*i]   = 0xFF;
          out[2*i+1] = 0xFF;
        }

        // Default is to encode '1' as a rising edge.
        else if (!d_invert) {
          if (in[i] > 0) {
            out[2*i]   = 0;
            out[2*i+1] = 1;
          }
          else {
            out[2*i]   = 1;
            out[2*i+1] = 0;
          }
        }

        // Inverted version encodes '1' as a falling edge.
        else {
          if (in[i] > 0) {
            out[2*i]   = 1;
            out[2*i+1] = 0;
          }
          else {
            out[2*i]   = 0;
            out[2*i+1] = 1;
          }
        }
      }

      // Tell runtime system how many output items we produced.
      return 2 * i;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

