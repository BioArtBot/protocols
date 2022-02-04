import os
import tempfile
import unittest
import filecmp
import sbol3 
import paml
import tyto


# import paml_md
import uml

#############################################
# set up the document
print('Setting up document')
doc = sbol3.Document()
sbol3.set_namespace('https://bbn.com/scratch/')

#############################################
# Import the primitive libraries
print('Importing libraries')
paml.import_library('liquid_handling')
print('... Imported liquid handling')
paml.import_library('plate_handling')
print('... Imported plate handling')
paml.import_library('spectrophotometry')
print('... Imported spectrophotometry')
paml.import_library('sample_arrays')
print('... Imported sample arrays')

#############################################
# Create the protocol
print('Creating protocol')
protocol = paml.Protocol('golden_gate_protocol')
protocol.name = "golden_gate_protocol"
protocol.description = '''
This protocol is for Golden Gate modular cloning Assembly of pairs of DNA fragments into plasmids. 
'''
doc.add(protocol)


#  materials to be provisioned 

"""                
 Materials:
MC.016 PLASMID_BACKBONE_Kana
MC.043 PROMOTER+RBS_chloro
MC.066 GFP CDS
MC.024 TERMINATOR_chloro
enzyme_bsal
enzyme ligase
T4_buffer_NEb
"""


#create the selected materias in PAML form

def create_MC016() -> protocol.Component:
    plasmid_backbone = protocol.Component('plasmid_backbone',)
    plasmid_backbone.name = 'BIOBRICK, plasmid backbone, kanamicyn resistent'   
    return plasmid_backbone

def create_MC043() -> protocol.Component:
  promorbs = protocol.Component('promorbs',)
  promorbs.name = 'BIOBRICK, promoter+rbs, chloro resistent'   
  return promorbs

def create_MC066() -> protocol.Component:
  GFP = protocol.Component('GFP',)
  GFP.name = 'BIOBRICK, GFP coding sequence'   
  return GFP

def create_MC024() -> protocol.Component:
  terminator = protocol.Component('terminator',)
  terminator.name = 'BIOBRICK, sequence terminator, chloro resistent'   
  return terminator

def create_bsaI() -> sbol3.Component:
  BsaI = protocol.Component('enzyme_bsaI',)
  BsaI.name = 'enzyme, cut in selected parts, bsaI'   
  return bsaI

def create_bufferT4() -> sbol3.Component:
    buffer = protocol.Component('enzyme_buffer_T4',)
    buffer.name = 'buffer_T4, enzyme ligase, NEB'   
    return buffer

def create_ligase() -> sbol3.Component:
  ligase = protocol.Component('enzyme_ligase',)
  ligase.name = 'enzyme, bind sequences, needs buffer T4'   
  return ligase

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



# define the wells where you will be doing the GG assembly
goldengate_build_wells = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='G1:G2')


# add coordinates of each component in the plate using the provision and platecoordinates primitives

def provision_MC016(protocol: paml.Protocol, plate, plasmid_backbone) -> None:
    c_plasmid_backbone = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:B1')
    protocol.primitive_step('Provision', resource=plasmid_backbone, destination=c_plasmid_backbone.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

def provision_MC043(protocol: paml.Protocol, plate, promorbs) -> None:
    c_promorbs = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='C1:D1')
    protocol.primitive_step('Provision', resource=promorbs, destination=c_promorbs.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

def provision_MC066(protocol: paml.Protocol, plate, GFP) -> None:
    c_GFP = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='E1:F1')
    protocol.primitive_step('Provision', resource=GFP, destination=c_GFP.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

def provision_MC024(protocol: paml.Protocol, plate, terminator) -> None:
    c_terminator = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='G1:H1')
    protocol.primitive_step('Provision', resource=terminator, destination=c_terminator.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

def provision_bsaI(protocol: paml.Protocol, plate, bsaI) -> None:
    c_bsaI = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A2:B2')
    protocol.primitive_step('Provision', resource=bsaI, destination=c_bsaI.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

def provision_bufferT4(protocol: paml.Protocol, plate, buffer) -> None:
    c_buffer = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='C2:D2')
    protocol.primitive_step('Provision', resource=buffer, destination=c_buffer.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

def provision_ligase(protocol: paml.Protocol, plate, ligase) -> None:
    c_ligase = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='E2:F2')
    protocol.primitive_step('Provision', resource=ligase, destination=c_ligase.output_pin('samples'),
                            amount=sbol3.Measure(15, tyto.OM.microliter))

source_wells = [MC016, MC043, MC066, MC024, bsaI, buffer_T4, ligase ]

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

plasmid_backbone = create_MC016()
      doc.add(plasmid_backbone)

promorbs = create_MC043()
      doc.add(promorbs)

GFP = create_MC066()
      doc.add(GFP)

terminator = create_MC024()
      doc.add(ligase)

bsaI = create_bsaI()
      doc.add(bsaI)

buffer = create_bufferT4()
      doc.add(buffer)

ligase = create_ligase()
      doc.add(ligase)


# actual steps of the protocol (liquid handling part)
#get a plate

plate = create_plate(protocol)

# put DNA into the selected wells following the build plan

provision_MC016(protocol: paml.Protocol, plate, plasmid_backbone)

provision_MC043(protocol: paml.Protocol, plate, promorbs)

provision_MC066(protocol: paml.Protocol, plate, GFP)

provision_MC024(protocol: paml.Protocol, plate, terminator)

provision_bsaI(protocol: paml.Protocol, plate, bsaI)

provision_bufferT4(protocol: paml.Protocol, plate, buffer)

provision_ligase(protocol: paml.Protocol, plate, ligase)

# Transfer the dna to assembly wells following the build plan
protocol.primitive_step('TransferByMap', source=source_wells, destination=goldengate_build_wells.output_pin('samples'), plan=sbol3.Measure(2, tyto.OM.microliter))


output = protocol.designate_output('constructs', 'http://bioprotocols.org/paml#SampleCollection', build_wells.output_pin('samples'))
protocol.order(protocol.get_last_step(), output)  # don't return until all else is complete


########################################
# Validate and write the document
if __name__ == '__main__':
    new_protocol: paml.Protocol
    new_protocol, doc = golden_gate_protocol() 
    print('Validating and writing protocol')
    v = doc.validate()
    assert len(v) == 0, "".join(f'\n {e}' for e in v)



print('Validating and writing protocol')
v = doc.validate()
assert len(v) == 0, "".join(f'\n {e}' for e in v)

 rdf_filename = os.path.join(os.path.dirname(__file__), 'golden_gate_assembly.nt')
    doc.write(rdf_filename, sbol3.SORTED_NTRIPLES)
    print(f'Wrote file as {rdf_filename}')


# render and view the dot
dot = protocol.to_dot()
dot.render(f'{protocol.name}.gv')
dot.view()
