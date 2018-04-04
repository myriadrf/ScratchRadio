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

#ifndef INCLUDED_SCRATCH_RADIO_OOK_DEMODULATOR_IMPL_H
#define INCLUDED_SCRATCH_RADIO_OOK_DEMODULATOR_IMPL_H

#include <scratch_radio/ook_demodulator.h>

namespace gr {
  namespace scratch_radio {

    class ook_demodulator_impl : public ook_demodulator
    {
     private:
      int d_symbol_avg_period;
      int d_offset_avg_period;
      float d_symbol_acc_value;
      float d_offset_acc_value;

     public:
      ook_demodulator_impl(int baud_rate, int sample_rate);
      ~ook_demodulator_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_OOK_DEMODULATOR_IMPL_H */

