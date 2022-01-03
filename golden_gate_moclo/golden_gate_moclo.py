from opentrons import protocol_api
import math

metadata = {
    'apiLevel': '2.8',
    'protocolName': 'Golden Gate MoClo Assembly',
    'author': 'Tim Dobbs',
    'source': 'https://www.protocols.io/view/golden-gate-lvl-0-b2k4qcyw',
    'description': """
                    Adaptable protocol for doing Golden Gate
                    assembly following the Modular Cloning standard.
                    A nice video description hereof MoClo:
                    https://www.youtube.com/playlist?list=PLvzzMEb3Zsn-n-ItduNGJzghAJsgsnd4Q

                    Materials:
                    T4 DNA Ligase buffer (1ul per construct) [from NEB]
                    T4 DNA Ligase (0.5ul per construct) [from NEB]
                    BsaI-HFv2 (0.5ul per construct) [from NEB]
                    Water (10ul per construct)

                    DNA insert (0.5ul per construct using it) [concentration?]
                    Entry Vector at 15ng/ul (0.5ul per construct)
                   """
    }

"""
    An example construct data structure:
    {'uuid351': ['fuGFP','RBS1','Term3','pOpen'], 'uuid963': ['cjBlue','RBS1','Term3','pOpen']}
"""


def run(protocol: protocol_api.ProtocolContext):
    #A dict mapping desired construct uids to lists of parts
    constructs = %%CONSTRUCT DATA%%

    def make_flat_material_list(constructs):
        return [insert for construct in constructs.values() for insert in construct]
    def make_unique_material_list(constructs):
        flat_list = make_flat_material_list(constructs)
        unique_material_list = list(set(flat_list))
        return unique_material_list
    inserts = {insert: 0.5 for insert in make_unique_material_list(constructs)}
    shared_reagents = {
                        'T4_DNA_Ligase': 0.5, 
                        'T4_DNA_Ligase_buffer': 1.0,
                        'BsaI-HFv2': 0.5,
                       }
    dilution = {'water': 10} # we will add water until each final well has this volume
    reagents = {**inserts, **shared_reagents, **dilution}
    
    # a function that gets us the next available slot on the deck
    available_slots = range(11,0,-1)
    def slot_generator(available_slots):
        for slot in available_slots:
            yield slot
    get_slot = slot_generator(available_slots)

    # a function that gets us the next available well on a plate
    # if the plate is full, the functions provisions another plate
    def well_generator(labware_type):
        while True:
            try:
                plate = protocol.load_labware(labware_type, next(get_slot))
            except StopIteration:
                 raise IndexError("""There aren't enough slots on the deck to run
                                        all of the samples you're attempting to run.
                                        Try doing it on two seperate runs."""
                                    ) #Would prefer to raise StopIteration, but OT seems to be weird about handling it
            for well in plate.wells():
                yield well
    get_reagent_well = well_generator('%%REAGENT PLATE%%')
    get_product_well = well_generator('%%PRODUCT PLATE%%')


    # load a tiprack
    # assume every transfer will be mixed, meaning the tip will need to be replaced
    total_tips = (
                  len(make_flat_material_list(constructs)) #inserts
                  + (len(constructs) * len(shared_reagents)) #shared reagents
                  + len(dilution) #we'll distribute first and thus use just one tip
                 )
    tipracks = list()
    for rack in range(math.ceil(total_tips / 95)):
        tipracks.append(protocol.load_labware('%%TIPRACK%%', next(get_slot)))
        
    
    # set the pipette we will be using
    pipette = protocol.load_instrument(
            '%%PIPETTE%%',
            mount='left',
            tip_racks=tipracks
    )

    protocol.comment('**CHECK BEFORE RUNNING**')
    protocol.comment('Ensure you have matched the expected reagent platemap:')

    #load all reagents onto plates and output wellmap for them
    reagent_map = dict()
    for reagent in reagents:
        reagent_well = next(get_reagent_well)
        reagent_map[reagent] = reagent_well
        protocol.comment(f'    REAGENT | {reagent} -> {reagent_well}')

    #create wellmap for products
    product_map = {}
    for construct in constructs:
        product_well = next(get_product_well)
        product_map[construct] = product_well

    #load water into all of the necessary wells
    #Begin by calculating required water dilution for each construct
    water_vols = list()
    for construct in product_map:
        target_vol = dilution['water']
        vol_from_inserts = sum([inserts[insert] for insert in constructs[construct]])
        vol_from_shared_reagents = sum(shared_reagents.values())
        water_vols.append(target_vol - vol_from_inserts - vol_from_shared_reagents)

    pipette.distribute(source=reagent_map['water'],
                       dest=list(product_map.values()),
                       volume=water_vols,
                       touch_tip=True
                       )

    #load reagents into each appropriate wells
    for construct in constructs:
        product_well = product_map[construct]
        for reagent in constructs[construct]:
            reagent_well = reagent_map[reagent]
            pipette.transfer(source=reagent_well,
                             dest=product_well,
                             volume=reagents[reagent],
                             new_tip='always',
                             touch_tip=True,
                             mix_after=(2,3)
                             )

    protocol.comment("""Loading complete.
                        Thermocycle product plate according to protocol schedule,
                        then transform to confirm assembly.
                        Construct platemap is as follows:""")
    for product in product_map:
        protocol.comment(f'    CONSTRUCT | {product} -> {product_map[product]}')