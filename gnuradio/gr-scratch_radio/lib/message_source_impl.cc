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
#include "message_source_impl.h"

namespace gr {
  namespace scratch_radio {

    message_source::sptr
    message_source::make(char* msg_file_name, int msg_cps_rate)
    {
      return gnuradio::get_initial_sptr
        (new message_source_impl(msg_file_name, msg_cps_rate));
    }

    /*
     * The private constructor
     */
    message_source_impl::message_source_impl(char* msg_file_name, int msg_cps_rate)
      : gr::sync_block("message_source",
              gr::io_signature::make(0, 0, 0),
              gr::io_signature::make(1, 1, sizeof(uint8_t)))
    {
      d_msg_ready = false;
      d_msg_overflow = false;
      d_msg_byte_count = 0;
      d_msg_length = 0;
      d_source = new std::ifstream(msg_file_name);
      if ((!d_source) || (!d_source->is_open ())) {
        // TODO: How do we handle missing files?
      }
      d_msg_buffer = new uint8_t [MSG_BUFFER_LEN];

      // Determine the output buffer threshold required to limit the
      // latency imposed by the output buffer.
      int max_buf_size = 4096 * (1 + msg_cps_rate / 4096);
      set_max_output_buffer(max_buf_size);
      set_max_noutput_items(msg_cps_rate);
    }

    /*
     * Our virtual destructor.
     */
    message_source_impl::~message_source_impl()
    {
      if (d_source) {
        if (d_source->is_open()) {
          d_source->close();
        }
        delete d_source;
        delete[] d_msg_buffer;
      }
    }

    bool
    message_source_impl::m_poll_for_message()
    {
      bool msg_valid = false;
      if ((d_source) && (d_source->is_open())) {
        while ((!msg_valid) && (d_source->rdbuf()->in_avail())) {
          uint8_t next_byte = (uint8_t) d_source->get();
          if (next_byte == '\n') {
            d_msg_buffer[d_msg_byte_count] = 0;
            msg_valid = !d_msg_overflow;
            d_msg_ready = !d_msg_overflow;
            d_msg_overflow = false;
            d_msg_length = d_msg_byte_count;
            d_msg_byte_count = 0;
          }
          else if (d_msg_byte_count < MAX_MESSAGE_SIZE) {
            d_msg_buffer[d_msg_byte_count++] = next_byte;
          }
          else {
            d_msg_overflow = true;
          }
        }
      }
      return msg_valid;
    }

    int
    message_source_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      uint8_t *out = (uint8_t *) output_items[0];
      int out_i = 0;

      // If waiting, poll for next input message once per work cycle.
      // If no message is available, pad the output with idle bytes.
      if ((!d_msg_ready) && (noutput_items > 0)) {
        d_msg_ready = m_poll_for_message();
        if (d_msg_ready) {
          out[out_i++] = d_msg_length;
        }
        else {
          while (out_i < noutput_items) {
            out[out_i++] = 0x00;
          }
        }
      }

      // Copy over the message contents.
      while ((d_msg_ready) && (out_i < noutput_items)) {
        if (d_msg_byte_count == d_msg_length) {
          d_msg_ready = false;
          d_msg_overflow = false;
          d_msg_byte_count = 0;
          d_msg_length = 0;
        } else {
          out[out_i++] = d_msg_buffer[d_msg_byte_count++];
        }
      }

      // Tell runtime system how many output items we produced.
      return out_i;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

