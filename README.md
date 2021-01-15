## Alternative density metrics

*note : I'm not an academic or a gis specialist. This is just a personal project. If you want to use this, please check my code before.*

This script computes several alternative density metrics for all countries and their first level subregions using population gridded datasets.

While everyone knows about population density, this number has its limitations, particularly if you want to interpret it as a measure of "crowdedness". The problem is that it takes into account all areas indiscriminately , even vast empty land. For example, the Sahara desert makes up 90% of Algeria's surface, which means Algeria has a fairly low population density. But, because of this huge bias, population density tells us very little about how crowded the remaining 10% land is. 
For more about this problem, you can read this excellent [article](https://theconversation.com/think-your-country-is-crowded-these-maps-reveal-the-truth-about-population-density-across-europe-90345).

Here I try to explore alternatives to traditional population density. My goal is to see whether these metrics are robust, by computing them at 3 different scales across 4 different datasets. I use population gridded datasets which split land into multiple cells of equal size and give population count for each of them. There are 4 of them : the [Worldpop](https://www.worldpop.org) project, Gridded Population of the World ([GPW](https://sedac.ciesin.columbia.edu/data/collection/gpw-v4)), the [Landscan](https://landscan.ornl.gov/) database, and the Global Human Settlement Layer ([ghsl](https://ghsl.jrc.ec.europa.eu/)). The advantage of using these uniform cells (although they are not exactly uniform, see below) instead of, say, census tracts as the basic unit is that it should minimize the modifiable areal unit problem and it should also have a higher precision.

The measures are :
- Population, area and population density. This is in order to check that these numbers are accurate compared to official figures.
- Lived cells : this is the percentage of cells where at least one person lives.
- Lived density : I got this one from Alasdair Rae. It's just total population divided by lived area (the sum of lived cells areas). It's the simplest metric since it's the same as population density but without taking into account empty cells.

- Population gini index : this is like the gini index for wealth inequality but applied to population location. Instead of measuring how much wealth is concentrated among a population, it measures how population is concentrated on a given land. At 0, the population is distributed evenly across all cells, while at 1 all the population is located in one cell and all the others are empty. This is more about emptiness than density but still pretty interesting.

- Population weighted density. This is equal to the sum of all the densities of the subareas of a place weighted by the share of the population that lives on each of them. It means that more populated areas will be given more weight in the calculation while empty areas won't have any. Thus it should give us the best idea of the density at which the average citizen lives.

- Population weighted density using the geometric mean instead of the arithmetic mean.  [Craig, 1984](https://www.jstor.org/stable/2061168?seq=1) explains why the geometric mean might be a better choice : 
  > *"For a given physical size  of area,the difference between a population of 500 and 1,500 is not the same as the difference between 10,000 and 11,000 persons-even though the absolute increase in density is the same in both cases.What is relevant to the people concerned is that in the former case there are three times as many  of them while in thelatter case the increase is only 10 percent.Therefore it is the relative density difference that matters rather than the absolute one."* 

  You can see it as the weighted sum of the magnitudes of local densities. In practice it mostly gives less weight to very crowded city centers.

#### How it works

To make this program work you need three input files : 
- A population gridded dataset in the raster format, usually geotif.
- A corresponding raster file that gives you the area of each individual pixel. Indeed,the cells aren't measured in km2 but in arc-seconds in these datasets and since the earth isn't a perfect sphere, the cells aren't of the same size everywhere. So you need it to calculate accurate pixel level density numbers. You can get this by using the Area function from the Raster library in R on your main raster file.(do note that some datasets are available in km instead of arc seconds which makes things much simpler, but not all of them)
- And third, you need a shapefile containing the polygons of all the regions for wich you want to compute the numbers. I use the awesome [gadm database](https://gadm.org/) for this.

What it does for each subregion: 
- Take the input raster image for both population count and cells size and clip them based on a given polygon to produce a smaller regional raster.
- Turn it into a pandas DataFrame and compute all the metrics. For this I convert each band into a numpy array and keep only the cells with population superior or equal to 0 and area strictly superior to zero.
- Repeat the process three times at 1km, 5km and 10km pixel resolution by downsampling the raster each time using the sum resampling algorithm from gdalwarp

The gdal clipping algorithm is good, however it sometimes excludes relevant cells since it takes into account only the pixels that have their centroid inside the polygon and discard the others. The gdal resampling algorithm is mostly good when dowsampling from 1km to 5km, although there can be mistakes, but a bit less so to 10km, sometimes even giving totally false numbers. 

In practice all you have to do is put the path of your input files in the "to_process.csv" and then launch the program. You can execute it on several datasets and several shapefiles, one per row. You must have the gdal and fiona libraries installed.

#### The numbers

They are a mess. They vary a lot across datasets, so much that I'm not sure they are very reliable at all. I expected the numbers to be different because the datasets don't all mesure exactly the same thing but not by that much. Either my calculations are totally wrong or the methods and inputs of the datasets are just too different from one another and we shouldn't count on them to give us reliable numbers.

I checked my calculations with this [paper](https://arxiv.org/pdf/2005.01167.pdf) which is pretty much the only one that has computed population weighted density estimates at country level, using the worldpop dataset. I found the same numbers except for a few anomalies so I assumed this should work for the other datasets. But maybe this is not the case and we should use custom methods for each dataset? I don't know. 

In "outputs", besides the raw numbers, you can find :
- A big file with all the cleaned results in one place.
- A similar file specifically for Europe, with estimates for all NUTS regions at each level and a comparison with official population numbers;
- A similar file for the US, with estimates for each county. Weirdly, this is the only one where the estimates are similar accross the 4 datasets.
- An excel file with comparisons of the metric across scales and datasets



