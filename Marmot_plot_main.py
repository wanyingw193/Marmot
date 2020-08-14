# -*- coding: utf-8 -*-
"""
Created on Thu Dec  5 14:16:30 2019

@author: dlevie
"""
#%%

import pandas as pd
import os
import pathlib
import matplotlib as mpl
import sys
import importlib 
#changes working directory to location of this python file
os.chdir(pathlib.Path(__file__).parent.absolute()) #If running in sections you have to manually change the current directory to where Marmot is

from meta_data import MetaData

# import capacity_out
# import thermal_cap_reserve
# import constraints

class plottypes:
    
    def __init__(self, figure_type, figure_output_name, argument_list):
        self.figure_type = figure_type
        self.figure_output_name = figure_output_name
        self.argument_list = argument_list
        
    def runmplot(self):
        plot = importlib.import_module(self.figure_type)
        fig = plot.mplot(self.argument_list)
        
        process_attr = getattr(fig, self.figure_output_name)
        
        Figure_Out = process_attr()
        return Figure_Out

try:
    print("Will plot row:" +(sys.argv[1]))
    print(str(len(sys.argv)-1)+" arguments were passed from commmand line.")
except IndexError:
    #No arguments passed
    pass

#===============================================================================
# Graphing Defaults
#===============================================================================

mpl.rc('xtick', labelsize=11)
mpl.rc('ytick', labelsize=12)
mpl.rc('axes', labelsize=16)
mpl.rc('legend', fontsize=11)
mpl.rc('font', family='serif')

#===============================================================================
# Load Input Properties
#===============================================================================

#A bug in pandas requires this to be included, otherwise df.to_string truncates long strings
#Fix available in Pandas 1.0 but leaving here in case user version not up to date
pd.set_option("display.max_colwidth", 1000)

Marmot_user_defined_inputs = pd.read_csv('Marmot_user_defined_inputs.csv', usecols=['Input','User_defined_value'],
                                         index_col='Input', skipinitialspace=True)

Marmot_plot_select = pd.read_csv("Marmot_plot_select.csv")

Scenario_name = Marmot_user_defined_inputs.loc['Main_scenario_plot'].squeeze().strip()

# Folder to save your processed solutions
Marmot_Solutions_folder = Marmot_user_defined_inputs.loc['Marmot_Solutions_folder'].to_string(index=False).strip()

# These variables (along with Region_Mapping) are used to initialize MetaData
PLEXOS_Solutions_folder = Marmot_user_defined_inputs.loc['PLEXOS_Solutions_folder'].to_string(index=False).strip()
HDF5_folder_in = os.path.join(PLEXOS_Solutions_folder, Scenario_name)

Multi_Scenario = pd.Series(Marmot_user_defined_inputs.loc['Multi_scenario_plot'].squeeze().split(",")).str.strip().tolist()

# For plots using the differnec of the values between two scenarios.
# Max two entries, the second scenario is subtracted from the first.
Scenario_Diff = pd.Series(str(Marmot_user_defined_inputs.loc['Scenario_Diff_plot'].squeeze()).split(",")).str.strip().tolist()
if Scenario_Diff == ['nan']: Scenario_Diff = [""]

Mapping_folder = 'mapping_folder'

Region_Mapping = pd.read_csv(os.path.join(Mapping_folder, Marmot_user_defined_inputs.loc['Region_Mapping.csv_name'].to_string(index=False).strip()))
Region_Mapping = Region_Mapping.astype(str)

Reserve_Regions = pd.read_csv(os.path.join(Mapping_folder, Marmot_user_defined_inputs.loc['reserve_region_type.csv_name'].to_string(index=False).strip()))
gen_names = pd.read_csv(os.path.join(Mapping_folder, Marmot_user_defined_inputs.loc['gen_names.csv_name'].to_string(index=False).strip()))

AGG_BY = Marmot_user_defined_inputs.loc['AGG_BY'].squeeze().strip()
print("Aggregation selected: "+AGG_BY)
# Facet Grid Labels (Based on Scenarios)
zone_region_sublist = pd.Series(str(Marmot_user_defined_inputs.loc['zone_region_sublist'].squeeze()).split(",")).str.strip().tolist()
if zone_region_sublist != ['nan']:
    print("Only plotting " + AGG_BY + "s: " + str(zone_region_sublist))

ylabels = pd.Series(str(Marmot_user_defined_inputs.loc['Facet_ylabels'].squeeze()).split(",")).str.strip().tolist()
if ylabels == ['nan']: ylabels = [""]
xlabels = pd.Series(str(Marmot_user_defined_inputs.loc['Facet_xlabels'].squeeze()).split(",")).str.strip().tolist()
if xlabels == ['nan']: xlabels = [""]

figure_format = str(Marmot_user_defined_inputs.loc['Figure_Format'].squeeze()).strip()
if figure_format == 'nan':
    figure_format = 'png'

#===============================================================================
# Input and Output Directories
#===============================================================================

figure_folder = os.path.join(Marmot_Solutions_folder, Scenario_name, 'Figures_Output')
try:
    os.makedirs(figure_folder)
except FileExistsError:
    # directory already exists
    pass

hdf_out_folder = os.path.join(Marmot_Solutions_folder, Scenario_name,'Processed_HDF5_folder')
try:
    os.makedirs(hdf_out_folder)
except FileExistsError:
    # directory already exists
    pass

#===============================================================================
# Standard Generation Order
#===============================================================================

ordered_gen = pd.read_csv(os.path.join(Mapping_folder, 'ordered_gen.csv'),squeeze=True).str.strip().tolist()

pv_gen_cat = pd.read_csv(os.path.join(Mapping_folder, 'pv_gen_cat.csv'),squeeze=True).str.strip().tolist()

re_gen_cat = pd.read_csv(os.path.join(Mapping_folder, 're_gen_cat.csv'),squeeze=True).str.strip().tolist()

vre_gen_cat = pd.read_csv(os.path.join(Mapping_folder, 'vre_gen_cat.csv'),squeeze=True).str.strip().tolist()

thermal_gen_cat = pd.read_csv(os.path.join(Mapping_folder, 'thermal_gen_cat.csv'), squeeze = True).str.strip().tolist()

# facet_gen_cat = pd.read_csv(os.path.join(Mapping_folder, 'facet_gen_cat.csv'), squeeze = True).str.strip().tolist()

if set(gen_names["New"].unique()).issubset(ordered_gen) == False:
                    print("\n WARNING!! The new categories from the gen_names csv do not exist in ordered_gen \n")
                    print(set(gen_names["New"].unique()) - (set(ordered_gen)))

#===============================================================================
# Colours and styles
#===============================================================================

#ORIGINAL MARMOT COLORS
# PLEXOS_color_dict = {'Nuclear':'#B22222',
#                     'Coal':'#333333',
#                     'Gas-CC':'#6E8B3D',
#                     'Gas-CC CCS':'#396AB1',
#                     'Gas-CT':'#FFB6C1',
#                     'DualFuel':'#000080',
#                     'Oil-Gas-Steam':'#cd5c5c',
#                     'Hydro':'#ADD8E6',
#                     'Ocean':'#000080',
#                     'Geothermal':'#eedc82',
#                     'Biopower':'#008B00',
#                     'Wind':'#4F94CD',
#                     'CSP':'#EE7600',
#                     'PV':'#FFC125',
#                     'PV-Battery':'#CD950C',
#                     'Storage':'#dcdcdc',
#                     'Other': '#9370DB',
#                     'Net Imports':'#efbbff',
#                     'Curtailment': '#FF0000'}

#STANDARD SEAC COLORS (AS OF MARCH 9, 2020)
PLEXOS_color_dict = pd.read_csv(os.path.join(Mapping_folder, 'colour_dictionary.csv'))
PLEXOS_color_dict["Generator"] = PLEXOS_color_dict["Generator"].str.strip()
PLEXOS_color_dict["Colour"] = PLEXOS_color_dict["Colour"].str.strip()
PLEXOS_color_dict = PLEXOS_color_dict[['Generator','Colour']].set_index("Generator").to_dict()["Colour"]

color_list = ['#396AB1', '#CC2529','#3E9651','#ff7f00','#6B4C9A','#922428','#cab2d6', '#6a3d9a', '#fb9a99', '#b15928']

marker_style = ["^", "*", "o", "D", "x", "<", "P", "H", "8", "+"]

#===============================================================================
# Main
#===============================================================================

gen_names_dict=gen_names[['Original','New']].set_index("Original").to_dict()["New"]

# Instead of reading in pickle files, an instance of metadata is initialized with the appropriate parameters
# Methods within that class are used to retreive the data that was stored in pickle files

meta = MetaData(HDF5_folder_in, Region_Mapping)
zones = meta.zones()
regions = meta.regions()

# Zones_pkl = pd.read_pickle(os.path.join(Marmot_Solutions_folder, Scenario_name,"zones.pkl"))
# Regions_pkl = pd.read_pickle(os.path.join(Marmot_Solutions_folder, Scenario_name,'regions.pkl'))

if AGG_BY=="zone": 
    Zones = zones['name'].unique()
    # print(zones)
    # sys.exit()
    if zone_region_sublist != ['nan']:
        zsub = []
        for zone in zone_region_sublist:
            if zone in Zones:
                zsub.append(zone)
            else:
                print("metadata does not contain zone: " + zone + ", SKIPPING ZONE")
        Zones = zsub

elif Region_Mapping.empty==True:
    Zones = regions['region'].unique()
    # print(Zones)
    # sys.exit()
    if zone_region_sublist != ['nan']:
        zsub = []
        for region in zone_region_sublist:
            if region in Zones:
                zsub.append(region)
            else:
                print("metadata does not contain region: " + region + ", SKIPPING REGION")
        Zones = zsub
else:
    Region_Mapping = regions.merge(Region_Mapping, how='left', on='region')
    Zones = Region_Mapping[AGG_BY].unique()
    # print(Zones)
    # sys.exit()
    if zone_region_sublist != ['nan']:
        zsub = []
        for region in zone_region_sublist:
            if region in Zones:
                zsub.append(region)
            else:
                print("metadata does not contain region: " + region + ", SKIPPING REGION")
        Zones = zsub

# Zones = Region_Mapping[AGG_BY].unique()   #If formated H5 is from an older version of Marmot may need this line instead.

Reserve_Regions = Reserve_Regions["Reserve_Region"].unique()

# Filter for chosen figures to plot
if (len(sys.argv)-1) == 1: # If passed one argument (not including file name which is automatic)
    print("Will plot row " +(sys.argv[1])+" of Marmot plot select regardless of T/F.")
    Marmot_plot_select = Marmot_plot_select.iloc[int(sys.argv[1])-1].to_frame().T
else:
    Marmot_plot_select = Marmot_plot_select.loc[Marmot_plot_select["Plot Graph"] == True]
    

#%%
# Main loop to process each figure and pass data to functions
for index, row in Marmot_plot_select.iterrows():

    print("\n\n\n")
    print("Plot =  " + row["Figure Output Name"])
    
    module = row['Marmot Module']
    method = row['Method']
    
    facet = False
    if 'Facet' in row["Figure Output Name"]:
        facet = True
    
    argument_list =  [row.iloc[3], row.iloc[4], row.iloc[5], row.iloc[6],row.iloc[7], row.iloc[8],
        hdf_out_folder, Zones, AGG_BY, ordered_gen, PLEXOS_color_dict, Multi_Scenario,
        Scenario_Diff, Marmot_Solutions_folder, ylabels, xlabels, color_list, marker_style, gen_names_dict, pv_gen_cat,
        re_gen_cat, vre_gen_cat, Reserve_Regions, thermal_gen_cat,Region_Mapping,figure_folder, meta, facet]
    
##############################################################################

# Use run_plot_types to run any plotting module
    figures = os.path.join(figure_folder, AGG_BY + '_' + module)
    try:
        os.makedirs(figures)
    except FileExistsError:
        pass
    fig = plottypes(module, method, argument_list)
    Figure_Out = fig.runmplot()
     
    if 'Reserve' in row['Figure Type']:
        Zones = Reserve_Regions
        facet = False
    for zone_input in Zones:
        if isinstance(Figure_Out[zone_input], pd.DataFrame):
            if module == 'hydro' or method == 'gen_stack_all_periods':
                print('plots & data saved within module')
            else:
                print("Data missing for "+zone_input)
        else:
            if figure_format == 'png':
                try: 
                    Figure_Out[zone_input]["fig"].figure.savefig(os.path.join(figures, zone_input.replace('.','') + "_" + row["Figure Output Name"] + "_" + Scenario_name), dpi=600, bbox_inches='tight')
                except AttributeError:
                    Figure_Out[zone_input]["fig"].savefig(os.path.join(figures, zone_input.replace('.','') + "_" + row["Figure Output Name"] + "_" + Scenario_name), dpi=600, bbox_inches='tight')
            else:
                try:
                    Figure_Out[zone_input]["fig"].figure.savefig(os.path.join(figures, zone_input.replace('.','') + "_" + row["Figure Output Name"] + "_" + Scenario_name + '.' + figure_format), dpi=600, bbox_inches='tight')
                except AttributeError:
                    Figure_Out[zone_input]["fig"].savefig(os.path.join(figures, zone_input.replace('.','') + "_" + row["Figure Output Name"] + "_" + Scenario_name + '.' + figure_format), dpi=600, bbox_inches='tight')
            
            if Figure_Out[zone_input]['data_table'].empty:
                print(row["Figure Output Name"] + 'does not return a data table')
                continue
            
            if not facet:
                Figure_Out[zone_input]["data_table"].to_csv(os.path.join(figures, zone_input.replace('.','') + "_" + row["Figure Output Name"] + "_" + Scenario_name + ".csv"))
            else:
                tables_folder = os.path.join(figures, zone_input.replace('.','') + "_" + row["Figure Output Name"] + "_data_tables")
                try:
                     os.makedirs(tables_folder)
                except FileExistsError:
                     # directory already exists
                    pass
                for scenario in Multi_Scenario:
    #CSV output file name cannot exceed 75 characters!!  Scenario names may need to be shortened
                    s = zone_input.replace('.','') + "_" + scenario + ".csv"
                    Figure_Out[zone_input]["data_table"][scenario].to_csv(os.path.join(tables_folder, s))

###############################################################################
        mpl.pyplot.close('all')
 #%%
#subprocess.call("/usr/bin/Rscript --vanilla /Users/mschwarz/EXTREME EVENTS/PLEXOS results analysis/Marmot/run_html_output.R", shell=True)
