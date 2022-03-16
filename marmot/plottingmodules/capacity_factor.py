# -*- coding: utf-8 -*-
"""Generator capacity factor plots .

This module contain methods that are related to the capacity factor 
of generators and average output plots 
"""

import logging
import numpy as np
import pandas as pd

import marmot.utils.mconfig as mconfig

from marmot.plottingmodules.plotutils.plot_data_helper import PlotDataHelper
from marmot.plottingmodules.plotutils.plot_library import PlotLibrary
from marmot.plottingmodules.plotutils.plot_exceptions import (MissingInputData, MissingZoneData)

logger = logging.getLogger('plotter.'+__name__)
plot_data_settings = mconfig.parser("plot_data")

class MPlot(PlotDataHelper):
    """capacity_factor MPlot class.

    All the plotting modules use this same class name.
    This class contains plotting methods that are grouped based on the
    current module name.
    
    The capacity_factor.py module contain methods that are
    related to the capacity factor of generators. 

    MPlot inherits from the PlotDataHelper class to assist in creating figures.
    """

    def __init__(self, argument_dict: dict):
        """
        Args:
            argument_dict (dict): Dictionary containing all
                arguments passed from MarmotPlot.
        """
        # iterate over items in argument_dict and set as properties of class
        # see key_list in Marmot_plot_main for list of properties
        for prop in argument_dict:
            self.__setattr__(prop, argument_dict[prop])

        # Instantiation of MPlotHelperFunctions
        super().__init__(self.Marmot_Solutions_folder, self.AGG_BY, self.ordered_gen, 
                    self.PLEXOS_color_dict, self.Scenarios, self.ylabels, 
                    self.xlabels, self.gen_names_dict, self.TECH_SUBSET, 
                    Region_Mapping=self.Region_Mapping) 
        
        self.x = mconfig.parser("figure_size","xdimension")
        self.y = mconfig.parser("figure_size","ydimension")
        
    def avg_output_when_committed(self,
                                  start_date_range: str = None, 
                                  end_date_range: str = None, 
                                  barplot_groupby: str = 'Scenario', **_):
        """Creates barplots of the percentage average generation output when committed by technology type. 

        Each scenario is plotted by a different colored grouped bar. 

        Args:
            start_date_range (str, optional): Defines a start date at which to represent data from. 
                Defaults to None.
            end_date_range (str, optional): Defines a end date at which to represent data to.
                Defaults to None.

        Returns:
            dict: dictionary containing the created plot and its data table.
        """
        outputs : dict = {}
        
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True,"generator_Generation",self.Scenarios),
                      (True,"generator_Installed_Capacity",self.Scenarios)]
        
        # Runs get_formatted_data within PlotDataHelper to populate PlotDataHelper dictionary  
        # with all required properties, returns a 1 if required data is missing
        check_input_data = self.get_formatted_data(properties)

        if 1 in check_input_data:
            return MissingInputData()
        
        for zone_input in self.Zones:
            CF_all_scenarios = pd.DataFrame()
            logger.info(f"{self.AGG_BY} = {zone_input}")

            for scenario in self.Scenarios:
                logger.info(f"Scenario = {str(scenario)}")
                
                Gen : pd.DataFrame = self["generator_Generation"].get(scenario)
                try:
                    Gen = Gen.xs(zone_input, level=self.AGG_BY)
                except KeyError:
                    logger.warning(f'No data in {zone_input}')
                    continue
                Gen = Gen.reset_index()
                Gen = self.rename_gen_techs(Gen)
                Gen.tech = Gen.tech.astype("category")
                Gen.tech.cat.set_categories(self.ordered_gen, inplace=True)
                Gen = Gen[Gen['tech'].isin(self.thermal_gen_cat)]
                Gen.set_index('timestamp',inplace=True)
                Gen = Gen.rename(columns={0: "Output (MWh)"})
                
                Cap : pd.DataFrame = self["generator_Installed_Capacity"].get(scenario)
                Cap = Cap.xs(zone_input,level = self.AGG_BY)
                Cap = Cap.rename(columns={0: "Installed Capacity (MW)"})

                if pd.notna(start_date_range):
                    Cap, Gen = self.set_timestamp_date_range([Cap, Gen],
                                    start_date_range, end_date_range)
                    if Gen.empty is True:
                        logger.warning('No data in selected Date Range')
                        continue
                
                Gen['year'] = Gen.index.year.astype(str)
                Cap['year'] = Cap.index.get_level_values('timestamp').year.astype(str)
                Gen = Gen.reset_index()
                Gen = pd.merge(Gen, Cap, on=['gen_name', 'year'])
                Gen.set_index('timestamp',inplace=True)


                if barplot_groupby == 'Year-Scenario':
                    Gen['Scenario'] = \
                         Gen.index.year.astype(str) + f'_{scenario}'
                else:
                    Gen['Scenario'] = scenario

                year_scen = Gen['Scenario'].unique()
                for scen in year_scen:
                    Gen_scen = Gen.loc[Gen['Scenario'] == scen]
                    # Calculate CF individually for each plant, 
                    # since we need to take out all zero rows.
                    tech_names = Gen_scen.sort_values(["tech"])['tech'].unique()
                    CF = pd.DataFrame(columns=tech_names, index=[scen])
                    for tech_name in tech_names:
                        stt = Gen_scen.loc[Gen_scen['tech'] == tech_name]
                        if not all(stt['Output (MWh)'] == 0):

                            gen_names = stt['gen_name'].unique()
                            cfs = []
                            caps = []
                            for gen in gen_names:
                                sgt = stt.loc[stt['gen_name'] == gen]
                                if not all(sgt['Output (MWh)'] == 0):
                                    # Calculates interval step to correct for MWh of generation
                                    time_delta = sgt.index[1] - sgt.index[0]
                                    duration = sgt.index[len(sgt)-1] - sgt.index[0]
                                    duration = duration + time_delta #Account for last timestep.
                                    # Finds intervals in 60 minute period
                                    interval_count = 60/(time_delta/np.timedelta64(1, 'm'))
                                    #Get length of time series in hours for CF calculation.
                                    duration_hours = min(8760, duration/np.timedelta64(1, 'h'))
                                    #Remove time intervals when output is zero.
                                    sgt = sgt[sgt['Output (MWh)'] != 0] 
                                    total_gen = sgt['Output (MWh)'].sum()/interval_count
                                    cap = sgt['Installed Capacity (MW)'].mean()
                                    #Calculate CF
                                    cf = total_gen/(cap * duration_hours)
                                    cfs.append(cf)
                                    caps.append(cap)

                            #Find average "CF" (average output when committed) 
                            # for this technology, weighted by capacity.
                            cf = np.average(cfs, weights=caps)
                            CF[tech_name] = cf
                    CF_all_scenarios = CF_all_scenarios.append(CF)
                        
            if CF_all_scenarios.empty == True:
                outputs[zone_input] = MissingZoneData()
                continue
            
            Data_Table_Out = CF_all_scenarios.T

            mplt = PlotLibrary()
            fig, ax = mplt.get_figure()
            
            mplt.barplot(CF_all_scenarios.T, color=self.color_list, 
                                custom_tick_labels=list(CF_all_scenarios.columns),
                                ytick_major_fmt='percent')

            ax.set_ylabel('Average Output When Committed',  color='black', rotation='vertical')
            
            if plot_data_settings["plot_title_as_region"]:
                mplt.add_main_title(zone_input)
            # Add legend
            mplt.add_legend()
            
            outputs[zone_input] = {'fig': fig, 'data_table': Data_Table_Out}
        return outputs

    def cf(self, start_date_range: str = None, 
           end_date_range: str = None, 
           barplot_groupby: str = 'Scenario', **_):
        """Creates barplots of generator capacity factors by technology type. 

        Each scenario is plotted by a different colored grouped bar. 

        Args:
            start_date_range (str, optional): Defines a start date at which to represent data from. 
                Defaults to None.
            end_date_range (str, optional): Defines a end date at which to represent data to.
                Defaults to None.

        Returns:
            dict: dictionary containing the created plot and its data table.
        """
        
        outputs : dict = {}
        
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True,"generator_Generation",self.Scenarios),
                      (True,"generator_Installed_Capacity",self.Scenarios)]
        
        # Runs get_formatted_data within PlotDataHelper to populate PlotDataHelper dictionary  
        # with all required properties, returns a 1 if required data is missing
        check_input_data = self.get_formatted_data(properties)

        if 1 in check_input_data:
            return MissingInputData()
        
        for zone_input in self.Zones:
            cf_scen_chunks = []
            logger.info(f"{self.AGG_BY} = {zone_input}")

            for scenario in self.Scenarios:

                logger.info(f"Scenario = {str(scenario)}")
                Gen = self["generator_Generation"].get(scenario)
                try: #Check for regions missing all generation.
                    Gen = Gen.xs(zone_input,level = self.AGG_BY)
                except KeyError:
                        logger.warning(f'No data in {zone_input}')
                        continue
                Gen = self.df_process_gen_inputs(Gen)
                
                Cap = self["generator_Installed_Capacity"].get(scenario)
                Cap = Cap.xs(zone_input,level = self.AGG_BY)
                Cap = self.df_process_gen_inputs(Cap)
                
                if pd.notna(start_date_range):
                    Cap, Gen = self.set_timestamp_date_range([Cap, Gen],
                                    start_date_range, end_date_range)
                    if Gen.empty is True:
                        logger.warning('No data in selected Date Range')
                        continue

                # Calculates interval step to correct for MWh of generation
                time_delta = Gen.index[1] - Gen.index[0]
                duration = Gen.index[len(Gen)-1] - Gen.index[0]
                duration = duration + time_delta #Account for last timestep.
                # Finds intervals in 60 minute period
                interval_count : int = 60/(time_delta/np.timedelta64(1, 'm'))
                #Get length of time series in hours for CF calculation.
                duration_hours : int = min(8760, duration/np.timedelta64(1,'h'))

                Gen = Gen/interval_count

                Total_Gen = self.year_scenario_grouper(Gen, scenario, 
                                                groupby=barplot_groupby).sum()
                Cap = self.year_scenario_grouper(Cap, scenario, 
                                                groupby=barplot_groupby).sum()
                #Calculate CF
                CF = Total_Gen/(Cap * duration_hours)
                cf_scen_chunks.append(CF)

            CF_all_scenarios = pd.concat(cf_scen_chunks, axis=0, sort=False).T
            CF_all_scenarios = CF_all_scenarios.fillna(0, axis = 0)

            if CF_all_scenarios.empty == True:
                outputs[zone_input] = MissingZoneData()
                continue
            
            Data_Table_Out = CF_all_scenarios.T
            
            mplt = PlotLibrary(figsize=(self.x*1.5, self.y*1.5))
            fig, ax = mplt.get_figure()

            mplt.barplot(CF_all_scenarios, color=self.color_list,
                         ytick_major_fmt='percent')

            ax.set_ylabel('Capacity Factor',  color='black', rotation='vertical')
            # Add legend
            mplt.add_legend()
            # Add title
            if plot_data_settings["plot_title_as_region"]:
                mplt.add_main_title(zone_input)
            outputs[zone_input] = {'fig': fig, 'data_table': Data_Table_Out}

        return outputs


    def time_at_min_gen(self, start_date_range: str = None, 
                        end_date_range: str = None,
                        barplot_groupby: str = 'Scenario', **_):
        """Creates barplots of generator percentage time at min-gen by technology type. 

        Each scenario is plotted by a different colored grouped bar. 

        Args:
            start_date_range (str, optional): Defines a start date at which to represent data from. 
                Defaults to None.
            end_date_range (str, optional): Defines a end date at which to represent data to.
                Defaults to None.

        Returns:
            dict: dictionary containing the created plot and its data table.
        """
        
        outputs : dict = {}
        
        # List of properties needed by the plot, properties are a set of tuples and contain 3 parts:
        # required True/False, property name and scenarios required, scenarios must be a list.
        properties = [(True,"generator_Generation",self.Scenarios),
                      (True,"generator_Installed_Capacity",self.Scenarios),
                      (True,"generator_Hours_at_Minimum",self.Scenarios)]
        
        # Runs get_formatted_data within PlotDataHelper to populate PlotDataHelper dictionary  
        # with all required properties, returns a 1 if required data is missing
        check_input_data = self.get_formatted_data(properties)

        if 1 in check_input_data:
            return MissingInputData()
        
        for zone_input in self.Zones:
            logger.info(f"{self.AGG_BY} = {zone_input}")

            time_at_min = pd.DataFrame()

            for scenario in self.Scenarios:
                logger.info(f"Scenario = {str(scenario)}")

                Min = self["generator_Hours_at_Minimum"].get(scenario)
                try:
                    Min = Min.xs(zone_input,level = self.AGG_BY)
                except KeyError:
                    continue
                Gen = self["generator_Generation"].get(scenario)
                try: #Check for regions missing all generation.
                    Gen = Gen.xs(zone_input,level = self.AGG_BY)
                except KeyError:
                        logger.warning(f'No data in {zone_input}')
                        continue
                Cap = self["generator_Installed_Capacity"].get(scenario)
                Cap = Cap.xs(zone_input,level = self.AGG_BY)

                if pd.notna(start_date_range):
                    Min, Gen, Cap = self.set_timestamp_date_range([Min, Gen, Cap],
                                    start_date_range, end_date_range)
                    if Gen.empty is True:
                        logger.warning('No data in selected Date Range')
                        continue

                Min = Min.reset_index()
                Min = Min.set_index('gen_name')
                Min = Min.rename(columns = {0:"Hours at Minimum"})

                Gen = Gen.reset_index()
                Gen.tech = Gen.tech.astype("category")
                Gen.tech.cat.set_categories(self.ordered_gen, inplace=True)
                Gen = Gen.rename(columns = {0:"Output (MWh)"})
                Gen = Gen[~Gen['tech'].isin(self.vre_gen_cat)]
                Gen.index = Gen.timestamp

                Caps = Cap.groupby('gen_name').mean()
                Caps.reset_index()
                Caps = Caps.rename(columns = {0: 'Installed Capacity (MW)'})
                Min = pd.merge(Min,Caps, on = 'gen_name')

                #Find how many hours each generator was operating, for the denominator of the % time at min gen.
                #So remove all zero rows.
                Gen = Gen.loc[Gen['Output (MWh)'] != 0]
                online_gens = Gen.gen_name.unique()
                Min = Min.loc[online_gens]
                Min['hours_online'] = Gen.groupby('gen_name')['Output (MWh)'].count()
                Min['fraction_at_min'] = Min['Hours at Minimum'] / Min.hours_online

                tech_names = Min.tech.unique()
                time_at_min_individ = pd.DataFrame(columns = tech_names, index = [scenario])
                for tech_name in tech_names:
                    stt = Min.loc[Min['tech'] == tech_name]
                    wgts = stt['Installed Capacity (MW)']
                    if wgts.sum() == 0:
                        wgts = pd.Series([1] * len(stt))
                    output = np.average(stt.fraction_at_min,weights = wgts)
                    time_at_min_individ[tech_name] = output

                time_at_min = time_at_min.append(time_at_min_individ)

            if time_at_min.empty == True:
                outputs[zone_input] = MissingZoneData()
                continue
            
            Data_Table_Out = time_at_min.T
            
            mplt = PlotLibrary(figsize=(self.x*1.5, self.y*1.5))
            fig, ax = mplt.get_figure()

            mplt.barplot(time_at_min.T, color=self.color_list, 
                         custom_tick_labels=list(time_at_min.columns),
                         ytick_major_fmt='percent')
            
            ax.set_ylabel('Percentage of time online at minimum generation', 
                          color='black', rotation='vertical')
            # Add legend
            mplt.add_legend()
            # Add title
            if plot_data_settings["plot_title_as_region"]:
                mplt.add_main_title(zone_input)

            outputs[zone_input] = {'fig': fig, 'data_table': Data_Table_Out}
        return outputs
