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

#ifndef INCLUDED_SCRATCH_RADIO_OOK_MODULATOR_IMPL_H
#define INCLUDED_SCRATCH_RADIO_OOK_MODULATOR_IMPL_H

#include <scratch_radio/ook_modulator.h>

#define OUTPUT_LATENCY 250

namespace gr {
  namespace scratch_radio {

    class ook_modulator_impl : public ook_modulator
    {
     private:
      int d_sample_rate;
      int d_sample_count;
      int d_current_symbol;
      int64_t d_timestamp;
      bool d_first_call;
      int d_symbol_length;
      gr_complex* d_sample_table;

     public:
      ook_modulator_impl(int baud_rate, int sample_rate, int mod_freq);
      ~ook_modulator_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_OOK_MODULATOR_IMPL_H */

