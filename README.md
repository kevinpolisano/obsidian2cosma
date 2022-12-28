# Obsidian2cosma

## Description

### Obsidian

[Obsidian](https://obsidian.md/) is a popular Markdown note-taking application in the field of Personal Knowledge Management (PKM), with a big community support and plenty of third-party open source plugins. Obsidian editor is free to use but is not open source. It has some premium features, like syncing and publishing notes online. [Obsidian Publish](https://obsidian.md/publish) is one of these premium features, enabling to share the amazing graph view of the (bidirectional) links between notes. 

### Cosma

[Cosma](https://cosma.graphlab.fr/en/) is an [open source app](https://github.com/graphlab-fr/cosma) which can generate such a graph view, from a directory of text files written in Markdown, in a single HTML file called the **cosmoscope**. It offers a simple way to explore, visualize and share your knowledge graph with others. *Software comes and goes, but data should last*. Plain text are **future-proof**, hence the importance of not making your notes too dependent on a particular software syntax and of being able to migrate them easily.

## A Python script to convert Obsidian vault toward Cosma or Zettlr

- Cosma uses the same syntax as [Zettlr](https://zettlr.com), another great editor geared towards academic work, whose `[[internal links]]` relies on unique identifiers `[[id]]`, in the spirit of the [Zettelkasten method](https://docs.zettlr.com/en/academic/zkn-method/).
- Obsidian is different, as it uses the `[[filename]]` to link note files, which in my opinion is more restrictive in terms of **interoperability**. 

There are at least two good reasons to convert a collection of Markdown files written in Obsidian to make it compatible with Cosma:
- To ensure that your notes will still be readable and editable by other software such as Zettlr (for interoperability and future-proof)
- To be able to **export and share all or part of your knowledge graph with Cosma**, in the form of a single HTML page, simultaneously displaying the notes on the one hand and the graph view on the other.

In practise, the script follows these steps:
1. **Copy files** of your Obsidian vault (input folder) into another directory (output folder) to avoid accidental changes or losses. Folders starting with `_` are ignored.
2. *(Optional)* **Filter Markdown files** in the output folder according to particular type or tags
3. **Create metadata fields** `id` and `title` for each Markdown file where they were missing
4. **Save a CSV file** containing associated pairs `(id, title)` to preserve the correspondence
5. **Replace all wiki-links** `[[filename]]` used in Obsidian to [Zettlr syntax with identifiers](https://docs.zettlr.com/en/academic/zkn-method/) if `--zettlr=True` or (by default) to [Cosma syntax](https://cosma.graphlab.fr/en/docs/cli/user-manual/#links), mixing [Zettlr syntax](https://docs.zettlr.com/en/academic/zkn-method/) and [Obsidian style using alias](https://help.obsidian.md/How+to/Add+aliases+to+note), namely `[[id|alias]]`
6. *(Optional)* **Replace Obsidian typed links** using [Juggl syntax](https://juggl.io/Link+Types) `- prefix [[link]]` to the more flexible syntax of [semantic links in Cosma](https://cosma.graphlab.fr/en/docs/cli/user-manual/#links) `[[prefix:link]]`

## Installation

- **Download** the Python script
- **Install packages** required: os, platform, argparse, Path, datetime, re, shutil, csv, unicodedata

## Usage

 ```bash
 python obsidian2cosma.py -i input_folder_path -o output_folder_path
                        [--type TYPE] [--tags TAGS]
                        [--typedlinks TYPEDLINKS] [--semanticsection SEMANTICSECTION]
                        [--creationdate CREATIONDATE]
                        [--zettlr ZETTLR] 
                        [--verbose]
```

```bash
Optional arguments:
  --h, --help                           Show this help message
  --type TYPE                           Select notes with type TYPE (e.g --type "article")
  --tags TAGS                           Select notes with tags TAGS (e.g --tags "philosophy truth")
  --typedlinks TYPEDLINKS               Syntax of typed links modified if TYPEDLINKS=True (e.g --typedlinks True)
  --semanticsection SEMANTICSECTION     Specify in which section typed links are (e.g --semanticsection "## Typed links")
  --creationdate CREATIONDATE           Fill ID with file creation date if CREATIONDATE=True (e.g --creationdate True)
  --zettlr ZETTLR                       Use Zettlr syntax for wiki-links if ZETTLR=True (e.g --zettlr True)
  --v, --verbose                        Print changes in the terminal
  ```
  
## Examples

In the directory `data/` you will find an example of Obsidian vault called [LYT-Kit](https://www.linkingyourthinking.com/download-lyt-kit).

### `obsidian2cosma` converts `LYT-Kit/` to `LYT-Kit-cosma/`

At the folder root run the Python script:

```bash
python3 obsidian2cosma.py -i data/LYT-Kit -o data/LYT-Kit-cosma --creationdate True --verbose
```

This creates a new folder `LYT-Kit-cosma/` whose Markdown files have their **internal links transformed** as follows:
- `[[filename]]` are replaced by `[[id|filename]]` 
- `[[filename|alias]]` are replaced by `[[id|alias]]`

where `id` is the identifier of the file `filename.md`, that is `title2id["filename"]="id"` with dictionary `title2id` saved in the CSV file `title2id.csv`.

The next step is to use `cosma` to **generate a graph view** of your notes which can be export in a single HTML file.

Once you have installed [Cosma CLI v.2.0.0-beta-1](https://cosma.graphlab.fr/en/docs/cli/user-manual/) go to the output folder and initialize the config file:

```bash
cd data/LYT-Kit-cosma
cosma c
```

It creates a `config.yml` file in which you have to fill the second field with the absolute path of the output folder:

```bash
files_origin: '/path_to_obsidian2cosma/data/LYT-Kit-cosma'
```

Finally, let us create the `cosmoscope.html` by running:

```bash
cosma m
```

![LYT-Kit graph view displayed by Cosma](https://github.com/kevinpolisano/obsidian2cosma/blob/main/data/LYT-Kit/LYT-kit.png)

### `obsidian2cosma --zettlr True` converts `LYT-Kit/` to `LYT-Kit-zettlr/`

At the folder root run the Python script:

```bash
python3 obsidian2cosma.py -i data/LYT-Kit -o data/LYT-Kit-zettlr --creationdate True --zettlr True --verbose
```

This creates a new folder `LYT-Kit-zettlr/` whose Markdown files have their **internal links transformed** as follows:
- `[[filename]]` are replaced by `[filename]([[id]])` 
- `[[filename|alias]]` are replaced by `[alias]([[id]])` 

These files are now readable by [Zettlr](https://docs.zettlr.com/fr/academic/zkn-method/).
  
## Issues

Known bugs in Cosma:
- Alias should not contain special characters (comma, hypens, ...) only words and spaces.
- Title should not contain dates only (e.g 2022-12-26, see on [GitHub](https://github.com/graphlab-fr/cosma/issues/33))

## Related repository

`òbsidian2cosma` converts an Obsidian vault into a collection of Markdown files readable by Cosma and Zettlr. Conversely, it is possible to implement a script `zettlr2obsidian`: [Conversion tool to make Zettlr markdown files be visible in Graph Mode in Obsidian](https://gist.github.com/KarlClinckspoor/4ec995fd506ec6483b8e02d8afc388fc/raw/c787747da28d97080c64077352ec6d41e80ae6f5/conversion.py)

## Contact

Kévin Polisano  (kevin.polisano@cnrs.fr)
