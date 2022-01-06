import logging
import argparse
import datetime
import os

def read_args(explicit_args):
    parser = argparse.ArgumentParser()

    parser.add_argument('--vector_map', '-vm'
                        ,dest='%%VECTOR PLATEMAP%%'
                        ,default='None'
                        ,help='Vector Platemap data in JSON following the schema {VECTOR NAME:"A1", ...}'
                        )
    parser.add_argument('--num_vectors', '-nv'
                        ,dest='%%NUM OF VECTORS%%'
                        ,default='0'
                        ,help='Number of vectors to be used. If a platemap does not exist, this can be used instead to generate one'
                        )
    parser.add_argument('--vector_plate', '-vp'
                        ,dest='%%VECTOR PLATE%%'
                        ,default='nest_96_wellplate_100ul_pcr_full_skirt'
                        ,help='Name of labware to use to hold the vector solutions. Use Opentrons standard names.'
                        )
    parser.add_argument('--transformation_plate', '-tp'
                        ,dest='%%TRANSFORMATION PLATE%%'
                        ,default='nest_96_wellplate_200ul_flat'
                        ,help='Name of labware to use to hold the transformation cells. Use Opentrons standard names.'
                        )
    parser.add_argument('--cells_plate', '-cp'
                        ,dest='%%CELLS PLATE%%'
                        ,default='opentrons_24_tuberack_nest_1.5ml_snapcap'
                        ,help='Name of labware to use to hold the competant cells. Use Opentrons standard names.'
                        )
    parser.add_argument('--soc_plate', '-sp'
                        ,dest='%%SOC PLATE%%'
                        ,default='opentrons_6_tuberack_falcon_50ml_conical'
                        ,help='Name of labware to use to hold the SOC media. Use Opentrons standard names.'
                        )
    parser.add_argument('--small_pipette', '-smp'
                        ,dest='%%SMALL PIPETTE%%'
                        ,default='p20_single_gen2'
                        ,help='Specify the pipette type for small volumes. Use Opentrons standard names.'
                        )
    parser.add_argument('--small_tiprack', '-smt'
                        ,dest='%%SMALL TIPRACK%%'
                        ,default= None
                        ,help='Specify the tiprack type for small volumes. Use Opentrons standard names. An option is inferred if nothing is provided.'
                        )
    parser.add_argument('--large_pipette', '-lgp'
                        ,dest='%%LARGE PIPETTE%%'
                        ,default='p300_single_gen2'
                        ,help='Specify the pipette type for large volumes. Use Opentrons standard names.'
                        )
    parser.add_argument('--large_tiprack', '-lgt'
                        ,dest='%%LARGE TIPRACK%%'
                        ,default= None
                        ,help='Specify the tiprack type for large volumes. Use Opentrons standard names. An option is inferred if nothing is provided.'
                        )

    args = vars(parser.parse_args())
    if explicit_args: args |= explicit_args

    for size in ['LARGE','SMALL']:
        if not args[f'%%{size} TIPRACK%%']:
            args[f'%%{size} TIPRACK%%'] = {
                                'p1000_single_gen2':'opentrons_96_tiprack_1000ul'
                                ,'p300_single_gen2':'opentrons_96_tiprack_300ul'
                                ,'p20_single_gen2':'opentrons_96_tiprack_20ul'
                                }[args[f'%%{size} PIPETTE%%']]
            logging.info(f'Inferring tiprack as `{args[f"%%{size} TIPRACK%%"]}` based on pipette')

    if not args['%%VECTOR PLATEMAP%%'] and not args['%%NUM OF VECTORS%%']:
        raise(AttributeError, "No vector info was provided. use `python protocol_preprocessor.py --help` for more info")

    return args


def make_procedure(option_args = None): 
    params = read_args(option_args)
    APP_DIR = os.getcwd()
    TEMPLATE_NAME = 'cell_transform'

    #Get procedure template
    with open(os.path.join(APP_DIR, f'{TEMPLATE_NAME}.py')) as template_file:
        protocol = template_file.read()

    #Replace placeholders with values
    for placeholder in params:
        protocol = protocol.replace(placeholder, params[placeholder])

    #Save finalized version of of the file
    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_file_name = f'{TEMPLATE_NAME}_FILLED{now}.py'
    with open(os.path.join(APP_DIR,unique_file_name),'w') as output_file:
        output_file.write(protocol)

    return os.path.join(APP_DIR,unique_file_name)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    output_file = make_procedure()
    logging.info(f'Success - file is {output_file}')