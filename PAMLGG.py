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

def create_material(material_name, description) -> sbol3.Component:
    material = sbol3.Component(material_name,f'https://github.com/BioArtBot/protocols/{material_name}')
    material.name = material_name
    material.description = description
    return material

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

def provision_component(protocol: paml.Protocol, plate, component, coordinates, volume):
    c_component = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates=coordinates)
    protocol.primitive_step('Provision', resource=component, destination=c_component.output_pin('samples'),
                            amount=sbol3.Measure(volume, tyto.OM.microliter))
    return c_component

# define the functions for assemblying the materials from the soource wells to the build wells

def assemble_buffer_and_water(protocol:paml.Protocol,c_buffer,c_water,goldengate_build_wells) -> None:
   
    protocol.primitive_step('TransferInto', source=c_buffer, destination=goldengate_build_wells.output_pin('samples'), 
                            amount=sbol3.Measure(2, tyto.OM.microliter), dispenseVelocity=sbol3.Measure(20, tyto.OM.minute)) 

    protocol.primitive_step('TransferInto', source=c_water, destination=goldengate_build_wells.output_pin('samples'), 
                            amount=sbol3.Measure(4, tyto.OM.microliter), dispenseVelocity=sbol3.Measure(20, tyto.OM.minute))

def assemble_components(protocol, component, goldengate_build_wells) -> None:
    protocol.primitive_step('TransferInto', source=component, destination=goldengate_build_wells.output_pin('samples'), 
                            amount=sbol3.Measure(1, tyto.OM.microliter), dispenseVelocity=sbol3.Measure(20, tyto.OM.minute)) 

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

    wavelength_param = protocol.input_value(
    'wavelength', sbol3.OM_MEASURE, optional=True,
    default_value=sbol3.Measure(600, tyto.OM.nanometer))

    # create the materials to be provisioned
    # include all of their info here so we can reference it later
    component_info = {
                'plasmid_backbone':{
                    'description': 'BIOBRICK, plasmid backbone DNA sequence, kanamicyn resistent',
                    'coordinates':'A1:B1',
                    'volume': 5},
                'promoter_and_rbs':{
                    'description': 'BIOBRICK, promoter and rbs DNA sequence, chlorophenicol resistent',
                    'coordinates': 'C1:D1',
                    'volume': 5},
                'GFP':{
                    'description': 'BIOBRICK, GFP DNA sequence, chlorophenicol resistent',
                    'coordinates': 'E1:F1',
                    'volume': 5},
                'terminator':{
                    'description': 'BIOBRICK, sequence terminator DNA sequence, chlorophenicol resistent',
                    'coordinates': 'G1:H1',
                    'volume': 5},
                'bsaI':{
                    'description': 'enzyme, will cut plasmid DNA in selected parts, bsaI',
                    'coordinates': 'A2:B2',
                    'volume': 5},
                'buffer':{
                    'description': 'buffer_T4, enzyme ligase, NEB',
                    'coordinates': 'C2:D2',
                    'volume': 5},
                'ligase':{
                    'description':'enzyme, bind sequences, needs buffer T4, ligase',
                    'coordinates': 'E2:F2',
                    'volume': 5},
                'water':{
                    'description': 'pure water, fills up to 10 ul',
                    'coordinates':'G2:H2',
                    'volume': 10}
    }

    materials = {}
    for component in component_info:
        materials[component] = create_material(component, component_info[component]['description'])
        doc.add(materials[component])

    # actual steps of the protocol (liquid handling part)

    #get a plate
    plate = create_plate(protocol)

    # provision components to the plate
    components = {}
    for component in component_info:
        components[component] = provision_component(protocol,
                                                    plate,
                                                    materials[component],
                                                    component_info[component]['coordinates'],
                                                    component_info[component]['volume']
                                                    )
    
   
    # define the wells where you will be doing the GG assembly  
    goldengate_build_wells = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A3:B3')

    # assemble DNA in build wells
    for component in components.values():
        assemble_components(protocol, component, goldengate_build_wells)

    assemble_buffer_and_water(protocol,components['buffer'],components['water'],goldengate_build_wells) 


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