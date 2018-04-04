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

#ifndef INCLUDED_SCRATCH_RADIO_SIMPLE_FRAMER_IMPL_H
#define INCLUDED_SCRATCH_RADIO_SIMPLE_FRAMER_IMPL_H

#include <scratch_radio/simple_framer.h>

#define HEADER_LEN 10
#define HEADER_BYTES \
  {0xA5, 0xF0, 0xA5, 0xF0, 0xA5, 0xF0, 0x7E, 0x81, 0xC3, 0x3C}
#define FRAME_TERMINATOR 0xFF

#define IDLE_DOWNSAMPLE_RATE 10

namespace gr {
  namespace scratch_radio {

    class simple_framer_impl : public simple_framer
    {
     private:
      bool d_idle;
      int d_header_index;
      int d_byte_count;
      uint32_t d_checksum_0;
      uint32_t d_checksum_1;
      int d_idle_count;

      void m_send_data_byte (uint8_t* out, int offset, uint8_t byteData);
      void m_send_idle_byte (uint8_t* out, int offset);
      void m_update_checksum (uint8_t byte_data);

     public:
      simple_framer_impl();
      ~simple_framer_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_SIMPLE_FRAMER_IMPL_H */

