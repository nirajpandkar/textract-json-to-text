from parse import *
import json
from statistics import median
import glob
import time
import math
from pprint import pprint
import traceback
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
        table_coords = list()
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
            table_coords.append((tbl["StartY"], tbl["EndY"], tbl["PageNumber"], tbl["TableIndex"]))

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
        exists = list()
        len_tablenos = 0
        total_lines = len(page.lines)

        for lineno, line in enumerate(page.lines):
            topY = line.geometry.boundingBox.top
            bottomY = line.geometry.boundingBox.top + line.geometry.boundingBox.height
            ydiff = line.geometry.polygon[-1].y - prevY
            # #print("Diff: {}".format(ydiff))
            
            try:           
                for startY, endY, pageno, tableno in table_coords:
                    if(topY > startY and bottomY < endY):
                        if((pageno, tableno) not in exists):
                            text += "\n\n[# PageNo " + str(pageno) + " TableNo " + str(tableno) + " START #]\n"
                            exists.append((pageno, tableno))
                        text += "\n" + line.text
                        
                        # If the line is a "table line" AND it's the last line on that page, insert an END marker
                        # Needed to do this because it wouldn't go past this stage to the next if block; credit to it being the last line of that page.
                        if(lineno == total_lines - 1):
                            text += "\n\n[# PageNo " + str(pageno) + " TableNo " + str(tableno) + " END #]\n"
                        raise Exception("Skipping the table lines :)")

                # the ydiff should be greater than the median + std dev
                # which is set by trial and error (may want to make it dynamic)
                # then introduce a 2 line breaks to distinguish paragraph
                if len(exists) > len_tablenos:
                    text += "\n\n[# PageNo " + str(exists[-1][0]) + " TableNo " + str(exists[-1][1]) + " END #]\n"
                    len_tablenos = len(exists)
                
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
            except:
                pass
                # print(traceback.format_exc())
            prevY = line.geometry.polygon[-1].y
    jsonTables = json.dumps(tables)
    return text, jsonTables

if __name__ == '__main__':
    files = glob.glob("Files/GSTFiles/*.json")
    tables_folder = "OutputTables"
    for file_ in files:
        file_ = "Files/GSTFiles/file_1650_final.json"
        filename = file_.split("/")[-1][:-5]
        with open(file_, "r") as infile:
            responseJson = json.load(infile)
        print("Converting file " + file_)

        text, tableJSON = convert(responseJson)
        with open("Tables/" + file_.split("/")[-1][:-5] + "_tables.json", "w") as outfile:
            outfile.write(tableJSON)
        with open(file_[:-5] + ".txt", "w") as outfile:
            outfile.write(text)
        print("Done!") 
        break

        # Save the tables
        # excel_filepath = os.path.join(tables_folder, filename + ".xlsx")
        # with pd.ExcelWriter(excel_filepath, engine='xlsxwriter') as writer: 
        #     for i, df_ in enumerate(tables_df):   
        #         df_.to_excel(writer, "Table " + str(i)) 
        #     writer.save()

        