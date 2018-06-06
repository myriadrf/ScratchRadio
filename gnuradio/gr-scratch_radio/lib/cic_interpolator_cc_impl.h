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

#ifndef INCLUDED_SCRATCH_RADIO_CIC_INTERPOLATOR_CC_IMPL_H
#define INCLUDED_SCRATCH_RADIO_CIC_INTERPOLATOR_CC_IMPL_H

#include <scratch_radio/cic_interpolator_cc.h>

namespace gr {
  namespace scratch_radio {

    class cic_interpolator_cc_impl : public cic_interpolator_cc
    {
     private:
      int      d_int_factor;
      int      d_cic_stages;
      int64_t* d_integrator_state_re;
      int64_t* d_integrator_state_im;
      int64_t* d_comb_state_re;
      int64_t* d_comb_state_im;
      float    d_gain_compensation;

     public:
      cic_interpolator_cc_impl(int int_factor, int cic_stages);
      ~cic_interpolator_cc_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_CIC_INTERPOLATOR_CC_IMPL_H */

