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

#ifndef INCLUDED_SCRATCH_RADIO_SIMPLE_DEFRAMER_IMPL_H
#define INCLUDED_SCRATCH_RADIO_SIMPLE_DEFRAMER_IMPL_H

#include <scratch_radio/simple_deframer.h>

namespace gr {
  namespace scratch_radio {

    class simple_deframer_impl : public simple_deframer
    {
     private:
      bool d_idle;
      bool d_msg_received;
      uint32_t d_header;
      int d_msg_byte_count;
      int d_msg_length;
      uint8_t d_msg_buffer[256];
      uint32_t d_checksum_0;
      uint32_t d_checksum_1;
      int d_idle_count;

      uint8_t m_get_data_byte (const uint8_t* in, int offset);
      void m_update_checksum (uint8_t byte_data);

     public:
      simple_deframer_impl();
      ~simple_deframer_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_SIMPLE_DEFRAMER_IMPL_H */

