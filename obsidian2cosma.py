"""Convert an Obsidian vault into a collection of Markdown notes readable by Cosma (https://cosma.graphlab.fr/en/)

Usage: python obsidian2cosma.py -i input_folder_path -o output_folder_path
                                [--type TYPE] [--tags TAGS]
                                [--typedlinks TYPEDLINKS] [--semanticsection SEMANTICSECTION]
                                [--creationdate CREATIONDATE] 
                                [--verbose]

Optional arguments:
  --h, --help                           Show this help message
  --type TYPE                           Select notes with type TYPE (e.g --type "article")
  --tags TAGS                           Select notes with tags TAGS (e.g --tags "philosophy truth")
  --typedlinks TYPEDLINKS               Syntax of typed links modified if TYPEDLINKS=True (e.g --typedlinks True)
  --semanticsection SEMANTICSECTION     Specify in which section typed links are (e.g --semanticsection "## Typed links")
  --creationdate CREATIONDATE           Fill ID with file creation date if CREATIONDATE=True (e.g --creationdate True)
  --v, --verbose                        Print changes in the terminal

Author: Kévin Polisano 
Contact: kevin.polisano@cnrs.fr

License: GNU General Public License v3.0

"""

import os
import platform
import argparse
import re
import shutil
import csv
import unicodedata
from datetime import datetime as dt
from pathlib import Path

# Create an ArgumentParser object
parser = argparse.ArgumentParser()

# Add command line arguments
parser.add_argument("-i", "--input", help="Path to the input folder", required=True)
parser.add_argument("-o", "--output", help="Path to the output folder", required=True)
parser.add_argument("--type", help="Select notes with type TYPE (e.g --type 'article')", default=None)
parser.add_argument("--tags", help="Select notes with tags TAGS (e.g --tags 'philosophy truth')", default=None)
parser.add_argument("--typedlinks", help="Syntax of typed links modified if TYPEDLINKS=True (e.g --typedlinks True)", default=False)
parser.add_argument("--semanticsection", help="Specify in which section typed links are (e.g --semanticsection '## Typed links')", default=None)
parser.add_argument("--creationdate", help="Fill ID with file creation date if CREATIONDATE=True (e.g --creationdate True)", default=False)
parser.add_argument("--zettlr", help="Use Zettlr syntax for wiki-links if ZETTLR=True", default=False)
parser.add_argument("-v", "--verbose", action='store_true', help='Print changes in the terminal')

# Parse the command line arguments
args = parser.parse_args()

# Input and output folders path
input_folder = args.input
output_folder = args.output

# Print function displaying text if option --verbose is used
def printv(text):
  if args.verbose:
      print(text)

# Initialize an ID with the current date timestamp
global currentId
currentId = int(dt.fromtimestamp(dt.now().timestamp()).strftime('%Y%m%d%H%M%S'))

def creation_date(file):
  """
  Try to get the date that a file was created, falling back to when it was
  last modified if that isn't possible.
  See http://stackoverflow.com/a/39501288/1709587 for explanation.
  """
  if platform.system() == 'Windows':
    return os.path.getctime(file)
  else:
    stat = os.stat(file)
    try:
      return stat.st_birthtime
    except AttributeError:
      # We're probably on Linux. No easy way to get creation dates here,
      # so we'll settle for when its content was last modified.
      return stat.st_mtime

def copy_system_birthtime(source, destination):
  """Assign the creation date of source file to destination file"""
  # Get the creation date of source file
  timestamp = creation_date(source)
  # Convert in the format YYYYMMDDHHmm.ss (see man touch)
  birthtime = dt.fromtimestamp(timestamp).strftime('%Y%m%d%H%M.%S')
  # Assign source file's creation date to destination's one (but also overwrite access and modification dates)
  # Can use instead on Mac OSX: SetFile -d "$(GetFileInfo -d source)" destination to avoid this issue
  str_cmd = "touch -t " + birthtime + " " + "\"" + destination + "\"" 
  os.system(str_cmd)

def create_id(file) -> str:
  """Function to create an 14 digit id by timestamp (year, month, day, hours, minutes and seconds) corresponding to the file creation date"""
  global currentId
  # If the files creation date are available
  if args.creationdate:
    # Retrieve the file creation date
    timestamp = creation_date(file)
    # Convert the date to a string in the format YYYYMMDDHHMMSS
    return dt.fromtimestamp(timestamp).strftime('%Y%m%d%H%M%S')
  # Otherwise create ad-hoc IDs by incrementing the current ID (initialized with current date)
  else:
    currentId = currentId + 1
    return currentId

def parse_yaml_front_matter(content):
  """Parses YAML front matter from a Markdown file."""
  match = re.match(r"^---\n(.*?)\n---(.*)", content, re.DOTALL)
  if match:
    front_matter = match.group(1)
    content = match.group(2)
    data = {}
    for line in front_matter.split("\n"):
      key_value = line.split(": ")
      if len(key_value) < 2:
        continue
      key, value = key_value
      # Parse values as integers or floats if possible, otherwise keep as string
      try:
        value = int(value)
      except ValueError:
        try:
          value = float(value)
        except ValueError:
          pass
      # Convert the tags field to a list if necessary
      if key == "tags":
        if isinstance(value, str):
          # Remove the brackets from the string
          value = value.strip("[]")
          # Split the string on commas and store the resulting list of tags
          value = value.split(",")
          # Strip any leading or trailing whitespace from each tag
          value = [tag.strip() for tag in value]
      data[key] = value
    return data, content
  return {}, content

def filter_files(root, files, type=None, tags=None):
  """Filters a list of Markdown files based on the given type and tags, and images."""
  filtered_files = []
  for file in files:
    # Select Markdown files
    if file.endswith(".md"):
      file_path = os.path.join(root, file)
      with open(file_path, "r") as f:
        content = f.read()
        # Extract the YAML front matter
        front_matter, _ = parse_yaml_front_matter(content)
        if tags:
          # Check for tags in the front matter
          yaml_tags = front_matter.get("tags", [])
          if isinstance(yaml_tags, str):
            yaml_tags = [yaml_tags]
          file_tags_set = set(yaml_tags)
          printv("\t - YAML tags: {}".format(file_tags_set))
          # Check for tags in the content
          content_tags = re.findall(r"#(\w+)", content)
          printv("\t - Content #tags: {}".format(set(content_tags)))
          file_tags_set = file_tags_set.union(set(content_tags))
          printv("\t - All file tags: {}".format(file_tags_set))
          # Set of tags passing in arguments
          if isinstance(tags, str):
            if " " in tags:
              tags_temp = tags.split()
            else:
              tags_temp = [tags]
          filter_tags_set = set(tags_temp)
          printv("\t - Filter tags: {}".format(filter_tags_set))
          # Compare the two sets of tags: if filter TAGS are not part of file tags then it is not selected
          if not filter_tags_set.issubset(file_tags_set):
            printv("[IGNORED] {} (missing tags)".format(file))
            continue
        # If type field is missing then the file is not selected
        if type and "type" not in front_matter:
          printv("[IGNORED] {} (missing type)".format(file))
          continue
        # If type field exists but is not consistent with TYPE then the file is not selected
        if type and "type" in front_matter and front_matter["type"] != type:
          printv("[IGNORED] {} (different type)".format(file))
          continue
        # Otherwise the file is selected
        printv("[SELECTED] {}".format(file))
        filtered_files.append(file)
    if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
      printv("[SELECTED] {}".format(file))
      filtered_files.append(file)
  return filtered_files

def copy_and_filter_files(input_folder, output_folder):
  """Function to copy all Markdown files and images from the input folder and its subfolders to the output folder"""
  printv("\n=== Filtering files and copying them in the output folder ===\n")
  for root, dirs, files in os.walk(input_folder):
    # Ignore subfolders that start with an underscore
    dirs[:] = [d for d in dirs if not d.startswith("_")]
    # Filter Markdown files based on the given type and tags
    filtered_files = filter_files(root, files, type=args.type, tags=args.tags)
    for file in filtered_files:
      # Copy current file from the input folder to output folder
      shutil.copy2(os.path.join(root, file), output_folder) # copy2() preserve access and modifications dates
      copy_system_birthtime(os.path.join(root, file), os.path.join(output_folder, file)) # but birthtime (= creation date) has to be set up manually
  
def metadata_init(files) -> dict:
  """Function to initialize metadata and save them in a csv file
  Find (or create) the title and id fields in the YAML frontmatter of all Markdown files
  Return a dictionary title2id["title"] = "id"
  """
  printv("\n=== Initialize or complete metadata of filtered files ===\n")
  title2id = {}
  for file in files:
    with open(file, "r", encoding="utf-8") as f:
      content = f.read()
    # Extract the YAML front matter
    front_matter, _ = parse_yaml_front_matter(content)
    # Search for the ID and title fields
    id = front_matter.get("id")
    title = front_matter.get("title")
    # At this stage no ID or title are created
    idcreated = False
    titlecreated = False
    # If the id field does not exist, then create one
    if id is None:
      id = create_id(file)
      printv('[COMPLETED] {}:\n \t - Id {} created'.format(os.path.basename(file),id))
      # Search for the YAML front matter
      match = re.match(r"^---\n(.*?)\n---(.*)", content, re.DOTALL)
      # Insert the ID field in the YAML front matter
      if match:
        content = content.replace("---", "---\nid: {}".format(id), 1)
      else:
        content = "---\nid: {}\n---\n".format(id) + content
      idcreated = True
      with open(file, "w", encoding="utf-8") as f:
        f.write(content)
    # If the title field does not exist, then create one
    if title is None:
        # Extract the filename (file without path and extension)
        title = Path(file).stem
        if idcreated:
          printv('\t - Title created')
        else:
          printv('[COMPLETED] {}:\n \t - Title created'.format(os.path.basename(file)))
        with open(file, "r", encoding="utf-8") as f:
          content = f.read()
        # Search for the YAML front matter
        match = re.match(r"^---\n(.*?)\n---(.*)", content, re.DOTALL)
        # Insert the title field in the YAML front matter
        if match:
          content = content.replace("---", "---\ntitle: {}".format(title), 1)
        else:
          content = "---\ntitle: {}\n---\n".format(title) + content
        titlecreated = True
        with open(file, "w", encoding="utf-8") as f:
          f.write(content)
    # No ID or title have been created means the file already contains ones
    if not idcreated and not titlecreated:
      printv('[OK] {}'.format(os.path.basename(file)))
    # Finally the value "id" is associated to the key "title" in a dictionary
    title2id[title] = id
  # Write the results to a CSV file
  # csvname = os.path.basename(input_folder) + '_title2id.csv'
  csvname = os.path.join(output_folder, '_title2id.csv')
  with open(csvname, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(title2id.items())
  # Return the dictionary
  return title2id

def replace_wiki_links(file, title2id):
  """Function to replace every single wiki-style [[internal link]] in a Markdown file with [[id | internal link]]
  where internal link refers to the title (possibily with an alias) of an other Markdown file
  whose id can be found in the dictionary title2id
  Eventually transforms image wiki-links ![[image.{jpg,jpeg,png}]] to ![](image.{jpg,jpeg,png})"""
  with open(file, "r", encoding="utf-8") as f:
    content = f.read()
  global count # Variable counting the number of links replaced
  count = 0
  # Function replacing one internal link matched
  def replace_wiki_link(match):
    global count
    count = count + 1
    # Extract the [[link_text]]
    link_text = match.group(1)
    # If this link text contains an alias ([[title | alias]])
    if "|" in link_text:
      # Separate the title from the alias
      link_title, link_alias = link_text.split("|")
      # If the title is not in the dictionary, there is no corresponding Markdown file (ghost note)
      if link_title not in title2id:
        return f"[[{link_text}]]" # Keep the original link
      # Otherwise find the corresponding ID of this file
      id = title2id[link_title]
      # If Zettlr syntax: Return [alias]([[id]])
      if args.zettlr:
        return f"[{link_alias.strip()}]([[{id}]])"
      # Return [[id | alias]]
      return f"[[{id}|{link_alias.strip()}]]"
    # Otherwise link_text = title
    else:
      # If the title is not in the dictionary, there is no corresponding Markdown file (ghost note)
      if link_text not in title2id:
        return f"[[{link_text}]]" # Keep the original link
      # Otherwise find the corresponding ID of this file
      id = title2id[link_text]
      # If Zettlr syntax: Return [title]([[id]])
      if args.zettlr:
        return f"[{link_text}]([[{id}]])"
      # Return [[id | title]]
      return f"[[{id}|{link_text}]]"
  # Substitute all wiki links match with replace_wiki_link(match)
  content = re.sub(r"(?<!!)\[\[(.+?)\]\](?!\()", replace_wiki_link, content)
  # Eventually let replace images wiki-link
  pattern = r'!\[\[(.+?\.jpe?g|.+?\.png)\]\]' # ![[image.{jpg,jpeg,png}]]
  matches = re.finditer(pattern, content)
  # Transform ![[image.{jpg,jpeg,png}]] to ![](image.{jpg,jpeg,png})
  for match in matches:
    image_link = match.group(1)
    content = content.replace(match.group(0), '![]({})'.format(image_link))
    count = count + 1
  printv("[{} links replaced] {}".format(count, os.path.basename(file)))
  # Write the results in the file
  with open(file, "w", encoding="utf-8") as f:
    f.write(content)

def transform_typed_links(file):
  """Function to transform typed links as "- prefix [[destination]]" into the format "[[prefix:destination]]"
  prefix is a word characterizing the type of the directional link between the current file and another one (destination)
  In Obsdian, such semantic links can be drawn with the syntax of the Juggl plugin: https://juggl.io/Link+Types
  """
  with open(file, "r", encoding="utf-8") as f:
    content = f.read()
  # Find the section corresponding to SEMANTICSECTION
  if args.semanticsection is not None:
    pattern = r"(?:^|\n)%s[^\n]*\n(.*?)(?=\n##?\s|$)" % args.semanticsection
    match = re.search(pattern, content, re.DOTALL)
    if match:
      printv("Semantic section << {} >> found".format(args.semanticsection))
      # Extract the content of this section
      section = match.group(1)
      # Transform typed links as "- prefix [[destination]]" into the format "[[prefix:destination]]"
      section = re.sub(r"- (.*?) \[\[(.*?)\]\]", r"[[\1:\2]]", section)
      # Substitute the old content section by the new one
      new_string = "{}\n{}\n".format(args.semanticsection, section)
      content = content.replace(match.group(0), new_string)
  # If not found then replace typed links everywhere
  else:
    content = re.sub(r"- (.*?) \[\[(.*?)\]\]", r"[[\1:\2]]", content)
  # Save changes
  with open(file, "w", encoding="utf-8") as f:
    f.write(content)

def rename_file(file):
  """Function to rename a file by removing accents and replacing spaces with hyphens"""
  # Remove accents
  new_name = unicodedata.normalize("NFD", file).encode("ascii", "ignore").decode("utf-8")
  # Replace spaces with hyphens
  new_name = new_name.replace(" ", "-")
  # Write the new filename
  os.rename(file, new_name)

def main():
  # If the output folder does not exist, then create one
  Path(output_folder).mkdir(parents=True, exist_ok=True)

  # Copy all Markdown files and images from the input folder and subfolders to the output folder
  copy_and_filter_files(input_folder, output_folder)

  # Store the list of Markdown files within the output folder
  filenames = [file for file in os.listdir(output_folder) if file.endswith(".md")]
  files = [os.path.join(output_folder, file) for file in filenames]

  # Initialize YAML metadata of the selected files, fill a dictionary title -> id and save it into a csv file
  title2id = metadata_init(files)

  # Replace links in a format compatible with Cosma
  printv("\n=== Replacing wiki links ===\n")
  for file in files:
    # Replace every single wiki-style [[internal link]] in a Markdown file with [[id | internal link]]
    replace_wiki_links(file, title2id)
    # Transform typed links as "- prefix [[destination]]" into the format "[[prefix:destination]]"
    if args.typedlinks:
      transform_typed_links(file)

  # Rename files by removing accents and replacing spaces with hyphens
  for file in files:
    rename_file(file)

if __name__ == "__main__":
  main()
