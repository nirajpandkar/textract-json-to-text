# Textract JSON to text

> Utility tool to parse and convert the lines into a continuous form of text with line breaks intact.

## Usage

```
from pprint import pprint
from json_to_text import convert

text, tablesJSON = convert(jsonResponse)
print(text)
pprint(tablesJSON)
```