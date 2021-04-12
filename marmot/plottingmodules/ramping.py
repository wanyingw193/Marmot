# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 13:20:56 2019

This module creates bar plot of the total volume of generator starts in MW,GW,etc.


@author: dlevie
"""

import pandas as pd
import logging
import matplotlib as mpl
import marmot.plottingmodules.marmot_plot_functions as mfunc
import marmot.config.mconfig as mconfig


#===============================================================================
class mplot(object):

    def __init__(self, argument_dict):
        # iterate over items in argument_dict and set as properties of class
        # see key_list in Marmot_plot_main for list of properties
        for prop in argument_dict:
            self.__setattr__(prop, argument_dict[prop])

        self.logger = logging.getLogger('marmot_plot.'+__name__)
        self.x = mconfig.parser("figure_size","xdimension")
        self.y = mconfig.parser("figure_size","ydimension")
        self.y_axes_decimalpt = mconfig.parser("axes_options","y_axes_decimalpt")

    
    def capacity_started(self):
        outputs = {}
        gen_collection = {}
        cap_collection = {}
        check_input_data = []
        
        check_input_data.extend([mfunc.get_data(cap_collection,"generator_Installed_Capacity", self.Marmot_Solutions_folder, self.Scenarios)])
        check_input_data.extend([mfunc.get_data(gen_collection,"generator_Generation", self.Marmot_Solutions_folder, self.Scenarios)])
        
        # Checks if all data required by plot is available, if 1 in list required data is missing
        if 1 in check_input_data:
            outputs = mfunc.MissingInputData()
            return outputs
        
        for zone_input in self.Zones:
            self.logger.info(f"{self.AGG_BY} = {zone_input}")
            cap_started_all_scenarios = pd.DataFrame()

            for scenario in self.Scenarios:

                self.logger.info(f"Scenario = {str(scenario)}")

                Gen = gen_collection.get(scenario)
                
                try:
                    Gen = Gen.xs(zone_input,level = self.AGG_BY)
                except KeyError:
                    self.logger.warning(f"No installed capacity in : {zone_input}")
                    break
                
                Gen = Gen.reset_index()
                Gen.tech = Gen.tech.astype("category")
                Gen.tech.cat.set_categories(self.ordered_gen, inplace=True)
                # Gen = Gen.drop(columns = ['region'])
                Gen = Gen.rename(columns = {0:"Output (MWh)"})
                Gen = Gen[Gen['tech'].isin(self.thermal_gen_cat)]    #We are only interested in thermal starts/stops.

                Cap = cap_collection.get(scenario)
                Cap = Cap.xs(zone_input,level = self.AGG_BY)
                Cap = Cap.reset_index()
                Cap = Cap.drop(columns = ['timestamp','tech'])
                Cap = Cap.rename(columns = {0:"Installed Capacity (MW)"})
                Gen = pd.merge(Gen,Cap, on = 'gen_name')
                Gen.set_index('timestamp',inplace=True)
                
                if self.prop == 'Date Range':
                    self.logger.info(f"Plotting specific date range: \
                    {str(self.start_date)} to {str(self.end_date)}")
                    # sort_index added see https://github.com/pandas-dev/pandas/issues/35509
                    Gen = Gen.sort_index()[self.start_date : self.end_date]

                tech_names = Gen['tech'].unique()
                Cap_started = pd.DataFrame(columns = tech_names,index = [scenario])

                for tech_name in tech_names:
                    stt = Gen.loc[Gen['tech'] == tech_name]

                    gen_names = stt['gen_name'].unique()

                    cap_started = 0


                    for gen in gen_names:
                        sgt = stt.loc[stt['gen_name'] == gen]
                        if any(sgt["Output (MWh)"] == 0) and not all(sgt["Output (MWh)"] == 0):   #Check that this generator has some, but not all, uncommited hours.
                            #print('Couting starts for: ' + gen)
                            for idx in range(len(sgt['Output (MWh)']) - 1):
                                    if sgt["Output (MWh)"].iloc[idx] == 0 and not sgt["Output (MWh)"].iloc[idx + 1] == 0:
                                        cap_started = cap_started + sgt["Installed Capacity (MW)"].iloc[idx]
                                      # print('started on '+ timestamp)
                                    # if sgt[0].iloc[idx] == 0 and not idx == 0 and not sgt[0].iloc[idx - 1] == 0:
                                    #     stops = stops + 1

                    Cap_started[tech_name] = cap_started

                cap_started_all_scenarios = cap_started_all_scenarios.append(Cap_started)


                # import time
                    # start = time.time()
                    # for gen in gen_names:
                    #     sgt = stt.loc[stt['gen_name'] == gen]

                    #     if any(sgt[0] == 0) and not all(sgt[0] == 0):   #Check that this generator has some, but not all, uncommited hours.
                    #         zeros = sgt.loc[sgt[0] == 0]

                    #         print('Couting starts and stops for: ' + gen)
                    #         for idx in range(len(zeros['timestamp']) - 1):
                    #                if not zeros['timestamp'].iloc[idx + 1] == pd.Timedelta(1,'h'):
                    #                    starts = starts + 1
                    #                   # print('started on '+ timestamp)
                    #                if not zeros['timestamp'].iloc[idx - 1] == pd.Timedelta(1,'h'):
                    #                    stops = stops + 1

                    # starts_and_stops = [starts,stops]
                    # counts[tech_name] = starts_and_stops


                # end = time.time()
                # elapsed = end - start
                # print('Method 2 (first making a data frame with only 0s, then checking if timestamps > 1 hour) took ' + str(elapsed) + ' seconds')

            if cap_started_all_scenarios.empty == True:
                out = mfunc.MissingZoneData()
                outputs[zone_input] = out
                continue
            
            unitconversion = mfunc.capacity_energy_unitconversion(cap_started_all_scenarios.values.max())
            
            cap_started_all_scenarios = cap_started_all_scenarios/unitconversion['divisor'] 
            Data_Table_Out = cap_started_all_scenarios.T.add_suffix(f" ({unitconversion['units']}-starts)")
            
            cap_started_all_scenarios.index = cap_started_all_scenarios.index.str.replace('_',' ')
            cap_started_all_scenarios.columns = cap_started_all_scenarios.columns.str.wrap(10, break_long_words=False)
            
            fig1 = cap_started_all_scenarios.T.plot.bar(stacked = False, figsize=(self.x,self.y), rot=0,
                                 color = self.color_list,edgecolor='black', linewidth='0.1')

            fig1.spines['right'].set_visible(False)
            fig1.spines['top'].set_visible(False)
            fig1.set_ylabel(f"Capacity Started ({unitconversion['units']}-starts)",  color='black', rotation='vertical')
            fig1.tick_params(axis='y', which='major', length=5, width=1)
            fig1.tick_params(axis='x', which='major', length=5, width=1)
            fig1.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            fig1.legend(loc='lower left',bbox_to_anchor=(1,0),
                          facecolor='inherit', frameon=True)

            outputs[zone_input] = {'fig': fig1, 'data_table': Data_Table_Out}
        return outputs

##############################################################################


    def count_ramps(self):
        outputs = {}
        gen_collection = {}
        cap_collection = {}
        check_input_data = []
        
        check_input_data.extend([mfunc.get_data(cap_collection,"generator_Installed_Capacity", self.Marmot_Solutions_folder, self.Scenarios)])
        check_input_data.extend([mfunc.get_data(gen_collection,"generator_Generation", self.Marmot_Solutions_folder, self.Scenarios)])
        
        # Checks if all data required by plot is available, if 1 in list required data is missing
        if 1 in check_input_data:
            outputs = mfunc.MissingInputData()
            return outputs
        
        for zone_input in self.Zones:
            self.logger.info(f"Zone =  {zone_input}")
            cap_started_chunk = []

            for scenario in self.Scenarios:

                self.logger.info(f"Scenario = {str(scenario)}")
                Gen = gen_collection.get(scenario)
                Gen = Gen.xs(zone_input,level = self.AGG_BY)

                Gen = Gen.reset_index()
                Gen.tech = Gen.tech.astype("category")
                Gen.tech.cat.set_categories(self.ordered_gen, inplace=True)
                Gen = Gen.rename(columns = {0:"Output (MWh)"})
                Gen = Gen[['timestamp','gen_name','tech','Output (MWh)']]
                Gen = Gen[Gen['tech'].isin(self.thermal_gen_cat)]    #We are only interested in thermal starts/stops.tops.

                Cap = cap_collection.get(scenario)
                Cap = Cap.xs(zone_input,level = self.AGG_BY)
                Cap = Cap.reset_index()
                Cap = Cap.rename(columns = {0:"Installed Capacity (MW)"})
                Cap = Cap[['gen_name','Installed Capacity (MW)']]
                Gen = pd.merge(Gen,Cap, on = ['gen_name'])
                Gen.index = Gen.timestamp
                Gen = Gen.drop(columns = ['timestamp'])

                # Min = pd.read_hdf(os.path.join(Marmot_Solutions_folder, scenario,"Processed_HDF5_folder", scenario + "_formatted.h5"),"generator_Hours_at_Minimum")
                # Min = Min.xs(zone_input, level = AGG_BY)

                if self.prop == 'Date Range':
                    self.logger.info(f"Plotting specific date range: \
                    {str(self.start_date)} to {str(self.end_date)}")
                    Gen = Gen[self.start_date : self.end_date]

                tech_names = Gen['tech'].unique()
                ramp_counts = pd.DataFrame(columns = tech_names,index = [scenario])

                for tech_name in tech_names:
                    stt = Gen.loc[Gen['tech'] == tech_name]

                    gen_names = stt['gen_name'].unique()

                    up_ramps = 0

                    for gen in gen_names:
                        sgt = stt.loc[stt['gen_name'] == gen]
                        if any(sgt["Output (MWh)"] == 0) and not all(sgt["Output (MWh)"] == 0):   #Check that this generator has some, but not all, uncommited hours.
                            #print('Couting starts for: ' + gen)
                            for idx in range(len(sgt['Output (MWh)']) - 1):
                                    if sgt["Output (MWh)"].iloc[idx] == 0 and not sgt["Output (MWh)"].iloc[idx + 1] == 0:
                                        up_ramps = up_ramps + sgt["Installed Capacity (MW)"].iloc[idx]
                                      # print('started on '+ timestamp)
                                    # if sgt[0].iloc[idx] == 0 and not idx == 0 and not sgt[0].iloc[idx - 1] == 0:
                                    #     stops = stops + 1

                    ramp_counts[tech_name] = up_ramps

                cap_started_chunk.append(ramp_counts)
            
            cap_started_all_scenarios = pd.concat(cap_started_chunk)
            
            if cap_started_all_scenarios.empty == True:
                out = mfunc.MissingZoneData()
                outputs[zone_input] = out
                continue
            
            cap_started_all_scenarios.index = cap_started_all_scenarios.index.str.replace('_',' ')

            unitconversion = mfunc.capacity_energy_unitconversion(cap_started_all_scenarios.values.max())
            
            cap_started_all_scenarios = cap_started_all_scenarios/unitconversion['divisor'] 
            Data_Table_Out = cap_started_all_scenarios.T.add_suffix(f" ({unitconversion['units']}-starts)")
            
            fig2 = cap_started_all_scenarios.T.plot.bar(stacked = False, figsize=(self.x,self.y), rot=0,
                                  color = self.color_list,edgecolor='black', linewidth='0.1')

            fig2.spines['right'].set_visible(False)
            fig2.spines['top'].set_visible(False)
            fig2.set_ylabel(f"Capacity Started ({unitconversion['units']}-starts)",  color='black', rotation='vertical')
            fig2.tick_params(axis='y', which='major', length=5, width=1)
            fig2.tick_params(axis='x', which='major', length=5, width=1)
            fig2.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, p: format(x, f',.{self.y_axes_decimalpt}f')))
            fig2.legend(loc='lower left',bbox_to_anchor=(1,0),
                          facecolor='inherit', frameon=True)

            outputs[zone_input] = {'fig': fig2, 'data_table': Data_Table_Out}
        return outputs
