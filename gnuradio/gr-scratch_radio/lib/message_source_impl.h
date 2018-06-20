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

#ifndef INCLUDED_SCRATCH_RADIO_MESSAGE_SOURCE_IMPL_H
#define INCLUDED_SCRATCH_RADIO_MESSAGE_SOURCE_IMPL_H

#include <fstream>
#include <scratch_radio/message_source.h>

#define MAX_MESSAGE_SIZE 255
#define MSG_BUFFER_LEN (MAX_MESSAGE_SIZE+1)

namespace gr {
  namespace scratch_radio {

    class message_source_impl : public message_source
    {
     private:
      bool d_msg_ready;
      bool d_msg_overflow;
      int d_msg_byte_count;
      int d_msg_length;
      std::ifstream* d_source;
      uint8_t d_msg_buffer[MSG_BUFFER_LEN];

      bool m_poll_for_message(void);

     public:
      message_source_impl(char* msg_file_name, int msg_cps_rate);
      ~message_source_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_MESSAGE_SOURCE_IMPL_H */

