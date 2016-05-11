#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
restart_particles - create a spawn file for particle tracking based on the
                    end position on a particle tracking run
                    
    restart_particles -i Input_file -o Output_file  Date Time
 
    Input_file  - name of the netcdf file
    Output_file - name of the output csv file
    Date_string - String containing the Date and time of spawning
    
    example:
    restart_particles -i tn.nc -o Output_file spawnfile 1996-01-01 01:00:00

Context: Particle tracking over multiple years or to repeat years
         Written for Matthew Bone's PhD on Winter Nitrate NERC-SSB

Created on Tue May 10 16:44:56 2016

@author: TAMS00
"""

from netCDF4 import Dataset
import numpy as np
import argparse
import sys

#******************************************************************
def read_nc(VarName,FName):


    #print 'VarName, FName',VarName, FName
    try:
        grp = Dataset(FName)
    except:
        print("ERROR reading file "+FName)
        sys.exit()

    Var = grp.variables[VarName][:]

    #print "read var "+VarName+" from "+FName

    grp.close()
      
    return Var




#******************************************************************
def write_csv(FName,rows):
    import csv
    
    with open(FName,'wb') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        for row in rows:
            csvwriter.writerow(row)
            
            

#******************************************************************
# main() to take an optional 'argv' argument, which allows us to call it 
# from the interactive Python prompt: 
def main():
    # parse command line options
    
    parser = argparse.ArgumentParser()
    parser.add_argument('date', help='date for spawing')
    parser.add_argument('time', help='time for spawing')
    parser.add_argument('-i', '--infile', required=True, help='path of data input file')
    parser.add_argument('-o', '--outfile', required=True, help='path of data output file')
    args = parser.parse_args()
    
    strDateTime = args.date+" "+args.time
    InFName = args.infile
    OutFName = args.outfile

    link=InFName

    # Extract ipos
    try:           
        ipos = read_nc('ipos',link)
    except:
        print("ERROR Can\'t find variable ipos")
        sys.exit()

    # Extract jpos
    try:           
        jpos = read_nc('jpos',link)
    except:
        print("ERROR Cannot find variable jpos")
        sys.exit()

    # Extract vertical position. Negative is down.            
    try:           
        kpos = read_nc('kpos',link)
    except:
        print("ERROR Can\'t find variable kpos")
        sys.exit()

    # Extract health of superparticle
    try:           
        wfact = read_nc('wfact',link)
    except:
        print("ERROR Can\'t find variable wfact")
        sys.exit()

           
    # Use final position
    [Ntime,Npart]=ipos.shape
    ipos = ipos[Ntime-1,:]
    jpos = jpos[Ntime-1,:]
    kpos = kpos[Ntime-1,:]
    wfact = wfact[Ntime-1,:]

        
    rows=[]
    # Header has number of particles
    rows.append([Npart])
    # Create a row for every particle
    for ipart in range(Npart):
        lon=ipos[ipart]
        lat=jpos[ipart]
        depth=kpos[ipart]
        health=wfact[ipart]
        row=[ipart,lon,lat,depth,strDateTime,health]
        rows.append(row)
        
    write_csv(OutFName,rows)
        

if __name__ == "__main__":
    main()
