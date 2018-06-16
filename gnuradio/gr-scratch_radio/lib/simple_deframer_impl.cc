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
#include "simple_deframer_impl.h"

namespace gr {
  namespace scratch_radio {

    simple_deframer::sptr
    simple_deframer::make()
    {
      return gnuradio::get_initial_sptr
        (new simple_deframer_impl());
    }

    /*
     * The private constructor
     */
    simple_deframer_impl::simple_deframer_impl()
      : gr::block("simple_deframer",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(uint8_t)))
    {
      d_idle = true;
      d_msg_received = false;
      d_header = 0;
      d_msg_byte_count = 0;
      d_msg_length = 0;
      d_msg_buffer = new uint8_t [256];
      d_checksum_0 = 0;
      d_checksum_1 = 0;
      d_idle_count = 0;
      set_max_output_buffer(4096);
      set_max_noutput_items(256);
    }

    /*
     * Our virtual destructor.
     */
    simple_deframer_impl::~simple_deframer_impl()
    {
      delete[] d_msg_buffer;
    }

    void
    simple_deframer_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = noutput_items * 8;
    }

    uint8_t
    simple_deframer_impl::m_get_data_byte (const uint8_t* in, int offset)
    {
      uint8_t byte_shift = 0;
      for (int i = 0; i < 8; i++) {
        byte_shift >>= 1;
        if (in[offset+i] != 0)
          byte_shift |= 0x80;
      }
      return byte_shift;
    }

    void
    simple_deframer_impl::m_update_checksum (uint8_t byte_data)
    {
      d_checksum_0 += byte_data;
      d_checksum_1 += d_checksum_0;
    }

    int
    simple_deframer_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const uint8_t *in = (const uint8_t *) input_items[0];
      uint8_t *out = (uint8_t *) output_items[0];
      int in_i = 0;
      int out_i = 0;

      while ((in_i <= ninput_items[0] - 8) && (out_i < noutput_items)) {

        // If a valid message has been received, copy it from the
        // local buffer to the output.
        if (d_msg_received) {
          out[out_i++] = d_msg_buffer[d_msg_byte_count++];
          if (d_msg_byte_count == d_msg_length) {
            d_idle = true;
            d_idle_count = 0;
            d_msg_received = false;
            d_msg_length = 0;
          }
        }

        // In the idle state, search for the start of frame header.
        // Matches on the byte sequence 0x7E, 0x81, 0xC3, 0x3C.
        else if (d_idle) {
          if (in[in_i++] == 0) {
            if (d_header == 0x3CC3817E) {
              d_idle = false;
              d_header = 0;
            } else {
              d_header >>= 1;
            }
          } else {
            if (d_idle_count == 0) {
              out[out_i++] = 0x00;
              d_idle_count = 7;
            } else {
              d_idle_count -= 1;
            }
            d_header = 0x40000000 | (d_header >> 1);
          }
        }

        // Get the number of bytes in the frame.
        else if (d_msg_length == 0) {
          d_msg_byte_count = 0;
          d_msg_length = m_get_data_byte (in, in_i);
          in_i += 8;
          d_checksum_0 = 0;
          d_checksum_1 = 0;
          m_update_checksum (d_msg_length);
          if (d_msg_length == 0) {
            d_idle = true;
          }
        }

        // Read the specified number of bytes from the input
        else if (d_msg_byte_count < d_msg_length) {
          uint8_t input_data = m_get_data_byte (in, in_i);
          in_i += 8;
          d_msg_buffer[d_msg_byte_count] = input_data;
          d_msg_byte_count += 1;
          m_update_checksum (input_data);
        }

        // Validate first checksum byte.
        else if (d_msg_byte_count == d_msg_length) {
          uint8_t check_byte = m_get_data_byte (in, in_i);
          in_i += 8;
          if (check_byte == d_checksum_0 % 255) {
            d_msg_byte_count += 1;
          } else {
            d_idle = true;
            d_msg_length = 0;
          }
        }

        // Validate second checksum byte.
        else {
          uint8_t check_byte = m_get_data_byte (in, in_i);
          in_i += 8;
          if (check_byte == d_checksum_1 % 255) {
            out[out_i++] = d_msg_length;
            d_msg_received = true;
            d_msg_byte_count = 0;
          } else {
            d_idle = true;
            d_msg_length = 0;
          }
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

