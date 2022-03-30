from ctypes import c_buffer
import json
import logging
import os
from socket import CAN_BCM_STARTTIMER
from subprocess import list2cmdline
from typing import Protocol, Tuple

import rdflib as rdfl
import sbol3
import tyto
from sbol3 import Document

import paml


#struggle with sourcewell & ggbuildwells definitions // verify issue with importing sbol3 & others // add new file for PAML gg protocol


logger: logging.Logger = logging.Logger("golden_gate_protocol")

CONT_NS = rdfl.Namespace('https://sift.net/container-ontology/container-ontology#')
OM_NS = rdfl.Namespace('http://www.ontology-of-units-of-measure.org/resource/om-2/')


#############################################
# set up the document
print('Setting up document')

def prepare_document() -> Document:
    logger.info('Setting up document')
    doc = sbol3.Document()
    sbol3.set_namespace('https://bbn.com/scratch/')

    return doc


#############################################
# Import the primitive libraries

def import_paml_libraries() -> None:
    logger.info('Importing libraries')
    paml.import_library('liquid_handling')
    logger.info('... Imported liquid handling')
    paml.import_library('plate_handling')
    logger.info('... Imported plate handling')
    paml.import_library('spectrophotometry')
    logger.info('... Imported spectrophotometry')
    paml.import_library('sample_arrays')
    logger.info('... Imported sample arrays')


DOCSTRING = \
    '''
This is the pilot study of the golden gate MOCLO protocol used in the CRI laboratories to test the assembly both manually and 
automatically using an opentrons machine. This one-pot reaction steps are the following:

- Use BsaI enzyme to cut selected DNA sequences from different MOCLO parts (promoter, RBS, GFP, terminator, plasmid backbone)
- use ligase to assemble parts into desired plasmid 
- incubate in thermocycler
- transform final product in new competent cells (the ones used for the current protocol were e.coli dh5alpha strains)

Protocols used as reference in the developement of this product

- https://www.protocols.io/view/golden-gate-lvl-0-b2k4qcyw
- https://github.com/LuHesketh/protocols/blob/main/golden_gate_moclo/golden_gate_moclo.py
- https://cafgroup.lbl.gov/protocols/general-molecular-biology/chemically-competent

'''
#############################################
# Create the protocol
print('Creating protocol')
def create_protocol() -> paml.Protocol:
    logger.info('Creating protocol')
    protocol: paml.Protocol = paml.Protocol('golden_gate_protocol')
    protocol.name = "golden_gate_protocol"
    protocol.description = DOCSTRING
    return protocol



#  materials to be provisioned 

"""                
 Materials:

PLASMID BACKBONE CDS (Kanamycin resistent)
PROMOTER+RBS CDS (chlorophenicol resistent)
GFP CDS (chlorophenicol resistent)
TERMINATOR CDS (chlorophenicol resistent)
bsal enzyme
enzyme ligase
T4_buffer_NEb
PURE WATER

"""

protocol = create_protocol()

#create the selected materias in PAML form

def create_PlasmidBackbone() -> sbol3.Component:
    plasmid_backbone = sbol3.Component('plasmid_backbone','https://github.com/BioArtBot/protocols/plasmid')
    plasmid_backbone.name = 'BIOBRICK, plasmid backbone DNA sequence, kanamicyn resistent'   
    return plasmid_backbone

def create_promoterandrbs() -> sbol3.Component:
    promoter_and_rbs = sbol3.Component('promorbs','https://github.com/BioArtBot/protocols/promorbs')
    promoter_and_rbs.name = 'BIOBRICK, promoter and rbs DNA sequence, chlorophenicol resistent'   
    return promoter_and_rbs

def create_GREEN_FLOURESCENT_PROTEIN() -> sbol3.Component:
  GFP = sbol3.Component('GFP','https://github.com/BioArtBot/protocols/GFP')
  GFP.name = 'BIOBRICK, GFP DNA sequence, chlorophenicol resistent'   
  return GFP

def create_terminator() -> sbol3.Component:
    terminator = sbol3.Component('terminator','https://github.com/BioArtBot/protocols/terminator')
    terminator.name = 'BIOBRICK, sequence terminator DNA sequence, chlorophenicol resistent'   
    return terminator

def create_bsaI() -> sbol3.Component:
    bsaI = sbol3.Component('enzyme_bsaI','https://github.com/BioArtBot/protocols/bsaI')
    bsaI.name = 'enzyme, will cut plasmid DNA in selected parts, bsaI'   
    return bsaI

def create_bufferT4() -> sbol3.Component:
    buffer = sbol3.Component('enzyme_buffer_T4','https://github.com/BioArtBot/protocols/buffer')
    buffer.name = 'buffer_T4, enzyme ligase, NEB'   
    return buffer

def create_ligase() -> sbol3.Component:
    ligase = sbol3.Component('enzyme_ligase','https://github.com/BioArtBot/protocols/ligase')
    ligase.name = 'enzyme, bind sequences, needs buffer T4, ligase'   
    return ligase

def create_purewater() -> sbol3.Component:
    water = sbol3.Component('uater','https://github.com/BioArtBot/protocols/water')
    water.name = 'pure water, fills up to 10 ul'   
    return water

# settle parameters for fuction definitions
doc = prepare_document()


# add an parameters for specifying the layout of the DNA source plate and build plate
PLATE_SPECIFICATION = \
    """ 
 cont:Corning 96 Well Plate 360 µL Flat and
 (cont:wellVolume some 
    ((om:hasUnit value om:microlitre) and
     (om:hasNumericalValue only xsd:decimal[>= "360"^^xsd:decimal])))"""


def create_plate(protocol: paml.Protocol):
   spec = paml.ContainerSpec(queryString=PLATE_SPECIFICATION, prefixMap=PREFIX_MAP, name='plateRequirement')
   plate = protocol.primitive_step('EmptyContainer',
                                    specification=spec)
   plate.name = 'Golden_Gate_plate'
   return plate

PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


# add coordinates of each component in the plate using the provision and plate coordinates primitives

def provision_PlasmidBackbone(protocol: paml.Protocol, plate, plasmidbackbone):
    c_plasmid_backbone = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:B1')
    protocol.primitive_step('Provision', resource=plasmidbackbone, destination=c_plasmid_backbone.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_plasmid_backbone

def provision_promoterandrbs(protocol: paml.Protocol, plate, promoter_and_rbs):
    c_promorbs = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='C1:D1')
    protocol.primitive_step('Provision', resource=promoter_and_rbs, destination=c_promorbs.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_promorbs 

def provision_GREEN_FLOURESCENT_PROTEIN(protocol: paml.Protocol, plate, GFP):
    c_GFP = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='E1:F1')
    protocol.primitive_step('Provision', resource=GFP, destination=c_GFP.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_GFP

def provision_terminator(protocol: paml.Protocol, plate, terminator):
    c_terminator = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='G1:H1')
    protocol.primitive_step('Provision', resource=terminator, destination=c_terminator.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_terminator

def provision_bsaI(protocol: paml.Protocol, plate, bsaI):
    c_bsaI = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A2:B2')
    protocol.primitive_step('Provision', resource=bsaI, destination=c_bsaI.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_bsaI

def provision_bufferT4(protocol: paml.Protocol, plate, buffer):
    c_buffer = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='C2:D2')
    protocol.primitive_step('Provision', resource=buffer, destination=c_buffer.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_buffer

def provision_ligase(protocol: paml.Protocol, plate, ligase):
    c_ligase = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='E2:F2')
    protocol.primitive_step('Provision', resource=ligase, destination=c_ligase.output_pin('samples'),
                            amount=sbol3.Measure(5, tyto.OM.microliter))
    return c_ligase

def provision_water(protocol: paml.Protocol, plate, water):
    c_water = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='G2:H2')
    protocol.primitive_step('Provision', resource=water, destination=c_water.output_pin('samples'),
                            amount=sbol3.Measure(10, tyto.OM.microliter))
    return c_water

# define the functions for assemblying the materials from the soource wells to the build wells

def assemble_buffer_and_water(protocol:paml.Protocol,c_buffer,c_water,goldengate_build_wells) -> None:
   
    protocol.primitive_step('TransferInto', source=c_buffer, destination=goldengate_build_wells.output_pin('samples'), 
    amount=sbol3.Measure(2, tyto.OM.microliter), dispenseVelocity=sbol3.OM_MEASURE(20, tyto.OM.minute)) 

    protocol.primitive_step('TransferInto', source=c_water, destination=goldengate_build_wells.output_pin('samples'), 
    amount=sbol3.Measure(4, tyto.OM.microliter), dispenseVelocity=sbol3.OM_MEASURE(20, tyto.OM.minute)) 

def assemble_components(protocol, component, goldengate_build_wells):
    protocol.primitive_step('TransferInto', source=component, destination=goldengate_build_wells.output_pin('samples'), 
    amount=sbol3.Measure(1, tyto.OM.microliter), dispenseVelocity=sbol3.OM_MEASURE(20, tyto.OM.minute)) 

# after this step  the liquid handling part is over. The next procedure will be incubation on a thermocycler followed by trnasformation

#############################################
 # set up the document
def golden_gate_protocol() -> Tuple[paml.Protocol, Document]:
    
    doc: Document = prepare_document()

#############################################
# Import the primitive libraries
    import_paml_libraries()

    
#############################################
# Create the protocol
    protocol: paml.Protocol = create_protocol()
    doc.add(protocol)

# create the materials to be provisione
    plasmid_backbone = create_PlasmidBackbone()
    doc.add(plasmid_backbone)

    promoter_and_rbs = create_promoterandrbs()
    doc.add(promoter_and_rbs)

    GFP = create_GREEN_FLOURESCENT_PROTEIN()
    doc.add(GFP)

    terminator = create_terminator()
    doc.add(terminator)

    bsaI = create_bsaI()
    doc.add(bsaI)

    buffer = create_bufferT4()
    doc.add(buffer)

    ligase = create_ligase()
    doc.add(ligase)

    water = create_purewater()
    doc.add(water)

# actual steps of the protocol (liquid handling part)
#get a plate

    plate = create_plate(protocol)

# put DNA into the selected wells following the build plan

    provision_PlasmidBackbone(protocol, plate, plasmid_backbone)

    provision_promoterandrbs(protocol, plate, promoter_and_rbs)

    provision_GREEN_FLOURESCENT_PROTEIN(protocol, plate, GFP)

    provision_terminator(protocol, plate, terminator)

    provision_bsaI(protocol, plate, bsaI)

    provision_bufferT4(protocol, plate, buffer)

    provision_ligase(protocol, plate, ligase)

    provision_water(protocol, plate, water)


     # list the materials for transfer function

    c_plasmid_backbone = provision_PlasmidBackbone(protocol, plate, plasmid_backbone) 
    c_promorbs = provision_promoterandrbs(protocol, plate, promoter_and_rbs)
    c_GFP = provision_GREEN_FLOURESCENT_PROTEIN(protocol, plate, GFP)
    c_terminator = provision_terminator(protocol, plate, terminator)
    c_bsaI = provision_bsaI(protocol, plate, bsaI)
    c_buffer = provision_bufferT4(protocol, plate, buffer)
    c_ligase = provision_ligase(protocol, plate, ligase)
    c_water = provision_water(protocol, plate, water)
    
   
# define the wells where you will be doing the GG assembly  
    goldengate_build_wells = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A3:B3')


# assemble DNA in build wells
    components: list = [c_plasmid_backbone,c_promorbs, c_GFP,c_terminator,c_bsaI,c_buffer, c_ligase, c_water]
    for component in components:
        assemble_components(protocol, component, goldengate_build_wells)

    assemble_buffer_and_water(protocol,c_buffer,c_water,goldengate_build_wells)

# 

# Finish liquid handling protocol

    output = protocol.designate_output('constructs', 'http://bioprotocols.org/paml#SampleCollection',
    goldengate_build_wells.output_pin('samples'))
    protocol.order(protocol.get_last_step(), output)
    
    return protocol, doc  # don't return until all else is complete

# the protocol needs to be updated with the 'temperature change' primitive for it to be possible to include the thermocycling steps

# incubation protocol by rapid improved thermocycling (https://www.protocols.io/view/golden-gate-lvl-0-b2k4qcyw)

# transformation procedure (https://cafgroup.lbl.gov/protocols/general-molecular-biology/chemically-competent)

# TODO: implement the 'temperature change' primitive step (ask jake/dan about implementing it on the markdown specialization and PAML package)
# TODO: write down the cool down time (ask jake/dan)


########################################
# Validate and write the document
if __name__ == '__main__':
    protocol: paml.Protocol
    protocol, doc = golden_gate_protocol() 
    print('Validating and writing protocol')
    v = doc.validate()
    assert len(v) == 0, "".join(f'\n {e}' for e in v)


print('Validating and writing protocol')
v = doc.validate()
assert len(v) == 0, "".join(f'\n {e}' for e in v)

rdf_filename = os.path.join(os.path.dirname(__file__), 'golden_gate_assembly.nt')
doc.write(rdf_filename, sbol3.SORTED_NTRIPLES)
print(f'Wrote file as {rdf_filename}')

from rdflib import Graph

g = Graph()

protocol.serialize(g)

new_g= Graph()
protocol.nodes[0].serialize(new_g)
new_g.serialize(format="turtle")