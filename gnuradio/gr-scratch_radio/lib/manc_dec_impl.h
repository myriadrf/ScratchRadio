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

#ifndef INCLUDED_SCRATCH_RADIO_MANC_DEC_IMPL_H
#define INCLUDED_SCRATCH_RADIO_MANC_DEC_IMPL_H

#include <scratch_radio/manc_dec.h>

namespace gr {
  namespace scratch_radio {

    class manc_dec_impl : public manc_dec
    {
     private:
      bool d_invert;
      bool d_out_of_sync;
      bool d_do_decode;
      uint8_t d_start_bit;

     public:
      manc_dec_impl(bool invert);
      ~manc_dec_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_MANC_DEC_IMPL_H */

