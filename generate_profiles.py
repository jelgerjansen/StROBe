from Corpus.residential import Household
from Corpus.feeder import IDEAS_Feeder
import os
import shutil
import pandas as pd
import numpy as np
import random

def generate_profiles ():
    """This function ..."""
    kwargs = {'members':['FTE','FTE']}
    family = Household("Example family", **kwargs) #alternative: family = Household("ex", members=["FTE"])
    family.parameterize()
    family.simulate()

    IDEAS_Feeder('Example', 1, "C:\Users\u0132350\Documents\GIT/occupant_profiles")

def generate_profiles_known_household():
    """This function ..."""
    family = Household("Example family")
    family.parameterize()
    family.simulate()

    IDEAS_Feeder('Example1', 1, "C:\Users\u0132350\Documents\GIT/occupant_profiles")

def generate_multiple_profiles(number_of_profiles = 2000, resultpath = "C:\Users\u0132350\Documents\StROBe_profiles/"):
    """ This function generates a predefined number of profiles and saves them to the predefined resultpath.
    The profiles are in the format: number_P.txt, number_Q.txt etc. This makes them valid as an input for teaser.
    You can copy-paste them to the occupancy-data-folder.
    """
    if not os.path.exists(resultpath):
        os.makedirs(resultpath)
    # Make sure you get the same profiles, so set a seed
    # random.seed(0) does not work!!

    # Then proceed
    index = 4200
    while index < number_of_profiles:
        resultpath_id = resultpath + str(index) + "/"
        if not os.path.exists(resultpath_id):
            os.makedirs(resultpath_id)
        IDEAS_Feeder(name=str(index), nBui=1, path=resultpath_id)
        delete_spaces(resultpath_id)
        index += 1
    rename_files(resultpath)

def delete_spaces(resultpath):
    """ This function deletes the # in the first two lines of the output-files,
        otherwise the strobe info manager can't read the profiles.
    :param resultpath:
    :return:
    """
    resultpath = resultpath
    outputfiles = [file for file in os.listdir(resultpath) if
                        file.endswith(".txt")]
    for outputfile in outputfiles:
        with open(resultpath+outputfile, 'r') as file:
            filedata = file.read()
        filedata = filedata.replace("# ", "")
        filedata = filedata.replace("#   ", "")
        with open(resultpath+outputfile, 'w') as file:
            file.write(filedata)

def rename_files(resultpath=None):
    """ This function renames the output-files and moves them to the upper-level folder.
    Subsequently, the lower-level folder are deleted.
    Finally, the sh_bath.txt-files are removed, as we don't need the temperature setpoints for bathrooms.
    """
    if resultpath is None:
        resultpath = "C:\Users\u0132350\Documents\StROBe/"
    else:
        resultpath = resultpath
    # list all output folders
    outputdirs = [dir for dir in os.listdir(resultpath) if os.path.isdir(resultpath+dir)]

    # rename every text file in output folder and move to upper level folder, then remove lower level folder
    for outputdir in outputdirs:
        outputfiles = [file for file in os.listdir(resultpath+"/"+outputdir) if
                       file.endswith(".txt")]
        print outputdir
        for filename in outputfiles:
            old_filename = filename
            new_filename = outputdir + "_" + filename
            os.rename(resultpath+outputdir+"/"+old_filename, resultpath+"/"+new_filename)
        try:
            shutil.rmtree(resultpath+"/"+outputdir)
        except:
            pass
    # remove sh_bath as we will never implement bathrooms
    files_to_remove = [file for file in os.listdir(resultpath) if
                   file.endswith("sh_bath.txt")]
    for file in files_to_remove:
        os.remove(resultpath + file)

def rename_ids(resultpath=None):
    """ This function renames the output-files and moves them to the upper-level folder.
    Subsequently, the lower-level folder are deleted.
    Finally, the sh_bath.txt-files are removed, as we don't need the temperature setpoints for bathrooms.
    """
    if resultpath is None:
        resultpath = "C:\Users\u0132350\Documents\StROBe/"
    else:
        resultpath = resultpath
    # list all output folders
    outputfiles= [file for file in os.listdir(resultpath) if os.path.isfile(resultpath+file) and file.endswith("_info.txt") ]
    # rename every text file in output folder and move to upper level folder, then remove lower level folder
    for outputfile in outputfiles:
        # Get strobe ID and get info file
        strobe_id = outputfile.split("_info.txt")[0]
        info = pd.read_csv(resultpath+outputfile, sep=";", header=None)
        # Get household size and create directory to put all profiles of this household size in
        household_size = info.iloc[0,1]
        resultpath_new = resultpath + str(household_size) + "/"
        if not os.path.exists(resultpath_new):
            os.makedirs(resultpath_new)
        # Replace files into folders (the folder name is the number of occupants)
        files = ['_info.txt', '_mDHW.txt', '_P.txt', '_Q.txt', '_QCon.txt', '_QRad.txt', '_sh_day.txt', '_sh_night.txt']
        for file in files:
            os.rename(resultpath+strobe_id+file, resultpath_new+strobe_id+file) # """

    # List number of profiles for every household number
    household_sizes = [size for size in os.listdir(resultpath) if os.path.isdir(resultpath+size)]
    print household_sizes
    household_size_dict = dict()
    for size in household_sizes:
        if int(size) < 10:
            profiles = [file for file in os.listdir(resultpath+size+"/") if os.path.isfile(resultpath+size+"/"+file) and file.endswith("_info.txt") ]
            profile_ids = [id.split("_info.txt")[0] for id in profiles]
            household_size_dict[int(size)] = len(profiles)
            print "For the households with " + str(size) + " people, we have " + str(len(profiles)) + " profiles."
            for index, profile_id in enumerate(profile_ids):
                id_old = profile_id
                if len(str(index)) == 1:
                    id_new = size + "000" + str(index)
                elif len(str(index)) == 2:
                    id_new = size + "00" + str(index)
                elif len(str(index)) == 3:
                    id_new = size + "0" + str(index)
                elif len(str(index)) == 4:
                    id_new = size + str(index)
                files = ['_info.txt', '_mDHW.txt', '_P.txt', '_Q.txt', '_QCon.txt', '_QRad.txt', '_sh_day.txt', '_sh_night.txt']
                for file in files:
                    os.rename(resultpath + size + "/" + id_old + file, resultpath + id_new + file)#"""
    print household_size_dict
    # At this point, the profiles are re-ordered. The first number is the number of occupants. Then, the specific ID follows (is reordered from zero to ...).

    """# In case you made an error
    for file in os.listdir(resultpath):
        if os.path.isfile(resultpath+file):
            resultpath_new = "D:\ina\StROBe_profiles/"
            os.rename(resultpath+file, resultpath_new+file)#"""
    """# Put all back in their folders!
    for file in os.listdir(resultpath):
        if os.path.isfile(resultpath+file):
            household_size = file.split("0",1)[0]

            id = file.split("0",1)[1]
            id = "100"+id
            resultpath_new = resultpath + household_size + "/"
            if not os.path.exists(resultpath_new):
                os.makedirs(resultpath_new)
            os.rename(resultpath+file, resultpath_new+id)#"""

def check_strobe_profiles(strobe_path = "C:\Users\u0132350\Documents\StROBe_profiles/"):
    info_files = [file for file in os.listdir(strobe_path) if file.endswith("_mDHW.txt")]
    file_ids = [file.split("_")[0] for file in info_files]
    number_of_profiles = len(file_ids)
    print file_ids
    profiles_to_remove=[]
    print "Total number of profiles: " + str(number_of_profiles)
    print "CHECK DAY ZONE AVERAGE TEMPERATURE"
    dayzone_check = 0.0
    for file in file_ids:
        # Import sh_day and calculate average
        df_setpoint = pd.read_csv(strobe_path+file+"_sh_day.txt", sep = " ", index_col=0, skiprows=2, usecols=[0,1])
        df_setpoint.columns = ['setpoint']
        if df_setpoint.shape[0] == 35040 or df_setpoint.shape[0] == 52561: #35040 if sampled with 900s, 52561 if sampled with 600s
            pass
        else:
            print ("    Profile " + file + " has an incorrect length considering sampled at 600 or at 900 seconds")

        average_setpoint = df_setpoint.mean()[0]
        if average_setpoint > 15.0:
            pass
        else:
            print ("    Profile " + file + " has average setpoint for day zone of " + str(average_setpoint) + ", which is thus lower than 15 degC")
            profiles_to_remove.append(file)
            dayzone_check += 1
    print str(dayzone_check) + " out of " + str(number_of_profiles) + " profiles have an unheated day zone, being " + str(round(dayzone_check/number_of_profiles*100,0)) + " percent"
    print profiles_to_remove
    print "CHECK NIGHT ZONE AVERAGE TEMPERATURE"
    nightzone_check = 0.0
    for file in file_ids:
        df_setpoint = pd.read_csv(strobe_path + file + "_sh_night.txt", sep=" ", index_col=0, skiprows=1, usecols=[0,1])
        df_setpoint.columns = ['setpoint']
        if df_setpoint.shape[0] == 35040 or df_setpoint.shape[0] == 52561: #35040 if sampled with 900s, 52561 if sampled with 600s
            pass
        else:
            print ("    Profile " + file + " has an incorrect length considering sampled at 600 or at 900 seconds")

        average_setpoint = df_setpoint.mean()[0]
        if average_setpoint < 15.0:
            pass
        else:
            print ("    Profile " + file + " has average setpoint for night zone of " + str(average_setpoint) + ", which means the night zone is heated")
            nightzone_check += 1
    print str(nightzone_check) + " out of " + str(number_of_profiles) + " profiles have a heated night zone, being " + str(round(nightzone_check/number_of_profiles*100,1)) + " percent"

    print "CHECK HOW WATER TAPPING"
    dhw_check = 0.0
    for file in file_ids:
        df_setpoint = pd.read_csv(strobe_path + file + "_mDHW.txt", sep=" ", index_col=0, skiprows=1, usecols=[0,1])
        df_setpoint.columns = ['flow']
        if df_setpoint.shape[0] == 35040 or df_setpoint.shape[0] == 52561 or df_setpoint.shape[0] == 525601: #35040 if sampled with 900s, 52561 if sampled with 600s, 525601 if sampled with 60 s
            pass
        else:
            print ("    Profile " + file + " has an incorrect length considering sampled at 60 or at 600 or at 900 seconds")
        timearray = df_setpoint.index.values
        qarray = df_setpoint['flow'].values
        dhw_use = np.trapz(y=qarray, x=timearray)
        if dhw_use < 15.0:
            pass
        else:
            print ("    Profile " + file + " has a draw-off of " + str(round(dhw_use/365.0,0)) + " l/day")
            nightzone_check += 1
    print str(dayzone_check) + " out of " + str(number_of_profiles) + " profiles have a heated night zone, being " + str(round(dhw_check/number_of_profiles*100,1)) + " percent"

def remove_profiles(ids, strobe_path = "C:\Users\u0132350\Documents\StROBe_profiles/"):
    for file in os.listdir(strobe_path):
        if os.path.isfile(strobe_path + file):
            id = file.split("_", 1)[0]
            if id in ids:
                print str(id) + " will be removed"
                os.remove(strobe_path+file)

def move_profiles(oldpath="C:\Users\u0132350\Documents\StROBe/Profiles/", newpath="D:\Ina\TEASER/teaser\data\input\inputdata\occupancydata/"):
    outputfiles= [file for file in os.listdir(oldpath) if os.path.isfile(resultpath+file) and file.endswith(".txt") ]
    for outputfile in outputfiles:
        os.rename(oldpath+outputfile, newpath+outputfile)


if __name__ == '__main__':
    resultpath = "C:\Users\u0132350\Documents\StROBe/Profiles/"
    # First generate multiple profiles. In the process, they will be in separate folders, but by the end, they are moved to 1 folder
    """generate_multiple_profiles(number_of_profiles = 4600, resultpath = resultpath)#"""
    # If you had a small error or so and it did not finish properly, then you can move the profile by using this function
    """rename_files(resultpath= resultpath)#"""
    # After that, you want to have the proper IDs. So, you detect the household size and put them in 1 folder per household size.
    # Then, you renumber the profiles per household size and put them back in the general folder.
    """rename_ids(resultpath=resultpath)#"""
    # However, there will be some files with setpoints at 12 degC. So you have to detect these. There will be printed out a list with wrong profiles.
    # You have to copy paste this list and remove these profiles.
    """check_strobe_profiles(strobe_path = resultpath)#"""
    # Remove these profiles
    """remove_profiles(ids = ['10003', '10015', '10019', '10022', '10031', '10036', '10074', '10108', '10132', '10185',
                           '10207', '10214', '10239', '10295', '10299', '10320', '10360', '10371', '10400', '10409',
                           '10435', '10545', '10557', '10609', '10661', '10680', '10698', '10730', '10750', '10775',
                           '10781', '10787', '10818', '10843', '10844', '10851', '20010', '20049', '20068', '20111',
                           '20119', '20137', '20162', '20166', '20221', '20281', '20299', '20308', '20314', '20321',
                           '20326', '20373', '20442', '20460', '20482', '20489', '30041', '30044', '30049', '30060',
                           '30077', '30084', '30091', '30132', '30143', '30206', '30248', '30264', '30268', '40014',
                           '40068', '40134', '40147', '40151', '40166', '50006', '50017', '50028', '50030', '50037',
                           '50057'], strobe_path = resultpath)#"""
    # However, now there are gaps in the IDs, so rerun this function to you have the proper numbering of the profiles
    """rename_ids(resultpath = resultpath)#"""
    # Move profiles to TEASER
    #move_profiles(oldpath="C:\Users\u0132350\Documents\StROBe/Profiles/", newpath="D:\Ina\TEASER/teaser\data\input\inputdata\occupancydata/")

    print("Done with generating profiles :)")
