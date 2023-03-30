from PIL import Image
import requests
from io import BytesIO

# This is script may only work with sentinelhub.__version__ >= '3.4.0'
from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox, SHConfig, Geometry

# Credentials
config = SHConfig()
config.sh_client_id = "cf51093c-bb8c-460b-afcb-4ebdf5683389"
config.sh_client_secret = "1bR{tG0nC7AwrV%taXd?|3I),>TQnBCt|cqDri56"
evalscript = """
//VERSION=3
function setup() {
    return {
        input: ["B02", "B08", "B03", "B04", "B11", "dataMask"],
        output: { bands: 4 },
        mosaicking: "TILE"
    };
}

var artifactPrecision = 80; //%

function calculateValue(sample){
    let bai = index(sample.B08, sample.B02);
    let ndwi = index (sample.B03, sample.B08);
    let ndvi = index (sample.B08, sample.B04);
    let ndisi = index (sample.B03, sample.B11);
    if(ndwi < 0.0 && bai < 0.47 && ndvi < 0.37 /*&& ndisi < -0.3*/)
        return [1];
    else
        return [0];
}

function preProcessScenes (collections) {
    var oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    var sevenMonthsAgo = new Date();
    sevenMonthsAgo.setMonth(sevenMonthsAgo.getMonth() - 7);
    
    collections.scenes.tiles = collections.scenes.tiles.filter(function (tile) {
        var tileDate = new Date(tile.date);
        if(tileDate > sevenMonthsAgo && tileDate < oneMonthAgo)
            return tile.cloudCoverage < 5;
    })
    return collections
}

function evaluatePixel(samples, scenes) {

    var countAll = 0;
    var countValid = 0;
    for(var i = 0; i < samples.length; i++)
    {
        if(samples.dataMask != 0){
            if(calculateValue(samples[i]) == 1)
                countValid++;
            else
                countAll++;
        } 
    }
    countAll += countValid;
    if(countValid >= (countAll * (artifactPrecision / 100)))
        return [1, 0, 0, 1];
    else
        return [0,0,0,0];
}
"""
bbox = BBox(bbox=[10.671472, 60.001029, 10.682879, 60.007002], crs=CRS.WGS84)

request = SentinelHubRequest(
    evalscript=evalscript,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L2A,          
            time_interval=('2022-02-28', '2023-03-30'),          
        ),
    ],
    responses=[
        SentinelHubRequest.output_response('default', MimeType.PNG),
    ],
    bbox=bbox,
    size=[629.563, 659.331],
    config=config
)

response = request.get_data()
image = response[0]
print(image)
plot_image(image, factor = 1/255, clip_range=(0,1))