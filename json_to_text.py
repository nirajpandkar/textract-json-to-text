from parse import *
import json
from statistics import median
import glob
import time
import math
from pprint import pprint

def convert(responseJson):
    """
    Returns a text string after parsing the Textract JSON

    Argument: 
        resopnseJson: response JSON that Textracts outputs
    Return: 
        text: Text string with appropriate line breaks
        jsonTables: JSON string of tables in the format required
    """
    doc = Document(responseJson)        

    text = ""
    tables = dict()
    tables["tables"] = list()
    difflist = list()
    for page in doc.pages:
        prevY = 0
        for line in page.lines:
            difflist.append(line.geometry.polygon[-1].y - prevY)
            prevY = line.geometry.polygon[-1].y

    # Calculate median
    med = median(difflist)
    med = round(med, 3)

    start = time.time()
    
    for pageno, page in enumerate(doc.pages):
        
        ## For extracting tables
        for tableno, table in enumerate(page.tables):
            tbl = dict()
            tbl["TableIndex"] = tableno
            tbl["PageNumber"] = pageno + 1
            tbl["Table"] = list()
            tbl["NumberOfRows"] = len(table.rows)
            tbl["NumberOfColumns"] = len(table.rows[0].cells)

            tbl["StartY"] = table.geometry.boundingBox.top
            tbl["EndY"] = table.geometry.boundingBox.top + table.geometry.boundingBox.height
            tbl["StartX"] = table.geometry.boundingBox.left
            tbl["EndX"] = table.geometry.boundingBox.left + table.geometry.boundingBox.width

            for r, row in enumerate(table.rows):
                rows = dict()
                rows["Row"] = list()
                for c, cell in enumerate(row.cells):
                    rows["Row"].append(dict({"Row": r, 
                                             "Column": c, 
                                             "Content": cell.text, 
                                             "Top":cell.geometry.boundingBox.top, 
                                             "Left": cell.geometry.boundingBox.left,
                                             "Height": cell.geometry.boundingBox.height,
                                             "Width": cell.geometry.boundingBox.width}))
                tbl["Table"].append(rows)
            tables["tables"].append(tbl)
        
        ## For extracting normal text
        prevY = 0
        for line in page.lines:
            ydiff = line.geometry.polygon[-1].y - prevY
            # print("Diff: {}".format(ydiff))
            

            # the ydiff should be greater than the median + std dev
            # which is set by trial and error (may want to make it dynamic)
            # then introduce a 2 line breaks to distinguish paragraph
            if(round(ydiff,3) > med + 0.002):
                # print("\n\n" + line.text)
                text += "\n\n" + line.text
            
            # if ydiff contains 3 0s after decimal place (0.0009325) or
            # if ydiff is less than 0, append the text to the previous line
            elif(math.floor(abs(math.log10(abs(ydiff)))) >= 3 or ydiff < 0): 
                # print(" " + line.text)
                text += " " + line.text
            
            # one line break if any other condition
            else:
                # print("\n" + line.text)
                text += "\n" + line.text
            
            prevY = line.geometry.polygon[-1].y
    jsonTables = json.dumps(tables)
    return text, jsonTables

if __name__ == '__main__':
    files = glob.glob("Files/Lease_Agreements_Library_Json's/*.json")

    for file_ in files:
        with open(file_, "r") as infile:
            responseJson = json.load(infile)
        print("Converting file " + file_)

        text, tableJSON = convert(responseJson)

        with open("Tables/" + file_.split("/")[-1][:-5] + "_tables.json", "w") as outfile:
            outfile.write(tableJSON)
        with open(file_[:-5] + ".txt", "w") as outfile:
            outfile.write(text)
        print("Done!")