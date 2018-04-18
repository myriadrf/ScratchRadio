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


#ifndef INCLUDED_SCRATCH_RADIO_MANC_ENC_H
#define INCLUDED_SCRATCH_RADIO_MANC_ENC_H

#include <scratch_radio/api.h>
#include <gnuradio/sync_interpolator.h>

namespace gr {
  namespace scratch_radio {

    /*!
     * \brief <+description of block+>
     * \ingroup scratch_radio
     *
     */
    class SCRATCH_RADIO_API manc_enc : virtual public gr::sync_interpolator
    {
     public:
      typedef boost::shared_ptr<manc_enc> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of scratch_radio::manc_enc.
       *
       * To avoid accidental use of raw pointers, scratch_radio::manc_enc's
       * constructor is in a private implementation
       * class. scratch_radio::manc_enc::make is the public interface for
       * creating new instances.
       */
      static sptr make(bool invert);
    };

  } // namespace scratch_radio
} // namespace gr

#endif /* INCLUDED_SCRATCH_RADIO_MANC_ENC_H */

