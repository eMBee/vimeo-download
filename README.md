Downloads segmented audio+video from Vimeo and saves as .mp4

Usage: 'python vimeo_downloader.py http://...master.json?base64_init=1 optional_name'


to use this script, the master url needs to be manually extracted from the page. 

for a more convenient experience use youtube-dl ( http://rg3.github.io/youtube-dl/ )

this script is useful for cases where youtube-dl is unable to find the master url, 
for example on pages that require login or cookies.


to get the master url:

   1. Open the network tab in the inspector
   2. Find the url of a request to the master.json file
   3. Run the script with the url as argument


code merges the following gists:

https://gist.github.com/alexeygrigorev/a1bc540925054b71e1a7268e50ad55cd

https://gist.github.com/tayiorbeii/d78c7e4b338b031ce8090b30b395a46f

https://gist.github.com/paschoaletto/7f65b7e36b76ccde9fe52b74b62ab9df
