from opentrons import protocol_api
import math

metadata = {
    'apiLevel': '2.8',
    'protocolName': 'Cell Transformation',
    'author': 'Tim Dobbs',
    'source': 'https://openwetware.org/wiki/NanoBio:_Bacterial_Transformation',
    'description': """
                    Adaptable protocol for E. coli cell transformations
                    
                    Materials:
                    Chemically-competent cells (10ul per vector) [TOP10 from Invitrogen, catalog # C4040-03]
                        Alternate cells can be used depending on need
                    SOC Media (170ul per vector)
                    
                    Vector (2ul per vector)

                    Will also need plates poured with selective media appropriate for each vector
                   """
    }


def run(protocol: protocol_api.ProtocolContext):
    num_of_samples = %%NUM OF VECTORS%%
    
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

    #TODO Set well generators for each kind of necessary well
    #TODO Figure out appropriate labware for SOC and cells
    get_vector_well = well_generator('%%VECTOR PLATE%%')
    get_sample_well = well_generator('%%SAMPLE PLATE%%')

    # load a tiprack and glycerol resevoir
    #TODO Load 2 tipracks, one for each pipette type
    tipracks = list()
    for rack in range(math.ceil(num_of_samples / 95)):
        tipracks.append(protocol.load_labware('%%TIPRACK%%', next(get_slot)))
        
    # set the pipettes we will be using
    pipette_sm = protocol.load_instrument(
            '%%SMALL PIPETTE%%',
            mount='left',
            tip_racks=tipracks
    )
    pipette_lg = protocol.load_instrument(
            '%%LARGE PIPETTE%%',
            mount='right',
            tip_racks=tipracks
    )

    #TODO Create sensible locations for SOC and cells
    #TODO Create platemap for expected position of vectors
    protocol.comment('**CHECK BEFORE RUNNING**')
    protocol.comment('Ensure you have matched the expected vector platemap:')
    source_list = list()
    for sample in range(num_of_samples):
        source_well = next(get_sample_well)
        source_list.append(source_well)
        protocol.comment(f'SAMPLE {sample + 1} -> {source_well}')

    #TODO create output map for transformed cells
    well_mapping = {}
    for source in source_list:
        destination_list = []
        for repeat in range(repeats_per_sample):
            destination_list.append(next(get_cryo_well))
        well_mapping[source] = destination_list

    #TODO load competant cells into all of the necessary tubes
    flat_well_list = [well for sublist in well_mapping.values() for well in sublist]
    pipette.distribute(source=glycerol_resevoir.wells("A1"),dest=flat_well_list,volume=500, disposal_volume=0)

    #TODO load vectors into each appropriate tubes
    for source in well_mapping:
        pipette.distribute(source=source,dest=well_mapping[source],volume=500, disposal_volume=0)

    #TODO Pause 30 minutes to hold at temp

    #TODO Instruct user to heat shock 30 seconds at 42C, then ice 2 minutes

    #TODO Add 170ul of SOC to all wells in product platemap

    #TODO Instruct user to incubate at 37C for 15 minutes

    #TODO Instruct user to plate