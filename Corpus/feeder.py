# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 11:39:35 2014

@author: Ruben
"""

import Corpus.residential as residential
import _pickle as cPickle
import numpy as np
import os

class IDEAS_Feeder(object):
    '''
    The Community class defines a set of households.
    '''
    
    def __init__(self, name, nBui, path, sh_K=True):
        '''
        Create the community based on number of households and simulate for
        output towards IDEAS model.
        '''
        self.name = name
        self.nBui = nBui
        self.sh_K = sh_K #defines whether space heating set-point temperature will be written in K (otherwise deg Celsius)
        
        # we create, simulate and pickle all 'nBui' buildings
        self.simulate(path)
        # then we loop through all variables and output as single file
        # for reading in IDEAS.mo
        os.chdir(path)
        self.output()
        # and conclude
        print('\n')
        print(' - Feeder %s outputted.' % str(self.name))

    def simulate(self, path):
        '''
        Simulate all households in the depicted feeder
        '''
        #######################################################################
        # we loop through all households for creation, simulation and pickling.
        # whereas the output is done later-on.
        cwd = os.getcwd()
        for i in range(self.nBui):
            hou = residential.Household(str(self.name) + '_' + str(i), path=path)
            hou.simulate()
            os.chdir(path)
            hou.pickle()
            os.chdir(cwd)

    def output(self):
        '''
        Output the variables for the dwellings in the feeder as a *.txt readable
        for Modelica.
        '''
        #######################################################################
        # we loop through all households for loading all variables 
        # which are stored in the object pickle.
        print('loading pickled household objects')
        # first load one house and grab dictionary of variables: 
        hou = cPickle.load(open(str(self.name)+'_0.p','rb'))
        variables=hou.variables # dictionary with explanation of main outputs
        dat=dict.fromkeys(variables.keys(),[])

        occ=[]

        for i in range(self.nBui): # loop over all households
            #print(i)
            hou = cPickle.load(open(str(self.name)+'_'+str(i)+'.p','rb')) #load results

            var = np.array(hou.occ)
            var_resolution = np.zeros((var.shape[0],8761))
            for member in range(0,var.shape[0]):
            # option 1: first point is the existing one for minute 0 (midnight), and the following are averages of previous 60 minutes.
            # This is only meaningfull if the occupancy profiles are converted first to metabolic heat gains before averaging.
                # var_resolution[member,:]=np.append(var[member,0],var[member,1:].reshape(-1,6).mean(axis=-1))  # moving average: mean of every 6 points
            # option 2: the setpoint of the first 10 minutes is assumed to be constant for the entire hour (instead of using an average value)
                var_resolution[member,:]=np.append(var[member,:var.shape[1]-1].reshape(-1,6)[:,0],var[member,var.shape[1]-1])
            if len(occ)!=0:
                occ=np.vstack((occ,var_resolution))
            else:
                occ=var_resolution

            for variable in variables.keys(): #loop over variables
                var = eval('hou.'+variable)
                if len(var)==525601: # if per minute data, make it per 60 min (mDHW, P, Q, QCon, QRad)
                    # first point is the existing one for minute 0 (midnight), and the following are averages of previous 60 minutes
                    var=np.append(var[0],var[1:].reshape(-1,60).mean(axis=-1)) # moving average: mean of every 60 points
                if len(var)==52561: # if per 10 minute data, make it per 60 min (sh_day, sh_night, sh_bath)
                    # option 1: first point is the existing one for minute 0 (midnight), and the following are averages of previous 60 minutes
                    var1 = np.append(var[0],var[1:].reshape(-1,6).mean(axis=-1))  # moving average: mean of every 6 points
                    # option 2: the setpoint of the first 10 minutes is assumed to be constant for the entire hour (instead of using an average value).
                    var = np.append(var[:len(var)-1].reshape(-1,6)[:,0],var[len(var)-1])
                if variable in ['sh_day','sh_bath','sh_night'] and self.sh_K: # if space heating setting and Kelvin required
                    variables[variable]=variables[variable].replace("Celsius", "Kelvin") # change variable explanation
                    var=var+273.15 # make it in Kelvin
                if len(dat[variable]) != 0: 
                    dat[variable] = np.vstack((dat[variable],var)) # add new column
                else: # if firts household (dat[variable] was empty)
                    dat[variable] = var # set equal to var

            # Checks
            # occupancy
            sum=0
            for i in range(0,occ.shape[1]):
                if 1 in occ[:,i]:
                    sum+=1
            print(sum)
        
        #######################################################################
        # and output the array to txt
        print('writing')
        for variable in variables.keys():
            print(variable)
            tim = np.linspace(0, 31536000,dat[variable].shape[0])  # create time column (always annual simulation=default)
            data = np.vstack((tim,dat[variable]))
            # print as header the necessary for IDEAS, plus explanation for each variable
            hea ='#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + variables[variable]
            np.savetxt(fname=variable+'.txt', X=data.T, header=hea,comments='', fmt='%.7g')

        # save occupancy profiles
        tim = np.linspace(0, 31536000,occ.shape[1])
        data = np.vstack((tim,occ))
        # print as header the necessary for IDEAS, plus explanation for each variable
        hea = '#1 \ndouble data(' + str(int(data.shape[1])) + ',' + str(int(data.shape[0])) + ') \n#' + 'Occupancy profiles (absent=3, sleeping=2, present & active=1)'
        np.savetxt(fname='occupancy.txt', X=data.T, header=hea, comments='', fmt='%.7g')