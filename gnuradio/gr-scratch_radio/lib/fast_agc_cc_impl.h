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

#ifndef INCLUDED_SCRATCH_RADIO_FAST_AGC_CC_IMPL_H
#define INCLUDED_SCRATCH_RADIO_FAST_AGC_CC_IMPL_H

#include <scratch_radio/fast_agc_cc.h>

namespace gr {
  namespace scratch_radio {

    class fast_agc_cc_impl : public fast_agc_cc
    {
     private:
      float d_rate;
      float d_reference;
      float d_gain;
      float d_max_gain;

     public:
      fast_agc_cc_impl(float rate, float reference, float gain, float max_gain);
      ~fast_agc_cc_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_FAST_AGC_CC_IMPL_H */

