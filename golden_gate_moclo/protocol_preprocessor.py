import logging
import argparse
import datetime
import os

def read_args(explicit_args):
    parser = argparse.ArgumentParser()

    parser.add_argument('--constructs', '-c'
                        ,dest='%%CONSTRUCT DATA%%'
                        ,default='{}'
                        ,help='Construct data in JSON following the schema {construct_uuid:[insert_uuid, ...]}'
                        )
    parser.add_argument('--product_plate', '-pr'
                        ,dest='%%PRODUCT PLATE%%'
                        ,default='nest_96_wellplate_100ul_pcr_full_skirt'
                        ,help='Name of labware to use to hold the liquid culture. Use Opentrons standard names.'
                        )
    parser.add_argument('--reagent_plate', '-reg'
                        ,dest='%%REAGENT PLATE%%'
                        ,default='corning_96_wellplate_360ul_flat'
                        ,help='Name of labware to use to hold the glycerol source. Use Opentrons standard names.'
                        )
    parser.add_argument('--pipette', '-pi'
                        ,dest='%%PIPETTE%%'
                        ,default='p20_single_gen2'
                        ,help='Specify the pipette type. Use Opentrons standard names.'
                        )
    parser.add_argument('--tiprack', '-tr'
                        ,dest='%%TIPRACK%%'
                        ,default= None
                        ,help='Specify the tiprack type. Use Opentrons standard names. An option is inferred if nothing is provided.'
                        )

    args = vars(parser.parse_args())
    if explicit_args: args |= explicit_args

    if not args['%%TIPRACK%%']:
        args['%%TIPRACK%%'] = {
                               'p1000_single_gen2':'opentrons_96_tiprack_1000ul'
                               ,'p300_single_gen2':'opentrons_96_tiprack_300ul'
                               ,'p20_single_gen2':'opentrons_96_tiprack_20ul'
                              }[args['%%PIPETTE%%']]
        logging.info(f'Inferring tiprack as `{args["%%TIPRACK%%"]}` based on pipette')

    if not args['%%CONSTRUCT DATA%%']:
        raise(AttributeError, "No construct data was provided. use `python protocol_preprocessor.py --help` for more info")

    return args


def make_procedure(option_args = None): 
    params = read_args(option_args)
    APP_DIR = os.getcwd()
    TEMPLATE_NAME = 'golden_gate_moclo'

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

    return os.path.join(APP_DIR,'procedures',unique_file_name)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    output_file = make_procedure()
    logging.info(f'Success - file is {output_file}')