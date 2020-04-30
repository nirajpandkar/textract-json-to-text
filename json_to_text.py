from parse import *
import json
from statistics import median
import glob
import time
import math

def convert(responseJson):
    """
    Returns a text string after parsing the Textract JSON

    Argument: 
        resopnseJson: response JSON that Textracts outputs
    Return: 
        text: Text string with appropriate line breaks
    """
    doc = Document(responseJson)        

    text = ""

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
    for page in doc.pages:
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
    return text

if __name__ == '__main__':
    files = glob.glob("Files/Lease_Agreements_Library_Json's/*.json")

    for file_ in files:
        with open(file_, "r") as infile:
            responseJson = json.load(infile)
        print("Converting file " + file_)
        text = convert(responseJson)

        with open(file_[:-5] + ".txt", "w") as outfile:
            outfile.write(text)
        print("Done!")