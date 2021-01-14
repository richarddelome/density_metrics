import gdal
import pandas as pd
import numpy as np
import fiona
import subprocess
import os
gdal.UseExceptions()




def make_df(raster_file):
    
    
    tif = gdal.Open(raster_file)
    
    arr_pop = tif.GetRasterBand(1) #raster bands to numpy arrays
    arr_pop = arr_pop.ReadAsArray().flatten()
    
    arr_area = tif.GetRasterBand(2)
    arr_area = arr_area.ReadAsArray().flatten()
    
    tif=None
    df = pd.DataFrame({"pop" : arr_pop, "area" : arr_area})
    
    
    df = df[(df["pop"] >= 0) & (df["area"] > 0)] #keeping land cells only

    df["pop"] = df["pop"].astype("float64") #gdal format arrays in float32 but I need float64 to compute the geometric mean (lots of decimals)
    df["area"] = df["area"].astype("float64")


    df["density"] = np.divide(df["pop"],df["area"],out=np.zeros_like(df["pop"]), where=df["area"]!=0) 

    df["density"] = df["density"].astype("float64")
    
    
    
    print("df done",end= " ")
    return df

def downsample(resolution):

    resample_dict = {
                 "10km" : "0.083333333 0.083333333",
                "5km" : '0.041666666 0.041666666',
                 }
    
    pixels = resample_dict[resolution] #getting the pixel size needed to resample at that scale
    
    command = "gdalwarp -overwrite -s_srs EPSG:4326 -t_srs  EPSG:4326 -tr {}  -r sum merged.vrt downsampled.tif".format(pixels) 
    subprocess.run(command,shell=True)
    print("downsampling done",end = " ")
    
    

def rename_dic(dic,resolution): # rename the metrics after the resolution of the current raster
    new_dic = dic.copy()
    for name in dic.keys():
        new_name = "{}_{}".format(resolution,name)
        new_dic[new_name] = new_dic.pop(name)
    return new_dic


def gini(array): # I use this function for the gini coefficient :  https://github.com/oliviaguest/gini
    """Calculate the Gini coefficient of a numpy array."""
    # based on bottom eq: http://www.statsdirect.com/help/content/image/stat0206_wmf.gif
    # from: http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    array = array.flatten() #all values are treated equally, arrays must be 1d
    if np.amin(array) < 0:
        array -= np.amin(array) #values cannot be negative
    array += 0.0000001 #values cannot be 0
    array = np.sort(array) #values must be sorted
    index = np.arange(1,array.shape[0]+1) #index per array element
    n = array.shape[0]#number of array elements
    return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array))) #Gini coefficient
        
def compute_metrics(df,resol):
    
    metrics = {}
        
    #population
    metrics["population"] = df["pop"].sum()
    print("metrics computed : population : ",metrics["population"], end=" ")

    #area
    metrics["area"] = df["area"].sum() 
    print("area : ", metrics["area"],end=" ")

    #emptiness
    lived_df = df[df["pop"] >= 1]
    metrics["lived_cells"] = len(lived_df)/len(df)*100
    print("lived cells : ",metrics["lived_cells"], end= " ")

    #lived density
    metrics["lived_density"] = lived_df["pop"].sum()/lived_df["area"].sum()
    print("lived density : ", metrics["lived_density"], end= " ")

    #population gini index
    metrics["gini_index"] = gini(df["pop"].to_numpy())
    print("gini_index : ", metrics["gini_index"], end= " ")
        
    #density
    metrics["density"] = np.divide(df["pop"].sum(),df["area"].sum(),out=np.zeros_like(df["pop"].sum()), where=df["area"].sum()!=0)
    print("density : ",metrics["density"], end=" ")
        
    #arithmetic mean pwd
    metrics["arithmetic_pwd"] = np.sum( df["density"] * (df["pop"]/df["pop"].sum()) )
    print("arithmetic mean pwd : ", metrics["arithmetic_pwd"], end=" ")
    
    #geometric mean pwd
    a = df["density"]**(df["pop"]/df["pop"].sum())
    metrics["geometric_pwd"] = pd.Series(a).product()
    print("geometric mean : ", metrics["geometric_pwd"], ". All metrics computed.")
    
        
    metrics = rename_dic(metrics,resol)
    return metrics


class Raster_base:
    def __init__(self, name, pop_file,area_file,shp_file,geo_name,layer=None):
        self.name = name
        self.pop_file = pop_file
        self.area_file = area_file
        self.shp_file = shp_file
        self.layer = layer
        self.geo_name = geo_name
        
    

    def make_raster(self,geoid):
        if self.layer :
            command_pop = f"""gdalwarp -overwrite -cutline {self.shp_file} -crop_to_cutline -cl {self.layer} -cwhere "{self.geo_name}='{geoid}'"  {self.pop_file} pop_temp.tif"""
            command_area = f"""gdalwarp -overwrite -cutline {self.shp_file} -crop_to_cutline -cl {self.layer} -cwhere "{self.geo_name}='{geoid}'"  {self.area_file} area_temp.tif"""
        else:
            command_pop = f"""gdalwarp -overwrite -cutline {self.shp_file} -crop_to_cutline -cwhere "{self.geo_name}='{geoid}'"  {self.pop_file} pop_temp.tif"""
            command_area = f"""gdalwarp -overwrite -cutline {self.shp_file} -crop_to_cutline -cwhere "{self.geo_name}='{geoid}'"  {self.area_file} area_temp.tif"""

        subprocess.run(command_pop,shell=True)
        subprocess.run(command_area,shell=True)

        command = "gdalbuildvrt -overwrite merged.vrt -separate pop_temp.tif area_temp.tif"
        subprocess.run(command,shell=True)
        print("Clipping raster done", end =" ")
        


    
    def generate_estimates(self):
        
        if self.layer:
            dst_in = fiona.open(self.shp_file, layer=self.layer)
        else :
            dst_in = fiona.open(self.shp_file)

        pwd_list = []
        n=1

        for feature in dst_in:

            pwd_dict = {}
            properties = feature["properties"]

            geoid = properties[self.geo_name]

            if geoid == "ATA":
                continue

            pwd_dict["geoid"] = geoid


            print("")
            print("region n°",n, " ",pwd_dict["geoid"])
            print("")
            print("")

            try :
                self.make_raster(geoid)
            except Exception as e:
                pwd_dict["1km_population"] = str(e)
                continue

            for resolution in ("1km","5km","10km"):
                try:
                    if resolution == "1km":
                        df=make_df("merged.vrt")
                    else:
                        downsample(resolution)
                        df = make_df("downsampled.tif")
                except Exception as e:
                    print(e)
                    pwd_dict["{}_population".format(resolution)] = str(e)
                    continue
                
                try :
                    metrics = compute_metrics(df,resolution)
                    pwd_dict = pwd_dict|metrics
                except Exception as e:
                    print(e)
                    pwd_dict["{}_population".format(resolution)] = str(e)
            
            pwd_list.append(pwd_dict)
            n +=1
            
        dst_in.closed
        df = pd.json_normalize(pwd_list)
        return df


def main():
    rasters_csv = "to_process.csv"

    if not os.path.exists('output'):
        os.makedirs('output')
    
    rasters_list = pd.read_csv(rasters_csv,keep_default_na=False)

    rasters_list.columns = ["name", "pop_file","area_file", "shp_file", "layer","geo_name"]
    
    for index, row in rasters_list.iterrows():

        name = row["name"]
        pop_file = row["pop_file"]
        area_file = row["area_file"]
        shp = row["shp_file"]
        layer = row["layer"]
        geo_name = row["geo_name"]
        print("layer = ", type(layer))
        if layer != "":
            raster_base = Raster_base(name, pop_file,area_file,shp, geo_name,layer)
            
        else :
            raster_base = Raster_base(name, pop_file,area_file,shp, geo_name)
            
        df = raster_base.generate_estimates()

        csv_name = f"output/{name}.csv"
        df.to_csv(csv_name,index=False)


if __name__ == "__main__":
    main()


