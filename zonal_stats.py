#!/usr/bin/env python
"""
 zonal_stats - Calculates statistics of a raster variable within a region.
               Reads array from netCDF file and regions from ashapefile.
 
 Usage: zonal_stats raster_file variable_name region_file results_file

	raster_file - filename of netCDF file. If a directory is given all 
                      the netcdf files will be processed
	variable_name - name of netCDF variable
        region_file - shapefile name containing region(s)
        results_file - filename of csv file containing the results


 example:
        zonal_stats.py analysed_spim_199801.nc SMMean CP2_lv2.shp results.csv


"""

# Modified:
#  v0 2016-02-10 TAMS
#  v1 2016-02-15 TAMS
#	Reads all nc files in directory
#  v2 2016-02-16 TAMS
#	For each polygon lops over all raster to avoid recalculating mask

# TODO
# Use better arguments module
#

import time,sys,os
import numpy as np
import netCDF4 as nc
import shapefile as shp
import shapely.geometry as shply
import matplotlib.pyplot as plt
import csv



#DEFINITONS
# set individual parameters here
stats=['mean','median','std','count']

#******************************************
def prelude(argv):
#******************************************

    # get input file name
    if len(sys.argv) <> 5:
        print ('ERROR: Must receive 4 arguments')
        print __doc__
        sys.exit()
        #raise Exception('Must receive 5 arguments')

    ncPath = sys.argv[1]
    ncVname = sys.argv[2]
    shpFname = sys.argv[3]
    resultsFname = sys.argv[4]
   
    options={'ncPath':ncPath,'ncVname':ncVname,'shpFname':shpFname, 'resultsFname':resultsFname}

    return options

#******************************************
def readNC(ncFname,ncVname):
#******************************************

    try:
        nc1 = nc.Dataset(ncFname, 'r')
    except:
        raise Exception('ERROR reading file '+ncFname)

    lat = nc1.variables['lat']
    lon = nc1.variables['lon']

    try:
        arrayVal = np.squeeze(nc1.variables[ncVname])
    except:
        print('Available variables:')
        print(nc1.variables)
        raise Exception('ERROR cannot find var '+ncVname)


    # Masking _FillValue if missing_value is not being used in netcdf file
    FillValue = nc1.variables[ncVname]._FillValue
    arrayVal =np.ma.masked_equal(arrayVal,FillValue)

    [Nrows,Ncols] = arrayVal.shape
    if len(lat.shape) == 1:
        arrayX,arrayY = np.meshgrid(lon,lat)
   

    return arrayX,arrayY,arrayVal

#**********************************************
def make_mask(polygon,arrayX,arrayY):
#**********************************************

    [Nrows,Nlines] = arrayX.shape
    mask = np.ma.zeros([Nrows,Nlines],dtype=bool)

    start=time.time()
    for row in range(Nrows):
        for col in range(Nlines):
            x = arrayX[row,col]
            y = arrayY[row,col]
            p=shply.Point(x,y)
            if p.within(polygon):
                mask[row,col] = True
    stop=time.time()
    elapsed= stop-start
    elapseds="%.2f"%elapsed
    print('make_mask: ' + elapseds + ' s')

    return mask


#******************************************
def zonal_stats(poly,arrayX,arrayY,arrayVal,stats,mask):
#******************************************


    if len(mask)==0:
        mask = make_mask(poly,arrayX,arrayY)
    maskedVal = np.ma.masked_where(np.logical_not(mask),arrayVal)

    mean=[]
    median=[]
    std=[]
    max=[]
    min=[]
    count=[]
    for stat in stats:
        if stat == 'mean':
            mean = np.ma.mean(maskedVal)
        elif stat == 'median':
            # for some reason median returns masked_array:
            #    masked_array(data = [1.0,mask = False,fill_value = 1e+20)
            median = float(np.ma.median(maskedVal))
        elif stat == 'std':
            std = np.ma.std(maskedVal)
        elif stat == 'max':
            max = np.ma.max(maskedVal)
        elif stat == 'min':
            min = np.ma.min(maskedVal)
        elif stat == 'count':
            count = np.ma.count(maskedVal)

    results={'mean':mean,'median':median,'std':std,'max':max,'min':min,'count':count}


    return results, mask


#******************************************
def area_overlap(bbox1,bbox2):
#******************************************

    if ( ( ( bbox1[0] > bbox2[2] ) or ( bbox1[2] < bbox2[0] ) ) or
         ( ( bbox1[1] > bbox2[3] ) or ( bbox1[3] < bbox2[1] ) ) ):
        overlap = False

    else:

        overlap = True

    return overlap


#********************************************************
def write_results(ncFiles,resultsll,resultsFname,shprecs):
#********************************************************

    NPoly = len(resultsll)
    NFiles = len(resultsll[0])

    f = open(resultsFname,'w')
    writer = csv.writer(f)

    writer.writerow(shprecs)    

    rec = ['FName']
    for iPoly in range(NPoly):
        for stat in stats:
            rec.append(stat)
    writer.writerow(rec)

    for iFile in range(NFiles):
        ncFile = ncFiles[iFile]
        rec=[ncFile]
        for iPoly in range(NPoly):
            for stat in stats:
                rec.append(resultsll[iPoly][iFile][stat])
        writer.writerow(rec)

   
#******************************************
def main(argv=None):
#******************************************

    start1 = time.time()

    if argv is None:
        argv = sys.argv


    options = prelude(argv)

    shpread = shp.Reader(options['shpFname'])
    shapes = shpread.shapes()

    #shapefile has no useful records describing the polygon
    try:
        shprecords = shpread.records()
        print(shprecords)
        shprecs=[]
        for rec in shprecords:
        # record 0 is OBJECTID
            shprecs=rec.append(rec[0])
        print('shprecs')
        print(shprecs)
    except:
        print('ERROR: no records in shapefile')

    if os.path.isdir(options['ncPath']):
        ncFiles = [options['ncPath']+f for f in os.listdir(options['ncPath']) if f.endswith('.nc')]
        ncFiles.sort()
    elif os.path.isfile(options['ncPath']):
        ncFiles = [options['ncPath']]
    else:
        print('ERROR ncPath does not exist'+ncPath)
        sys.exit()

    resultsll = []
    #for each polygon in shapefile 
    for shape in shapes:
        points = shape.points
        poly = shply.Polygon(points)

        prevArrayX = []
        prevArrayY = []
        mask=[]
        resultsl=[]
        for ncFile in ncFiles:

            print('reading:   '+os.path.basename(ncFile))
            [arrayX,arrayY,arrayVal]  = readNC(ncFile,options['ncVname'])
            array_bbox = [arrayX.min(),arrayY.min(),arrayX.max(),arrayY.max()]

            if True:
            #if area_overlap(poly.bounds,array_bbox):
                if ( np.array_equal(arrayX,prevArrayX) and np.array_equal(arrayY,prevArrayY) ):
                    [result,mask] = zonal_stats(poly,arrayX,arrayY,arrayVal,stats,mask)
                else:
                    [result,mask] = zonal_stats(poly,arrayX,arrayY,arrayVal,stats,[])
                    prevArrayX = arrayX
                    prevArrayY = arrayY

                resultsl.append(result)

        resultsll.append(resultsl)

    write_results(ncFiles,resultsll,options['resultsFname'],shprecs)

    stop1 = time.time()
    elapsed = stop1-start1
    elapseds="%.2f"% elapsed
    print('Time elapsed: ' + elapseds + ' s')



if __name__ == "__main__":
    main()


