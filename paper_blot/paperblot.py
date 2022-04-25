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
    samples = protocol.load_labware('nest_96_wellplate_2ml_deep', 2)
    membrane = protocol.load_labware('nest_96_wellplate_2ml_deep', 1)
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', 6)


    p300 = protocol.load_instrument('p300_multi_gen2', 'right', tip_racks=[tiprack])
    
    # loop to transfert solution from buffer to pellet with mixing

    for i in range(12):
        p300.pick_up_tip()
        source = samples.columns()[i]
        dest = membrane.wells()[8*i]
        p300.transfer(2, source, dest.top(), new_tip = 'never')
        p300.return_tip()

 