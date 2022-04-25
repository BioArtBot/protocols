#!/usr/bin/env python
# coding: utf-8

"""Opentrons python protocol adapted from """

from opentrons import protocol_api

metadata = {
    "protocolName": "Paper Blot",
    "author": "YHK",
    "description": "Drying liquid on whatman paper/Membrane",
    'apiLevel': '2.11'}

def run(protocol: protocol_api.ProtocolContext):
    samples = protocol.load_labware('nest_12_reservoir_15ml', 2)
    membrane = protocol.load_labware('127x85_agar_plate1', 1)
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 6)


    p20 = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack])
    
    # loop to transfert solution from buffer to pellet with mixing

    for i in range(12):
        p20.pick_up_tip()
        source = samples.wells()[1]
        dest = membrane.wells()[8*i]
        p20.aspirate(1.5, source) 
        p20.touch_tip()
        p20.dispense(1.5, dest.top())
        p20.return_tip()