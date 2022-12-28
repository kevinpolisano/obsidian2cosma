up:: [[Home]]
tags:: #map #effort 
rank:: 5

# My Newsletter MOC
This note is a simple example of how you can consolidate all of your notes related to an effort into a single spot.

Below is a data view that looks for notes in the `My Newsletters` folder within "Spaces".

``` dataview
TABLE WITHOUT ID
 file.link as "Newsletter",
 dates as "Date Published"

FROM "Spaces/My Newsletters"

SORT file.link desc

LIMIT 20
```