from opentrons import protocol_api
import math
import datetime
import csv

metadata = {
    'apiLevel': '2.8',
    'protocolName': 'Cell Transformation',
    'author': 'Tim Dobbs',
    'source': 'https://openwetware.org/wiki/NanoBio:_Bacterial_Transformation',
    'description': """
                    Adaptable protocol for E. coli cell transformations

                    May provide a platemap for vectors or just a number of vectors
                    If a number of vectors is provided, they will be assigned to wells
                    The vector platemap is expected to have a structure like:
                    {'VECTOR NAME': 'A1'}
                    Well positions are plaintext and written in Letter-Number format
                    Currently only one plate at a time is supported if using platemaps
                    
                    Materials:
                    Chemically-competent cells (10ul per vector) [TOP10 from Invitrogen, catalog # C4040-03]
                        Alternate cells can be used depending on need
                    SOC Media (170ul per vector)
                    
                    Vector (2ul per vector)

                    Will also need plates poured with selective media appropriate for each vector
                   """
    }


def run(protocol: protocol_api.ProtocolContext):
    vector_map = %%VECTOR PLATEMAP%%
    num_of_samples = len(vector_map) if vector_map else %%NUM OF VECTORS%%

    multichannel = %%MULTICHANNEL MODE%%
    
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

    def map_sort(platemap):
        """
        Sorts the platemap by well position
        This is necessary for row because a multichannel pipette always
        pipettes all the rows in the same order. We sort the columns
        as well, because it's just nice to not arbitrarily have your
        columns mixed up on the new plate.
        """
        sorted_by_row = sorted(platemap.items(), key=lambda x: x[1][:1])
        sorted_by_row_n_col = sorted(sorted_by_row, key=lambda x: int(x[1][1:]))
        return {k: v for k, v in sorted_by_row_n_col}

    get_vector_well = well_generator('%%VECTOR PLATE%%')
    get_transform_well = well_generator('%%TRANSFORMATION PLATE%%')

    # load the tipracks for the large and small pipettes
    tipracks_sm = list()
    for rack in range(math.ceil((num_of_samples + 1) / 95)):
        tipracks_sm.append(protocol.load_labware('%%SMALL TIPRACK%%', next(get_slot)))
    tipracks_lg = [protocol.load_labware('%%LARGE TIPRACK%%', next(get_slot))]
        
    # set the pipettes we will be using
    pipette_sm = protocol.load_instrument(
            '%%SMALL PIPETTE%%',
            mount='left',
            tip_racks=tipracks_sm
    )
    pipette_lg = protocol.load_instrument(
            '%%LARGE PIPETTE%%',
            mount='right',
            tip_racks=tipracks_lg
    )


    protocol.comment('**CHECK BEFORE RUNNING**')
    protocol.comment('Ensure you have matched the expected vector platemap:')
    
    # Load compentant cells. Expecting volume will be in 100ul to 2000ul range
    if not multichannel:
        competant_cells_plate = protocol.load_labware('%%CELLS PLATE%%', next(get_slot))
        competant_cells = competant_cells_plate.wells("A1")
        protocol.comment(f'Competant Cells -> {competant_cells}')

    # Load SOC. Expecting volumes in 2ml - 30ml range
    SOC_plate = protocol.load_labware('%%SOC PLATE%%', next(get_slot))
    SOC = SOC_plate.wells("A1")
    protocol.comment(f'SOC -> {SOC} (Closed lid until after heat shock)')

    if not vector_map:
        vector_map = dict()
        for vector in range(num_of_samples):
            vector_map[f'VECTOR {vector}'] = next(get_vector_well)
    else:
        # Ensure the vectormap is in plate order
        vector_map = map_sort(vector_map)
        vector_plate = protocol.load_labware('%%VECTOR PLATE%%', next(get_slot))
        for vector in vector_map:
            vector_map[vector] = vector_plate.wells_by_name()[vector_map[vector]]
    for vector in vector_map:
        protocol.comment(f'{vector} -> {vector_map[vector]}')

    if multichannel: transformation_plate = protocol.load_labware('%%TRANSFORMATION PLATE%%', next(get_slot))

    transformed_cells_map = dict()
    vector_well_list = list()
    transformed_cells_well_list = list()
    for vector in vector_map:
        if multichannel:
            #multichannel mode only supports directly mapping from one plate to another
            transformed_cells_map[vector] = transformation_plate.wells_by_name()[vector_map[vector].well_name]
        else:
            transformed_cells_map[vector] = next(get_transform_well)
        # ensure that vectors are explicitly listed in the same order in both plates
        vector_well_list.append(vector_map[vector])
        transformed_cells_well_list.append(transformed_cells_map[vector])

    # Load competant cells into all of the necessary wells
    if multichannel:
        vol_per_well = 10
        vol_in_start_column = math.ceil(len(transformed_cells_map) / 8) * vol_per_well + (math.ceil(len(transformed_cells_map) / 8)) #add extra vol for blowout
        transformed_cells_plate = transformed_cells_well_list[0].parent
        protocol.comment(f'ACTION: Before starting, load {vol_in_start_column}ul of competant cells into the first column of {transformed_cells_plate}')
        wells_to_load = list(transformed_cells_map.values())[8:] #Skip first 9 wells bc they are already loaded
        pipette_sm.distribute(vol_per_well, transformed_cells_plate.columns(0), wells_to_load, new_tip='once')
    else:
        pipette_sm.distribute(source=competant_cells,dest=list(transformed_cells_map.values()),volume=10)

    # Load each vector into the appropriate well
    pipette_sm.transfer(source=vector_well_list,
                            dest=transformed_cells_well_list,
                            volume=2,
                            new_tip='always',
                            touch_tip=True,
                            mix_after=(2,3)
                            )

    protocol.comment('Loading complete')
    protocol.comment('Hold samples at 4C for 30 minutes, then heat shock at 42C for 30sec')
    protocol.comment('Finally, hold samples again at 4C for 2 minutes, then return plate(s) to their slot')
    protocol.pause('Once plate is returned, continue protocol to load SOC media')
    
    # Load SOC media into all of the necessary wells
    pipette_lg.transfer(source=SOC,
                        dest=list(transformed_cells_map.values()),
                        volume=170,
                        new_tip='always',
                        mix_after=(2,100)
                        )

    protocol.comment('All cells loaded. Incubate at 37C for 15min if Amp resistant, and 60min otherwise')
    protocol.comment('Once incubated, plate each strain on selective agar and grow overnight')
    protocol.comment('Transformed strains are in the following wells:')
    for vector in transformed_cells_map:
        protocol.comment(f'{vector} -> {transformed_cells_map[vector]}')


    filename = f'CELL_TRANSFORM_PLATEMAP_{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.csv'
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Vector', 'Vector Plate Well', 'Transformed Cell Plate Well'])
        for vector in transformed_cells_map:
            writer.writerow([vector, vector_map[vector].well_name, transformed_cells_map[vector].well_name])
    csvfile.close()
    protocol.comment(f'Output CSV map is saved as {filename} ON the robot.')
    protocol.comment('This file will persist until the robot is turned off')