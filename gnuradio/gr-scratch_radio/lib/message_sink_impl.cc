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
#include "message_sink_impl.h"

namespace gr {
  namespace scratch_radio {

    message_sink::sptr
    message_sink::make(char* msg_file_name)
    {
      return gnuradio::get_initial_sptr
        (new message_sink_impl(msg_file_name));
    }

    /*
     * The private constructor
     */
    message_sink_impl::message_sink_impl(char* msg_file_name)
      : gr::sync_block("message_sink",
              gr::io_signature::make(1, 1, sizeof(uint8_t)),
              gr::io_signature::make(0, 0, 0))
    {
      d_msg_byte_count = 0;
      d_sink = new std::ofstream(msg_file_name);
      if ((!d_sink) || (!d_sink->is_open ())) {
        // TODO: How do we handle missing files?
      }
    }

    /*
     * Our virtual destructor.
     */
    message_sink_impl::~message_sink_impl()
    {
      if (d_sink) {
        if (d_sink->is_open()) {
          d_sink->close();
        }
        delete d_sink;
      }
    }

    int
    message_sink_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const uint8_t *in = (const uint8_t *) input_items[0];

      for (int in_i = 0; in_i < noutput_items; in_i++) {
        uint8_t next_char = in[in_i];

        // Search for start of next message.
        if (d_msg_byte_count == 0) {
          d_msg_byte_count = next_char;
        }

        // Copy message to output stream.
        else {
          d_sink->put(next_char);
          d_msg_byte_count -= 1;
          if (d_msg_byte_count == 0) {
            d_sink->put('\n');
            d_sink->flush();
          }
        }
      }

      // Tell runtime system how many input items we consumed.
      return noutput_items;
    }

  } /* namespace scratch_radio */
} /* namespace gr */

