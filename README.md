# density_metrics

*epistemic status : I'm not an academic or a gis specialist. This is just a personal project. If you want to use this, please check my code before.*

This program computes several alternative density metrics for all countries and several subregions using population gridded datasets.

While everyone knows about population density, this number has its limitations, particularly if you want to interpret it as a measure of "crowdedness". The problem is that it takes into account all areas indiscriminately , even vast empty land. For example, the Sahara desert makes up 90% of Algeria's surface, which means Algeria has a fairly low population density. But, because of this huge bias, population density tells us very little about how crowded the remaining 10% land is. 
For more about this problem, you can read this excellent [article](https://theconversation.com/think-your-country-is-crowded-these-maps-reveal-the-truth-about-population-density-across-europe-90345).

Here I try to explore alternatives to traditional population density. My goal is to see whether these metrics are robust, by computing them at 3 different scales across 4 different datasets. I use population gridded datasets, which split land into multiple, equal size, cells and give population count for each of them. There are 4 of them : the worldpop project, Gridded Populations of the World (GPW), the Landscan database and the Global Human Settlement Layer (ghsl).

Here are the metrics :
- First I provide estimates for population, area and population density. This is in order to check that these numbers are accurate compared to official estimates.
- Lived cells : this is the percentage of cells where at least one person lives.
- Lived density : this metric was invented by Alasdair Rae. It's just total population divided by lived area (the sum of lived cells areas). It's the simplest metric since it's the same as population density but without taking into account empty cells.

- Population gini index : this is like the gini index for wealth inequality but applied to population density. Instead of measuring how much wealth is concentrated among a population, it measures how population is concentrated on a given land. At 0, the population is distributed completely equally across all cells, while at 1 all the population is located in one cell and all the others are empty.

- Population weighted density. This is equal to the sum of all the densities of the subareas of a place weighted by the share of the population that lives on them. It means that more populated areas will have more weight in the calculus while empty areas won't have any. Thus it gives a good idea of the density at which the average citizen lives.

- Population weighted density using the geometric mean instead of the arithmetic mean.  Craig, 1984 explains why the geometric mean might be a better choice : *"For a given physical size  of area,the difference between a population of 500 and 1,500 is not the same as the difference between 10,000 and 11,000 persons-even though the absolute increase in density is the same in both cases.What is relevant to the people concerned is that in the former case there are three times as many  of them while in thelatter case the increase is only 10 percent.Therefore it is the relative density difference that matters rather than the absolute one."* In practice it mostly gives less weight to very crowded city centers.

How the program works

To make this program work you need three input files : 
- The population gridded dataset in the raster format, usually geotif.
- A corresponding pixels areas raster file. Indeed,the cells aren't measured in km2 but in arc-seconds in these datasets and since the earth isn't a perfect sphere, the cells aren't of the same size everywhere. That's why you need a raster that gives you the size of each cell in km2 (do note that some datasets are available in km instead of arc seconds which makes things much simpler, but not all of them). You can obtain it using the area function from the Raster library in R.
- And third, you need a shapefile containing the polygons of all the regions for wich you want to compute the numbers. I use the awesome gadm database for this.

What it does for each subregion: 
- Take the raster image of the whole country for both population count and cells size and clip them based on a polygon of the county to produce a smaller regional raster.
- Then merge those two new geotifs into a single multiband raster.
- Turn it into a pandas DataFrame and compute all the metrics.
- Repeat the process three times at 1km, 5km and 10km pixel resolution by downsampling the raster each time using the sum resampling algorithm from gdalwarp
- Finally, put all the data into a Dataframe and save it as a csv.

In practice all you have to do is put the path of your input files in the "to_process.csv" and then launch the program. You can execute it on several datasets, one by row.


The current dataset can be downloaded [here](https://drive.google.com/file/d/1vgFtk9XqVHYdP4CRt-pU7ZJWnXFZhw7W/view?usp=sharing). I want to emphasize that these are only appromixate numbers.




