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
#include "simple_framer_impl.h"

static const uint8_t c_header[HEADER_LEN] = HEADER_BYTES;

namespace gr {
  namespace scratch_radio {

    simple_framer::sptr
    simple_framer::make()
    {
      return gnuradio::get_initial_sptr
        (new simple_framer_impl());
    }

    /*
     * The private constructor
     */
    simple_framer_impl::simple_framer_impl()
      : gr::block("simple_framer",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(1, 1, sizeof(uint8_t)))
    {
      d_idle = true;
      d_header_index = 0;
      d_byte_count = 0;
      d_checksum_0 = 0;
      d_checksum_1 = 0;
      d_idle_count = 0;
      set_max_output_buffer(4096);
      set_max_noutput_items(256);
      set_output_multiple(8);
    }

    /*
     * Our virtual destructor.
     */
    simple_framer_impl::~simple_framer_impl()
    {
    }

    void
    simple_framer_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
      ninput_items_required[0] = noutput_items / 8;
    }

    void
    simple_framer_impl::m_send_data_byte(uint8_t* out, int offset, uint8_t byte_data)
    {
      for (int i = 0; i < 8; i++) {
        out[offset+i] = byte_data & 1;
        byte_data >>= 1;
      }
    }

    void
    simple_framer_impl::m_send_idle_byte(uint8_t* out, int offset)
    {
      for (int i = 0; i < 8; i++) {
        out[offset+i] = 0xFF;
      }
    }

    void
    simple_framer_impl::m_update_checksum (uint8_t byte_data)
    {
      d_checksum_0 += byte_data;
      d_checksum_1 += d_checksum_0;
    }

    int
    simple_framer_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const uint8_t *in = (const uint8_t *) input_items[0];
      uint8_t *out = (uint8_t *) output_items[0];
      int in_i = 0;
      int out_i = 0;

      while ((in_i < ninput_items[0]) && (out_i <= noutput_items - 8)) {

        // Process out of frame idle flags until a size byte is
        // detected, in which case we start generating the header.
        // Note that each idle flag maps to a single idle bit which
        // means we have 1/8 of the latency in the input buffer when
        // processing idle cycles.
        if (d_idle) {
          uint8_t this_byte = in[in_i++];
          if (this_byte == 0x00) {
            if (d_idle_count == 0) {
              d_idle_count = IDLE_DOWNSAMPLE_RATE - 1;
              m_send_idle_byte (out, out_i);
              out_i += 8;
            } else {
              d_idle_count -= 1;
            }
          }
          else {
            d_idle = false;
            d_idle_count = 0;
            m_send_data_byte (out, out_i, c_header[0]);
            d_byte_count = this_byte;
            d_header_index = 1;
            out_i += 8;
          }
        }

        // Perform header insertion.
        else if (d_header_index < HEADER_LEN) {
          m_send_data_byte (out, out_i, c_header[d_header_index++]);
          out_i += 8;
        }

        // Add the length field.
        else if (d_header_index == HEADER_LEN) {
          m_send_data_byte (out, out_i, d_byte_count);
          d_checksum_0 = 0;
          d_checksum_1 = 0;
          m_update_checksum (d_byte_count);
          d_header_index += 1;
          out_i += 8;
        }

        // Transfer the payload data.
        else if (d_byte_count > 0) {
          uint8_t this_byte = in[in_i++];
          m_send_data_byte (out, out_i, this_byte);
          m_update_checksum (this_byte);
          d_byte_count -= 1;
          out_i += 8;
        }

        // Append the first checksum byte.
        else if (d_header_index == HEADER_LEN + 1) {
          m_send_data_byte (out, out_i, d_checksum_0 % 255);
          d_header_index += 1;
          out_i += 8;
        }

        // Append the second checksum byte.
        else if (d_header_index == HEADER_LEN + 2) {
          m_send_data_byte (out, out_i, d_checksum_1 % 255);
          d_header_index += 1;
          out_i += 8;
        }

        // Append the frame terminator byte.
        else if (d_header_index == HEADER_LEN + 3) {
          m_send_data_byte (out, out_i, FRAME_TERMINATOR);
          d_header_index += 1;
          out_i += 8;
        }

        // Insert idle byte at end of frame.
        else {
          m_send_idle_byte (out, out_i);
          d_idle = true;
          out_i += 8;
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

