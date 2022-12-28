up:: [[Home]]
tags:: #map/view 

# The Outbox 📤
This is a place to track your various *outputs*. 

Below is a simple example of a data view that is looking for any note that has the tag: `output`

This is enough to get you started. Over time, you will probably want extra custom views.

```dataview
TABLE WITHOUT ID
 file.link as Outputs,
 tags as Tags
 
FROM #output 

SORT file.name asc
```
