# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 14:26:07 2019

@author: mh2210
"""

# python dnabot\dnabot_app.py nogui --construct_path \\icnas1.cc.ic.ac.uk\ljh119\GitHub\DNA-BOT\examples\construct_csvs\storch_et_al_cons\storch_et_al_cons.csv --source_paths \\icnas1.cc.ic.ac.uk\ljh119\GitHub\DNA-BOT\examples\part_linker_csvs\BIOLEGIO_BASIC_STD_SET.csv \\icnas1.cc.ic.ac.uk\ljh119\GitHub\DNA-BOT\examples\part_linker_csvs\part_plate_2_230419.csv
# python3 dnabot/dnabot_app.py nogui --construct_path /Users/liamhallett/Documents/GitHub/DNA-BOT/examples/construct_csvs/storch_et_al_cons/storch_et_al_cons.csv --source_paths /Users/liamhallett/Documents/GitHub/DNA-BOT/examples/part_linker_csvs/BIOLEGIO_BASIC_STD_SET.csv /Users/liamhallett/Documents/GitHub/DNA-BOT/examples/part_linker_csvs/part_plate_2_230419.csv

print("\nINITIALISING>>>")

import os
import csv
import argparse
import pandas as pd
import numpy as np
import json
import sys
import dnabot_gui as gui
import tkinter as tk
import mplates

# Constant str
TEMPLATE_DIR_NAME = 'template_ot2_scripts'
CLIP_TEMP_FNAME = 'clip_template.py'
MAGBEAD_TEMP_FNAME = 'purification_template.py'
F_ASSEMBLY_TEMP_FNAME = 'assembly_template.py'
TRANS_SPOT_TEMP_FNAME = 'transformation_template.py'
CLIP_FNAME = '1_clip.ot2.py'
MAGBEAD_FNAME = '2_purification.ot2.py'
F_ASSEMBLY_FNAME = '3_assembly.ot2.py'
TRANS_SPOT_FNAME = '4_transformation.ot2.py'
CLIPS_INFO_FNAME = 'clip_run_info.csv'
FINAL_ASSEMBLIES_INFO_FNAME = 'final_assembly_run_info.csv'
WELL_OUTPUT_FNAME = 'wells.txt'

# Constant floats/ints
CLIP_DEAD_VOL = 60
CLIP_VOL = 30
T4_BUFF_VOL = 3
BSAI_VOL = 1
T4_LIG_VOL = 0.5
CLIP_MAST_WATER = 15.5
PART_PER_CLIP = 200
MIN_VOL = 1
MAX_CONSTRUCTS = 96
MAX_CLIPS = 48
FINAL_ASSEMBLIES_PER_CLIP = 15
DEFAULT_PART_VOL = 1
MAX_SOURCE_PLATES = 6
MAX_FINAL_ASSEMBLY_TIPRACKS = 7

# Constant dicts
SPOTTING_VOLS_DICT = {2: 5, 3: 5, 4: 5, 5: 5, 6: 5, 7: 5}

# Constant lists
SOURCE_DECK_POS = ['2', '5', '8', '7', '10', '11'] # deck positions available for source plates (only pos 2 and 5 are normally used)


def __cli():
    """Command line interface.

    :returns: CLI arguments
    :rtype: <argparse.Namespace>
    """
    desc = "DNA assembly using BASIC on OpenTrons."
    parser = argparse.ArgumentParser(description=desc) # creates an argparse object that allows for command line interfacing - https://docs.python.org/3/howto/argparse.html#id1

    # Specific options for collecting settings from command line
    subparsers = parser.add_subparsers(help='Optional, to define settings from the terminal instead of the graphical '
                                            'interface. Type "python dnabot_app.py nogui -h" for more info.')
    parser_nogui = subparsers.add_parser('nogui') # adds a new sub-parser called nogui for parsing variables directly from the command line
    parser_nogui.add_argument('--construct_path', help='Construct CSV file.', required=True)
    parser_nogui.add_argument('--source_paths', help='Source CSV files.', nargs='+', required=True)
    parser_nogui.add_argument('--etoh_well', help='Well coordinate for Ethanol. Default: A11', default='A11', type=str)
    parser_nogui.add_argument('--soc_column', help='Column coordinate for SOC. Default: 1', default=1, type=int)
    parser_nogui.add_argument('--output_dir',
                              help='Output directory. Default: same directory than the one containing the '
                                   '"construct_path" file',
                              default=None, type=str or None)
    parser_nogui.add_argument('--template_dir',
                              help='Template directory. Default: "template_ot2_scripts" located next to the present '
                                   'script.',
                              default=None, type=str or None)
    # Makes life easier to decide if we should switch to GUI or not
    parser.set_defaults(nogui=False)
    parser_nogui.set_defaults(nogui=True)
    return parser.parse_args()


def __info_from_gui():
    """Pop GUI to collect user inputs.

    :returns user_inputs: info collected
    :rtype: dict
    """
    user_inputs = {
        'construct_path': None,
        'sources_paths': None,
        'etoh_well': None,
        'soc_column': None
    }

    # Obtain user input
    print("Requesting user input, if not visible checked minimized windows.")
    root = tk.Tk()
    dnabotinst = gui.DnabotApp(root)
    root.mainloop()
    root.destroy()
    if dnabotinst.quit_status:
        sys.exit("User specified 'QUIT' during app.")
    # etoh_well and soc_column are silently collected by the gui
    user_inputs['etoh_well'] = dnabotinst.etoh_well
    user_inputs['soc_column'] = dnabotinst.soc_column
    # construct file path
    root = tk.Tk()
    user_inputs['construct_path'] = gui.UserDefinedPaths(root, 'Construct csv file').output
    root.destroy()

    # part & linker file paths
    root = tk.Tk()
    user_inputs['sources_paths'] = gui.UserDefinedPaths(root, 'Sources csv files', multiple_files=True).output
    root.destroy()

    return user_inputs


def main():
    # Settings
    args = __cli()
    if args.nogui:  # input args using argparse
        etoh_well = args.etoh_well
        soc_column = args.soc_column
        construct_path = args.construct_path
        sources_paths = args.source_paths
        if args.output_dir == None:
            output_dir = os.path.dirname(construct_path)
        else:
            output_dir = args.output_dir
        template_dir = args.template_dir
        print("\netoh_well ", etoh_well)
        print("\nsoc_column ", soc_column)
        print("\nconstruct_path ", construct_path)
        print("\nsources_paths ", sources_paths)
        print("\noutput_dir ", output_dir)
        print("\ntemplate_dir", template_dir)
    else:       # input args from gui
        user_inputs = __info_from_gui()
        etoh_well = user_inputs['etoh_well']
        soc_column = user_inputs['soc_column']
        construct_path = user_inputs['construct_path']
        sources_paths = user_inputs['sources_paths']
        output_dir = os.path.dirname(construct_path)
        template_dir = None

    # Args checking
    if len(sources_paths) > len(SOURCE_DECK_POS):
        raise ValueError('Number of source plates exceeds deck positions.')

    # Path to template directory
    if template_dir is not None:
        # Just to comment this case: only way to fall here is that the variable has been set throught the command
        # line arguments, nothing to do.
        template_dir_path = template_dir
        pass
    elif __name__ == '__main__':
        # Alternatively, try to automatically deduce the path relatively to the main script path
        script_path = os.path.abspath(__file__)
        template_dir_path = os.path.abspath(os.path.join(script_path, '..', TEMPLATE_DIR_NAME))
    else:
        # Fallback
        generator_dir = os.getcwd()
        template_dir_path = os.path.abspath(os.path.join(generator_dir, TEMPLATE_DIR_NAME))

    # Dealing with output dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)           # make a directory called output_dir
    os.chdir(output_dir)                  # change to that directory

    # Prefix name
    construct_base = os.path.basename(construct_path)
    construct_base = os.path.splitext(construct_base)[0]    # returns the constructs csv path without the file name
    print('User input successfully collected.')

    # Process input csv files
    print('Processing input csv files...')
    constructs_list = generate_constructs_list(construct_path)  # returns a list of pandas dfs, each containing the clip reactions required for a given construct
    clips_df = generate_clips_df(constructs_list)               # generates df of unique clips, numbers required of each, and mag well location
    sources_dict = generate_sources_dict(sources_paths)         # generates dict for sources with well location, conc, and pos location

    # calculate OT2 script variables
    print('Calculating OT-2 variables...')
    clips_dict = generate_clips_dict(clips_df, sources_dict)    # returns a dictionary with prefix wells, prefix plates, suffix wells, suffix plates, parts wells, parts plates, parts vols, water vols
    magbead_sample_number = clips_df['number'].sum()            # total number of mag bead purifications required 
    final_assembly_dict = generate_final_assembly_dict(constructs_list, # returns a dictionary with assembly wells as keys and clip wells as values 
                                                       clips_df)
    final_assembly_tipracks = calculate_final_assembly_tipracks(        # returns total number of tipracks required
        final_assembly_dict)
    spotting_tuples = generate_spotting_tuples(constructs_list,         # returns a list of spotting tuples with the assembly well twice and the vol required - this means that the assemblies are spotted twice
                                               SPOTTING_VOLS_DICT)

    print('Writing files...')
    # Write OT2 scripts
    generate_ot2_script(CLIP_FNAME, os.path.join(                       # write clips script using clips_dict
        template_dir_path, CLIP_TEMP_FNAME), clips_dict=clips_dict)
    generate_ot2_script(MAGBEAD_FNAME, os.path.join(                    # write magbead purification script using magbead_sample_number and etoh_well
        template_dir_path, MAGBEAD_TEMP_FNAME),
        sample_number=magbead_sample_number,
        ethanol_well=etoh_well)
    generate_ot2_script(F_ASSEMBLY_FNAME, os.path.join(                 # write assembly script using final_assembly_dict and final_assembly_tipracks
        template_dir_path, F_ASSEMBLY_TEMP_FNAME),
        final_assembly_dict=final_assembly_dict,
        tiprack_num=final_assembly_tipracks)
    generate_ot2_script(TRANS_SPOT_FNAME, os.path.join(                 # write spotting script using spotting_tuples and SOC column
        template_dir_path, TRANS_SPOT_TEMP_FNAME),
        spotting_tuples=spotting_tuples,
        soc_well=f"A{soc_column}")

    # Write non-OT2 scripts
    if 'metainformation' in os.listdir():
        pass
    else:
        os.makedirs('metainformation')                                              # make a new folder in the directory called 'metainformation'
    os.chdir('metainformation')
    master_mix_df = generate_master_mix_df(clips_df['number'].sum())                # return master mix for total number of clips needed
    sources_paths_df = generate_sources_paths_df(sources_paths, SOURCE_DECK_POS)
    dfs_to_csv(construct_base + '_' + CLIPS_INFO_FNAME, index=False,
               MASTER_MIX=master_mix_df, SOURCE_PLATES=sources_paths_df,
               CLIP_REACTIONS=clips_df)
    with open(construct_base + '_' + FINAL_ASSEMBLIES_INFO_FNAME,                   # write a new csv for FINAL_ASSEMBLIES_INFO_FNAME
              'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        for final_assembly_well, construct_clips in final_assembly_dict.items():    # add in assembly wells and construct clips
            csvwriter.writerow([final_assembly_well, construct_clips])
    with open(construct_base + '_' + WELL_OUTPUT_FNAME, 'w') as f:                  # return text document with magbead ethanol well and SOC well
        f.write('Magbead ethanol well: {}'.format(etoh_well))
        f.write('\n')
        f.write('SOC column: {}'.format(soc_column))
    print('BOT-2 generator successfully completed!')


def generate_constructs_list(path):
    """Generates a list of dataframes corresponding to each construct. Each 
    dataframe lists components of the CLIP reactions required.

    """

    def process_construct(construct):
        """Processes an individual construct into a dataframe of CLIP reactions
        outlining prefix linkers, parts and suffix linkers.

        """

        def interogate_linker(linker):
            """Interrogates linker to determine if the suffix linker is a UTR
            linker.

            """
            if linker.startswith('U'):
                return linker.split('-')[0] + '-S'
            else:
                return linker + "-S"

        clips_info = {'prefixes': [], 'parts': [],
                      'suffixes': []}
        for i, sequence in enumerate(construct):
            if i % 2 != 0: # for odd values (ie non-linkers)
                clips_info['parts'].append(sequence)    # add name to clip_info dict parts array
                clips_info['prefixes'].append(
                    construct[i - 1] + '-P')            # add name of previous name to clip_info dict linker prefixes array
                if i == len(construct) - 1:             # if the part is the final part in the construct...
                    suffix_linker = interogate_linker(construct[0]) # ...find the suffix linker name from the first linker in the construct 
                    clips_info['suffixes'].append(suffix_linker)    # add the suffix linker to the clips_info dict
                else:
                    suffix_linker = interogate_linker(construct[i + 1])
                    clips_info['suffixes'].append(suffix_linker)    # add the suffix linker to the clips_info dict
        return pd.DataFrame.from_dict(clips_info)                   # converts the dictionary of parts to a pd.DataFrame

    constructs_list = []
    with open(path, 'r') as csvfile: # opens path as csvfile
        csv_reader = csv.reader(csvfile) # reads csv file
        for index, construct in enumerate(csv_reader): # for every construct (ie the row) in the csv file...
            if index != 0:  # Checks if row is header.
                construct = list(filter(None, construct)) # removes empty values from csv
                if not construct[1:]:
                    break
                else:
                    constructs_list.append(process_construct(construct[1:]))    # assembles a dictionary of parts and linkers for the constructs csv

    # Errors
    if len(constructs_list) > MAX_CONSTRUCTS:
        raise ValueError(
            'Number of constructs exceeds maximum. Reduce construct number in construct.csv.')
    else:
        return constructs_list

def generate_clips_df(constructs_list):
    """Generates a dataframe containing information about all the unique CLIP 
    reactions required to synthesise the constructs in constructs_list.

    """
    merged_construct_dfs = pd.concat(constructs_list, ignore_index=True) # converts list of dfs into one large df
    unique_clips_df = merged_construct_dfs.drop_duplicates()    # drop duplicates
    unique_clips_df = unique_clips_df.reset_index(drop=True)    # reset index (this creates a df of all unique clips)
    clips_df = unique_clips_df.copy() # makes a copy which is disconnected to the original

    # Error
    if len(unique_clips_df.index) > MAX_CLIPS:
        raise ValueError(
            'Number of CLIP reactions exceeds 48. Reduce number of constructs in construct.csv.')

    # Count number of each CLIP reaction
    clip_count = np.zeros(len(clips_df.index))              # creates an empty array the for each unique clip
    for i, unique_clip in unique_clips_df.iterrows():       # for every unique clip...
        for _, clip in merged_construct_dfs.iterrows():     # ...for every clip...
            if unique_clip.equals(clip):                    # ...if they are the same
                clip_count[i] = clip_count[i] + 1           # ...tally that unique clip
    clip_count = clip_count // FINAL_ASSEMBLIES_PER_CLIP + 1    # find the number of clip wells needed (ie there is a max number of clip uses per reaction/well, if required clips exceeds this for a unique clip then start a new well)
    clips_df['number'] = [int(i) for i in clip_count.tolist()]  # add a count column to unique clips df

    # Associate well/s for each CLIP reaction
    clips_df['mag_well'] = pd.Series(['0'] * len(clips_df.index),
                                     index=clips_df.index)  # adds new column 'mag_well'
    for index, number in clips_df['number'].iteritems():    # for every unique clip...
        if index == 0:                                      # ...if its the first clip...
            mag_wells = [] 
            for x in range(number):                         # ...for every count of that clip...
                mag_wells.append(mplates.final_well(x + 1 + 48))    # parse into mag wells to return list
            clips_df.at[index, 'mag_well'] = tuple(mag_wells)       # return tuple to mag_well col
        else:
            mag_wells = []
            for x in range(number):
                well_count = clips_df.loc[
                    :index - 1, 'number'].sum() + x + 1 + 48        # adds all previous clips to clip count
                mag_wells.append(mplates.final_well(well_count))
            clips_df.at[index, 'mag_well'] = tuple(mag_wells)
    return clips_df


def generate_sources_dict(paths):
    """Imports csvs files containing a series of parts/linkers with 
    corresponding information into a dictionary where the key corresponds with
    part/linker and the value contains a tuple of corresponding information.

    Args:
        paths (list): list of strings each corresponding to a path for a 
                      sources csv file. 

    """
    sources_dict = {}
    for deck_index, path in enumerate(paths):   # deck_index allocated to each source
        with open(path, 'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            for index, source in enumerate(csv_reader):
                if index != 0:
                    csv_values = source[1:]     # adds the part well location and concentration
                    csv_values.append(SOURCE_DECK_POS[deck_index])      # references the available source deck locations, allocates to the deck index, adds this value to the tuple
                    sources_dict[str(source[0])] = tuple(csv_values)    # adds value to sources dict
    return sources_dict


def generate_clips_dict(clips_df, sources_dict):
    """Using clips_df and sources_dict, returns a clips_dict which acts as the 
    sole variable for the opentrons script "clip.ot2.py".

    """
    max_part_vol = CLIP_VOL - (T4_BUFF_VOL + BSAI_VOL + T4_LIG_VOL
                               + CLIP_MAST_WATER + 2)
                               
    clips_dict = {'prefixes_wells': [], 'prefixes_plates': [],
                  'suffixes_wells': [], 'suffixes_plates': [],
                  'parts_wells': [], 'parts_plates': [], 'parts_vols': [],
                  'water_vols': []}

    # Generate clips_dict from args
    try:
        for _, clip_info in clips_df.iterrows():                                            # for every unique clip...
            prefix_linker = clip_info['prefixes']                                           # ...subset the prefix linker...
            clips_dict['prefixes_wells'].append([sources_dict[prefix_linker][0]]            # ...add the well ID to the clips_dict prefix wells as many times as unique clip used
                                                * clip_info['number'])
            clips_dict['prefixes_plates'].append(                                           # ...pass the prefix linker info (well pos, conc, deck pos) to handle_2_columns(), returning tuple of 3 values in the same format
                [handle_2_columns(sources_dict[prefix_linker])[2]] * clip_info['number'])
            suffix_linker = clip_info['suffixes']                                           # ...subset the prefix linker...
            clips_dict['suffixes_wells'].append([sources_dict[suffix_linker][0]]            # ...add the well ID to the clips_dict suffix wells as many times as unique clip used
                                                * clip_info['number'])
            clips_dict['suffixes_plates'].append(                                           # ...return suffix linker info in correct format as before
                [handle_2_columns(sources_dict[suffix_linker])[2]] * clip_info['number'])
            part = clip_info['parts']                                                       # ...subset the part...
            clips_dict['parts_wells'].append(                                               # ...pass the part info (well pos, conc, deck pos) to handle_2_columns(), returning tuple of 3 values in the same format
                [sources_dict[part][0]] * clip_info['number'])
            clips_dict['parts_plates'].append(                                              # ...return part info in correct format as before
                [handle_2_columns(sources_dict[part])[2]] * clip_info['number'])
            if not sources_dict[part][1]:                                                   # if concentration not defined...
                clips_dict['parts_vols'].append([DEFAULT_PART_VOL] *                        # ...add the default vol required * number of clips required
                                                clip_info['number'])
                clips_dict['water_vols'].append([max_part_vol - DEFAULT_PART_VOL]           # ...add the water vol required * number of clips required
                                                * clip_info['number'])
            else:
                part_vol = round(
                    PART_PER_CLIP / float(sources_dict[part][1]), 1)    # c1*v1/c2 = v2 where parts normally require 1ul at 100ng/ul 
                if part_vol < MIN_VOL:                                  # correct for min vol requirement (could add min conc here instead)
                    part_vol = MIN_VOL
                elif part_vol > max_part_vol:                           # correct for max vol requirement
                    part_vol = max_part_vol
                water_vol = max_part_vol - part_vol                     # calculate water vol
                clips_dict['parts_vols'].append(
                    [part_vol] * clip_info['number'])
                clips_dict['water_vols'].append(
                    [water_vol] * clip_info['number'])
    except KeyError:
        sys.exit('likely part/linker not listed in sources.csv')
    for key, value in clips_dict.items():                               # removes sublists from dict values
        clips_dict[key] = [item for sublist in value for item in sublist]
    return clips_dict


def generate_final_assembly_dict(constructs_list, clips_df):
    """Using constructs_list and clips_df, returns a dictionary of final
    assemblies with keys defining destination plate well positions and values
    indicating which clip reaction wells are used.

    """
    final_assembly_dict = {}
    clips_count = np.zeros(len(clips_df.index))                                 # empty array of length unique clips
    for construct_index, construct_df in enumerate(constructs_list):            # for every construct df in constructs list...
        construct_well_list = []
        for _, clip in construct_df.iterrows():                                 # ...for every clip in that constructs df...
            clip_info = clips_df[(clips_df['prefixes'] == clip['prefixes']) &   # ...selects unique clip (in clips df) by matching its linkers and part
                                 (clips_df['parts'] == clip['parts']) &
                                 (clips_df['suffixes'] == clip['suffixes'])]
            clip_wells = clip_info.at[clip_info.index[0], 'mag_well']           # subset mag bead wells
            clip_num = int(clip_info.index[0])                                  # find number of clips required
            clip_well = clip_wells[int(clips_count[clip_num] //                 # finds the mag bead well for that clip
                                       FINAL_ASSEMBLIES_PER_CLIP)]
            clips_count[clip_num] = clips_count[clip_num] + 1                   # counts clips so that mag well changes when clips required exceeds clips per well 
            construct_well_list.append(clip_well)                               # adds clip well to list
        final_assembly_dict[mplates.final_well(                                 # creates dict with assembly well as the key for each construct, and lists of required clip wells as values
            construct_index + 1)] = construct_well_list
    return final_assembly_dict


def calculate_final_assembly_tipracks(final_assembly_dict):
    """Calculates the number of final assembly tipracks required ensuring
    no more than MAX_FINAL_ASSEMBLY_TIPRACKS are used.

    """
    final_assembly_lens = []
    for values in final_assembly_dict.values():                     # for every assembly...
        final_assembly_lens.append(len(values))                     # ...count tips required
    master_mix_tips = len(list(set(final_assembly_lens)))           # how many MM tips required = number of different reactions requiring different numbers of parts (different master mixes required for each)
    total_tips = master_mix_tips + sum(final_assembly_lens)
    final_assembly_tipracks = (total_tips-1) // 96 + 1              # tipracks needed
    if final_assembly_tipracks > MAX_FINAL_ASSEMBLY_TIPRACKS:
        raise ValueError(
            'Final assembly tiprack number exceeds number of slots. Reduce number of constructs in constructs.csv')
    else:
        return final_assembly_tipracks


def generate_spotting_tuples(constructs_list, spotting_vols_dict):
    """Using constructs_list, generates a spotting tuple
    (Refer to 'transformation_spotting_template.py') for every column of 
    constructs, assuming the 1st construct is located in well A1 and wells
    increase linearly. Target wells locations are equivalent to construct well
    locations and spotting volumes are defined by spotting_vols_dict.

    Args:
        spotting_vols_dict (dict): Part number defined by keys, spotting
            volumes defined by corresponding value.

    """
    # Calculate wells and volumes
    wells = [mplates.final_well(x + 1) for x in range(len(constructs_list))]    # assigns a final well for every assembly using a list comprehension 
    vols = [SPOTTING_VOLS_DICT[len(construct_df.index)]                         # assigns spotting vol based on how many clips there are in each reaction
            for construct_df in constructs_list]

    # Package spotting tuples
    spotting_tuple_num = len(constructs_list)//8 + (1                           # number of spotting steps with the 8 channel pipette
                                                    if len(constructs_list) % 8 > 0 else 0)
    spotting_tuples = []
    for x in range(spotting_tuple_num):                                         # for every spotting step...
        if x == spotting_tuple_num - 1:                                         # 
            tuple_wells = tuple(wells[8*x:])
            tuple_vols = tuple(vols[8*x:])
        else:
            tuple_wells = tuple(wells[8*x:8*x + 8])
            tuple_vols = tuple(vols[8*x:8*x + 8])
        spotting_tuples.append((tuple_wells, tuple_wells, tuple_vols))
    return spotting_tuples


def generate_ot2_script(ot2_script_path, template_path, **kwargs):
    """Generates an ot2 script named 'ot2_script_path', where kwargs are 
    written as global variables at the top of the script. For each kwarg, the 
    keyword defines the variable name while the value defines the name of the 
    variable. The remainder of template file is subsequently written below.        

    """
    with open(ot2_script_path, 'w') as wf:
        with open(template_path, 'r') as rf:            # opens template in read format
            for index, line in enumerate(rf):
                if line[:3] == 'def':                   # find location of def in the file and save index as function start
                    function_start = index
                    break
                else:
                    wf.write(line)                      # otherwise write the line (ie write all lines up to start)
            for key, value in kwargs.items():           # read in kwargs (user defined input)
                wf.write('{}='.format(key))             # write 'key = '
                if type(value) == dict:                 # if the kwarg value is a dictionary then return as a str 
                    wf.write(json.dumps(value))
                elif type(value) == str:                # if the kwarf value is a string then return with''
                    wf.write("'{}'".format(value))
                else:                                   # else return string
                    wf.write(str(value))
                wf.write('\n')
            wf.write('\n')
        with open(template_path, 'r') as rf:            # reopen rf and write lines succeeding the user defined input
            for index, line in enumerate(rf):
                if index >= function_start - 1:
                    wf.write(line)


def generate_master_mix_df(clip_number):
    """Generates a dataframe detailing the components required in the clip 
    reaction master mix.

    """
    COMPONENTS = {'Component': ['Promega T4 DNA Ligase buffer, 10X',
                                'Water', 'NEB BsaI-HFv2',
                                'Promega T4 DNA Ligase']}
    VOL_COLUMN = 'Volume (uL)'
    master_mix_df = pd.DataFrame.from_dict(COMPONENTS) 
    master_mix_df[VOL_COLUMN] = (clip_number + CLIP_DEAD_VOL/CLIP_VOL) * \
        np.array([T4_BUFF_VOL,              # ratios of parts always the same, volume per one reaction timesed by total number of clips plus excess
                  CLIP_MAST_WATER,
                  BSAI_VOL,
                  T4_LIG_VOL])
    return master_mix_df


def generate_sources_paths_df(paths, deck_positions):
    """Generates a dataframe detailing source plate information.

    Args:
        paths (list): list of strings specifying paths to source plates.
        deck_positions (list): list of strings specifying candidate deck positions.

    """
    source_plates_dict = {'Deck position': [], 'Source plate': [], 'Path': []}  # empty dict
    for index, path in enumerate(paths):                                        # for every source...
        source_plates_dict['Deck position'].append(SOURCE_DECK_POS[index])      # add source deck position based on order of inputs
        source_plates_dict['Source plate'].append(os.path.basename(path))       # add source plate ID
        source_plates_dict['Path'].append(path)                                 # add source path name
    return pd.DataFrame(source_plates_dict)


def dfs_to_csv(path, index=True, **kw_dfs):
    """Generates a csv file defined by path, where kw_dfs are 
    written one after another with each key acting as a title. If index=True,
    df indexes are written to the csv file.

    """
    with open(path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        for key, value in kw_dfs.items():       # for every kw_dfs...
            csvwriter.writerow([str(key)])      # write a title relating to the key
            value.to_csv(csvfile, index=index)  # write a block relating to the value
            csvwriter.writerow('')

def handle_2_columns(datalist, return_list = False):
    """This function has the intent of changing:
    ('A8', '2') => ('A8', '', '2')
    ('A8', '', '2') => ('A8', '', '2')
    [('E2', '5')] => [('E2', '', '5')]
    [('G1', '', '5')] => [('G1', '', '5')]
    with the purpose of handling 2 column csv part file inputs,
    as at times when 2 column csv files are input it creates tuples
    of length 2 instead of 3
    """
    if isinstance(datalist,list):   # if data list is a list, extract tuple
        datalist = datalist[0] 
        return_list = True
    if len(datalist) == 2:          # if tuple is of length 2, insert empty value at position 1
        datalist = (datalist[0], "", datalist[1])
    if return_list:                 # if list passed to function, return output as list
        datalist = [datalist]
    return datalist

if __name__ == '__main__':
    main()

# 13 27 4 3 1 5 2 7 13 12 16 7
# s  s  m t w t f s s  m  t  w