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
        QMet=[]

        # Define variables to calculate metabolic heat gains. Since only thermal comfort is studied, only sensible heat is calculated (no latent heat is considered here).
        # Values taken from ASHRAE Handbook - Fundamentals (2009), body surface of 1.8 m^2 is assumed
        QMetActivePerA=80 # seated (quiet)=60 (35%), standing (relaxed)=70 (35%), walking (slow)=115 (10%), cooking=95-115 (10%), housecleaning=115-200 (10%)
        QMetSleepPerA=40
        A = {'U12': 0.9, 'School': 1.68, 'Unemployed': 1.8, 'PTE': 1.8, 'FTE': 1.8, 'Retired': 1.8} # based on https://doi.org/10.1016/j.dib.2017.10.036 ! For U12, no occupancy is generated, so it is not taken into account for metabolic heat gains
        radFra=0.5

        for i in range(self.nBui): # loop over all households
            #print(i)
            hou = cPickle.load(open(str(self.name)+'_'+str(i)+'.p','rb')) #load results
            var = np.array(hou.occ)
            QConMet_day = np.zeros((var.shape[0],var.shape[1]))
            QRadMet_day = np.zeros((var.shape[0],var.shape[1]))
            QConMet_night = np.zeros((var.shape[0],var.shape[1]))
            QRadMet_night = np.zeros((var.shape[0],var.shape[1]))
            for member in range(0,var.shape[0]):
                QConMet_day[member,:]=var[member,:]*((var[member,:]==1)*QMetActivePerA*A[str(hou.members[member])]*(1-radFra)+(var[member,:]!=1)*0)
                QRadMet_day[member,:]=var[member,:]*((var[member,:]==1)*QMetActivePerA*A[str(hou.members[member])]*radFra+(var[member,:]!=1)*0)
                QConMet_night[member,:]=var[member,:]*((var[member,:]==2)*QMetSleepPerA*A[str(hou.members[member])]*(1-radFra)+(var[member,:]!= 2)*0)
                QRadMet_night[member,:]=var[member,:]*((var[member,:]==2)*QMetSleepPerA*A[str(hou.members[member])]*radFra+(var[member,:]!=2)*0)

            QMetOneBuilding=np.array([QConMet_day,QRadMet_day,QConMet_night,QRadMet_night])
            QMetOneBuilding_resolution=np.zeros((QMetOneBuilding.shape[0],8761))
            QMetOneBuilding=QMetOneBuilding.sum(axis=1)

            for list in range(0,QMetOneBuilding.shape[0]):
            # option 1: first point is the existing one for minute 0 (midnight), and the following are averages of previous 60 minutes.
            # This is only meaningful if the occupancy profiles are converted first to metabolic heat gains before averaging.
                QMetOneBuilding_resolution[list]=np.append(QMetOneBuilding[list,0],QMetOneBuilding[list,1:].reshape(-1,6).mean(axis=-1))  # moving average: mean of every 6 points
            # option 2: the setpoint of the first 10 minutes is assumed to be constant for the entire hour (instead of using an average value)
                # var_resolution[member,:]=np.append(var[member,:var.shape[1]-1].reshape(-1,6)[:,0],var[member,var.shape[1]-1])
            if len(occ)!=0:
                occ=np.vstack((occ,var))
            else:
                occ=var

            if len(QMet)!=0:
                QMetOneBuilding_resolution.resize(QMetOneBuilding_resolution.shape[0],1,QMetOneBuilding_resolution.shape[1])
                QMet=np.concatenate((QMet,QMetOneBuilding_resolution),axis=1)
            else:
                QMet=QMetOneBuilding_resolution
                QMet.resize(QMet.shape[0],1,QMet.shape[1])

            for variable in variables.keys(): #loop over variables
                var = eval('hou.'+variable)
                if len(var)==525601: # if per minute data, make it per 60 min (mDHW, P, Q, QCon, QRad)
                    # first point is the existing one for minute 0 (midnight), and the following are averages of previous 60 minutes
                    var=np.append(var[0],var[1:].reshape(-1,60).mean(axis=-1)) # moving average: mean of every 60 points
                if len(var)==52561: # if per 10 minute data, make it per 60 min (sh_day, sh_night, sh_bath)
                    # option 1: first point is the existing one for minute 0 (midnight), and the following are averages of previous 60 minutes
                    var = np.append(var[0],var[1:].reshape(-1,6).mean(axis=-1))  # moving average: mean of every 6 points
                    # option 2: the setpoint of the first 10 minutes is assumed to be constant for the entire hour (instead of using an average value).
                    # var = np.append(var[:len(var)-1].reshape(-1,6)[:,0],var[len(var)-1])
                if variable in ['sh_day','sh_bath','sh_night'] and self.sh_K: # if space heating setting and Kelvin required
                    variables[variable]=variables[variable].replace("Celsius", "Kelvin") # change variable explanation
                    var=var+273.15 # make it in Kelvin
                if len(dat[variable]) != 0: 
                    dat[variable] = np.vstack((dat[variable],var)) # add new column
                else: # if firts household (dat[variable] was empty)
                    dat[variable] = var # set equal to var
        
        #######################################################################
        # and output the array to txt
        print('writing')
        for variable in variables.keys():
            print(variable)
            tim = np.linspace(0, 31536000,dat[variable].shape[1])  # create time column (always annual simulation=default)
            data = np.vstack((tim,dat[variable]))
            # print as header the necessary for IDEAS, plus explanation for each variable
            hea ='#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + variables[variable]
            np.savetxt(fname=variable+'.txt', X=data.T, header=hea,comments='', fmt='%.7g')

        # save occupancy profiles and print as header the necessary for IDEAS, plus explanation for each variable
        tim = np.linspace(0, 31536000,occ.shape[1])
        data = np.vstack((tim,occ))
        hea = '#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + 'Occupancy profiles (absent=3, sleeping=2, present & active=1)'
        np.savetxt(fname='occupancy.txt', X=data.T, header=hea, comments='', fmt='%.7g')
        tim = np.linspace(0, 31536000,QMet.shape[2])
        data = np.vstack((tim,QMet[0,:,:]))
        hea = '#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + 'Convective metabolic heat gains in the day zone in W'
        np.savetxt(fname='QConMet_day.txt', X=data.T, header=hea, comments='', fmt='%.7g')
        tim = np.linspace(0, 31536000,QMet.shape[2])
        data = np.vstack((tim,QMet[1,:,:]))
        hea = '#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + 'Radiative metabolic heat gains in the day zone in W'
        np.savetxt(fname='QRadMet_day.txt', X=data.T, header=hea, comments='', fmt='%.7g')
        tim = np.linspace(0, 31536000,QMet.shape[2])
        data = np.vstack((tim,QMet[2,:,:]))
        hea = '#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + 'Convective metabolic heat gains in the night zone in W'
        np.savetxt(fname='QConMet_night.txt', X=data.T, header=hea, comments='', fmt='%.7g')
        tim = np.linspace(0, 31536000,QMet.shape[2])
        data = np.vstack((tim,QMet[3,:,:]))
        hea = '#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + 'Radiative metabolic heat gains in the night zone in W'
        np.savetxt(fname='QRadMet_night.txt', X=data.T, header=hea, comments='', fmt='%.7g')