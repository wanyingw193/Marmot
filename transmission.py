# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 10:34:48 2019

This code creates generation stack plots and is called from Marmot_plot_main.py

@author: dlevie
"""

import os
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
import numpy as np



#===============================================================================

class mplot(object):
    def __init__(self,argument_list):

        self.prop = argument_list[0]
        self.start = argument_list[1]
        self.end = argument_list[2]
        self.timezone = argument_list[3]
        self.start_date = argument_list[4]
        self.end_date = argument_list[5]
        self.hdf_out_folder = argument_list[6]
        self.zone_input =argument_list[7]
        self.AGG_BY = argument_list[8]
        self.ordered_gen = argument_list[9]
        self.PLEXOS_color_dict = argument_list[10]
        self.Multi_Scenario = argument_list[11]
        self.Scenario_Diff = argument_list[12]
        self.PLEXOS_Scenarios = argument_list[13]
        self.ylabels = argument_list[14]
        self.xlabels = argument_list[15]
        self.color_list = argument_list[16]
        self.gen_names_dict = argument_list[18]
        self.re_gen_cat = argument_list[20]
        self.Region_Mapping = argument_list[24]



    def net_export(self):

        print("Zone = " + self.zone_input)

        region2zone_mapping = pd.read_csv('/home/mschwarz/PLEXOS results analysis/Marmot/mapping_folder/region2zone.csv')
        region2zone_mapping = region2zone_mapping.set_index('region').to_dict()['Zones']
        Net_Export_all_scenarios = pd.DataFrame()

        for scenario in self.Multi_Scenario:

            print("Scenario = " + str(scenario))

            Net_Export_read = pd.read_hdf(os.path.join(self.PLEXOS_Scenarios,scenario, 'Processed_HDF5_folder', scenario + '_formatted.h5'),'region_Net_Interchange')

            Net_Export = Net_Export_read.xs(self.zone_input, level = self.AGG_BY)
            Net_Export = Net_Export.reset_index()
            Net_Export = Net_Export.groupby(["timestamp"]).sum()
            Net_Export.columns = [scenario]

            if self.prop == 'Date Range':
                print("Plotting specific date range:")
                print(str(self.start_date) + '  to  ' + str(self.end_date))

                Net_Export = Net_Export[self.start_date : self.end_date]

            Net_Export_all_scenarios = pd.concat([Net_Export_all_scenarios,Net_Export], axis = 1)

        # Data table of values to return to main program
        Data_Table_Out = Net_Export_all_scenarios

        #Make scenario/color dictionary.
        scenario_color_dict = {}
        for idx,column in enumerate(Net_Export_all_scenarios.columns):
            dictionary = {column : self.color_list[idx]}
            scenario_color_dict.update(dictionary)

        fig1, ax = plt.subplots(figsize=(9,6))
        for idx,column in enumerate(Net_Export_all_scenarios.columns):
            ax.plot(Net_Export_all_scenarios.index.values,Net_Export_all_scenarios[column], linewidth=2, color = scenario_color_dict.get(column,'#333333'),label=column)


        ax.set_ylabel('Net exports (MW)',  color='black', rotation='vertical')
        ax.set_xlabel('Date ' + '(' + self.timezone + ')',  color='black', rotation='horizontal')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.tick_params(axis='y', which='major', length=5, width=1)
        ax.tick_params(axis='x', which='major', length=5, width=1)
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.margins(x=0.01)

        locator = mdates.AutoDateLocator(minticks=6, maxticks=12)
        formatter = mdates.ConciseDateFormatter(locator)
        formatter.formats[2] = '%d\n %b'
        formatter.zero_formats[1] = '%b\n %Y'
        formatter.zero_formats[2] = '%d\n %b'
        formatter.zero_formats[3] = '%H:%M\n %d-%b'
        formatter.offset_formats[3] = '%b %Y'
        formatter.show_offset = False
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        handles, labels = ax.get_legend_handles_labels()

        #Legend 1
        leg1 = ax.legend(reversed(handles), reversed(labels), loc='best',facecolor='inherit', frameon=True)

        # Manually add the first legend back
        ax.add_artist(leg1)

        return {'fig': fig1, 'data_table': Data_Table_Out}


    def line_util(self):          #Duration curve of individual line utilization for all hours

        Flow_Collection = {}        # Create Dictionary to hold Datframes for each scenario

        for scenario in self.Multi_Scenario:
            Flow_Collection[scenario] = pd.read_hdf(os.path.join(self.PLEXOS_Scenarios, scenario,"Processed_HDF5_folder", scenario+ "_formatted.h5"),"line_Flow")



        print("Line analysis done only once (not per zone).")

        fig3, ax3 = plt.subplots(len(self.Multi_Scenario),figsize=(9,6)) # Set up subplots for all scenarios

        n=0 #Counter for scenario subplots

        for scenario in self.Multi_Scenario:

            print("Scenario = " + str(scenario))

            Flow = Flow_Collection.get(scenario)

            if (self.prop!=self.prop)==False: # This checks for a nan in string. If no scenario selected, do nothing.
                print("Line category = "+str(self.prop))
                line_relations=pd.read_pickle(os.path.join(self.PLEXOS_Scenarios,scenario,"line_relations.pkl")).rename(columns={"name":"line_name"}).set_index(["line_name"])
                Flow=pd.merge(Flow,line_relations,left_index=True,right_index=True)
                Flow=Flow[Flow["category"]==self.prop]
                Flow=Flow.drop('category',axis=1)

            AbsMaxFlow = Flow.abs().groupby(["line_name"]).max()
            Flow = pd.merge(Flow,AbsMaxFlow,left_index=True, right_index=True)
            del AbsMaxFlow
            Flow['Util']=Flow['0_x'].abs()/Flow['0_y']

            for line in Flow.index.get_level_values(level='line_name').unique() :
                duration_curve = Flow.xs(line,level="line_name").sort_values(by='Util',ascending=False).reset_index()

                if len(self.Multi_Scenario)>1:
                    ax3[n].plot(duration_curve['Util'])
                    ax3[n].set_ylabel(scenario+' Line Utilization '+'\n'+'Line cateogory: '+str(self.prop),  color='black', rotation='vertical')
                    ax3[n].set_xlabel('Intervals',  color='black', rotation='horizontal')
                    ax3[n].spines['right'].set_visible(False)
                    ax3[n].spines['top'].set_visible(False)
                    plt.ylim((0,1.1))

                else:
                    ax3.plot(duration_curve['Util'])
                    ax3.set_ylabel(scenario+' Line Utilization '+'\n'+'Line cateogory: '+str(self.prop),  color='black', rotation='vertical')
                    ax3.set_xlabel('Intervals',  color='black', rotation='horizontal')
                    ax3.spines['right'].set_visible(False)
                    ax3.spines['top'].set_visible(False)
                    plt.ylim((0,1.1))

                del duration_curve
            del Flow


            n=n+1
        #end scenario loop

        return {'fig': fig3}



    def line_hist(self):                #Histograms of individual line utilization factor for entire year
        Flow_Collection = {}            # Create Dictionary to hold Datframes for each scenario


        for scenario in self.Multi_Scenario:
            Flow_Collection[scenario] = pd.read_hdf(os.path.join(self.PLEXOS_Scenarios, scenario,"Processed_HDF5_folder", scenario+ "_formatted.h5"),"line_Flow")

        print("Line analysis done only once (not per zone).")

        fig3, ax3 = plt.subplots(len(self.Multi_Scenario),figsize=(9,6)) # Set up subplots for all scenarios

        n=0 #Counter for scenario subplots

        for scenario in self.Multi_Scenario:

            print("Scenario = " + str(scenario))
            Flow = Flow_Collection.get(scenario)

            if (self.prop!=self.prop)==False: # This checks for a nan in string. If no category selected, do nothing.
                print("Line category = "+str(self.prop))
                line_relations=pd.read_pickle(os.path.join(self.PLEXOS_Scenarios,scenario,"line_relations.pkl")).rename(columns={"name":"line_name"}).set_index(["line_name"])
                Flow=pd.merge(Flow,line_relations,left_index=True,right_index=True)
                Flow=Flow[Flow["category"]==self.prop]
                Flow=Flow.drop('category',axis=1)

            AbsMaxFlow = Flow.abs().groupby(["line_name"]).max()
            Flow = pd.merge(Flow,AbsMaxFlow,left_index=True, right_index=True)
            Flow['Util']=Flow['0_x'].abs()/Flow['0_y']
            Annual_Util=Flow['Util'].groupby(["line_name"]).mean()
            del Flow

            if len(self.Multi_Scenario)>1:
                ax3[n].hist(Annual_Util.replace([np.inf,np.nan]),bins=20,range=(0,1),label=scenario)
                ax3[n].set_ylabel(scenario+' Number of lines '+'\n'+'Line cateogory: '+str(self.prop),  color='black', rotation='vertical')
                ax3[n].set_xlabel('Utilization',  color='black', rotation='horizontal')
                ax3[n].spines['right'].set_visible(False)
                ax3[n].spines['top'].set_visible(False)

            else:
                ax3.hist(Annual_Util.replace([np.inf,np.nan]),bins=20,range=(0,1),label=scenario)
                ax3.set_ylabel(scenario+' Number of lines '+'\n'+'Line cateogory: '+str(self.prop),  color='black', rotation='vertical')
                ax3.set_xlabel('Utilization',  color='black', rotation='horizontal')
                ax3.spines['right'].set_visible(False)
                ax3.spines['top'].set_visible(False)

            del Annual_Util
            n=n+1
        #end scenario loop

        return {'fig': fig3}

    def zone_zone_interchange(self):
        print('Zone = ' + str(self.zone_input))

        xdimension=len(self.xlabels)
        if xdimension == 0:
            xdimension = 1
        ydimension=len(self.ylabels)
        if ydimension == 0:
            ydimension = 1
        grid_size = xdimension*ydimension
        fig4, axs = plt.subplots(ydimension,xdimension, figsize=((8*xdimension),(4*ydimension)), sharey=True)
        plt.subplots_adjust(wspace=0.05, hspace=0.2)
        axs = axs.ravel()
        i=0

        region2zone_mapping = pd.read_csv('/home/mschwarz/PLEXOS results analysis/Marmot/mapping_folder/region2zone.csv')
        region2zone_mapping = region2zone_mapping.set_index('region').to_dict()['Zones']

        for scenario in self.Multi_Scenario:
            zz_int = pd.read_hdf(os.path.join(self.PLEXOS_Scenarios,scenario,"Processed_HDF5_folder", scenario + "_formatted.h5"),"region_regions_Net_Interchange")
            zz_int = zz_int.reset_index()
            zz_int['parent'] = zz_int['parent'].map(region2zone_mapping)
            zz_int['child']  = zz_int['child'].map(region2zone_mapping)
            zz_int_agg = zz_int.groupby(['timestamp','parent','child'],as_index=True).sum()
            zz_int_agg.rename(columns = {0:'Flow (MW)'}, inplace = True)
            zz_int_agg = zz_int_agg.unstack(level = 'child')
            zz_int_agg = zz_int_agg.droplevel(level = 0, axis = 1)
            zz_int_agg = zz_int_agg.stack(level = 'child')
            zz_int_agg = zz_int_agg.reset_index()

            one_zone = zz_int_agg[zz_int_agg['parent'] == self.zone_input]    #Select only this particular zone.
            one_zone = one_zone.pivot(index = 'timestamp',columns = 'child',values = 0)
            one_zone = one_zone.loc[:,(one_zone != 0).any(axis = 0)] #Remove all 0 columns (uninteresting).
            for column in one_zone.columns:
                axs[i].plot(one_zone.index.values,one_zone[column], linewidth=2, label=column)

            axs[i].spines['right'].set_visible(False)
            axs[i].spines['top'].set_visible(False)
            axs[i].tick_params(axis='y', which='major', length=5, width=1)
            axs[i].tick_params(axis='x', which='major', length=5, width=1)
            axs[i].yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            axs[i].margins(x=0.01)

            locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
            formatter = mdates.ConciseDateFormatter(locator)
            formatter.formats[2] = '%d\n %b'
            formatter.zero_formats[1] = '%b\n %Y'
            formatter.zero_formats[2] = '%d\n %b'
            formatter.zero_formats[3] = '%H:%M\n %d-%b'
            formatter.offset_formats[3] = '%b %Y'
            formatter.show_offset = False
            axs[i].xaxis.set_major_locator(locator)
            axs[i].xaxis.set_major_formatter(formatter)
            if i == (len(self.Multi_Scenario) - 1) :
                handles, labels = axs[i].get_legend_handles_labels()
                leg1 = axs[i].legend(reversed(handles), reversed(labels), loc='lower left',bbox_to_anchor=(1,0),facecolor='inherit', frameon=True)
                axs[i].add_artist(leg1)
            i = i + 1

        all_axes = fig4.get_axes()

        self.xlabels = pd.Series(self.xlabels).str.replace('_',' ').str.wrap(10, break_long_words=False)

        j=0
        k=0
        for ax in all_axes:
            if ax.is_last_row():
                ax.set_xlabel(xlabel=(self.xlabels[j]),  color='black')
                j=j+1
            if ax.is_first_col():
                ax.set_ylabel(ylabel=(self.ylabels[k]),  color='black', rotation='vertical')
                k=k+1

        fig4.add_subplot(111, frameon=False)
        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        plt.xlabel('Date ' + '(' + self.timezone + ')',  color='black', rotation='horizontal', labelpad = 40)
        plt.ylabel('Flow to zone indicated in legend (MW)',  color='black', rotation='vertical', labelpad = 60)

        return {'fig': fig4}
