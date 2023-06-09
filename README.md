## Introduction

`PMC-AB` aims to mimic CiteAB's functionaliy as an Antibody citation search engine.

Currently we search articles on EuropePMC.

This software is packaged as a Python module.

## Workflow

For a given input that uniquely identifies a commercially available antibody,
this program generates EuropePMC-compatible search queries that will return articles that cite that antibody.

Queries are generated by replacing previously-known templates that represent ways that a antibody can be referenced in academic texts

### Input

Antibody data: `SKU`, `CLONE_ID`, `MANUFACTURER`, ``

### Query templates

```
$SKU $MANUFACTURER
#$TARGET*$CLONE
#$MANUFACTURER AND $CLONE
#$SKU AND $MANUFACTURER
"$TARGET \(Clone #$CLONE, $MANUFACTURER"
"$TARGET antibody \($CLONE; $MANUFACTURER"
"$MANUFACTURER clone $CLONE"
"$MANUFACTURER, clone $CLONE"
```

### Built queries

Applying antibody information to our query templates yield a list of independent queries:

```
"CD4 \(Clone #RM4-5, BD Biosciences"
"CD4 \(Clone #RM4-5, BDBiosciences"
"CD4 \(Clone #RM4-5, BD-Biosciences"
"CD4 antibody \(RM4-5; BD Biosciences"
"CD4 antibody \(RM4-5; BDBiosciences"
"CD4 antibody \(RM4-5; BD-Biosciences"
"BD Biosciences clone RM4-5"
"BDBiosciences clone RM4-5"
"BD-Biosciences clone RM4-5"
"BD Biosciences, clone RM4-5"
"BDBiosciences, clone RM4-5"
"BD-Biosciences, clone RM4-5"
```

We can combine independent queries with `OR` directives so we can query all of them in a single API call:
```
(550280 BD Biosciences) OR (550280 BDBiosciences) OR (550280 BD-Biosciences) OR ("CD4 \(Clone #RM4-5, BD Biosciences") OR ("CD4 \(Clone #RM4-5, BDBiosciences") OR ("CD4 \(Clone #RM4-5, BD-Biosciences") OR ("CD4 antibody \(RM4-5; BD Biosciences") OR ("CD4 antibody \(RM4-5; BDBiosciences") OR ("CD4 antibody \(RM4-5; BD-Biosciences") OR ("BD Biosciences clone RM4-5") OR ("BDBiosciences clone RM4-5") OR ("BD-Biosciences clone RM4-5") OR ("BD Biosciences, clone RM4-5") OR ("BDBiosciences, clone RM4-5") OR ("BD-Biosciences, clone RM4-5")

```

## Validation

To validate search results, we compare to the .xlsx reference, which is based on CiteAB results.

Application execution two type of files:

1. A `.csv` record containing overall statistics:

|Antibody ID          |Fulfillment Rate|Fulfillment rate PMC|False Positive Rate|Search Hit Count|Search N|Agreement N|Benchmark N (CiteAB)|
|---------------------|----------------|--------------------|-------------------|----------------|--------|-----------|--------------------|
|BD Biosciences:550280|63.76%          |78.54%              |95.13%             |6952            |6900    |336        |527                 |
|Invitrogen:11-0041-82|35.95%          |39.77%              |96.31%             |4471            |4472    |165        |459                 |
|Abcam:ab183685       |80.71%          |97.66%              |16.31%             |325             |325     |272        |337                 |
|BioLegend:100401     |92.47%          |87.61%              |94.38%             |5467            |5467    |307        |332                 |
|Abcam:ab133616       |77.62%          |93.33%              |29.75%             |316             |316     |222        |286                 |
|R&D Systems:AF1828   |66.67%          |90.0%               |4.76%              |42              |42      |40         |60                  |
|R&D Systems:BAF1828  |71.43%          |100.0%              |0.0%               |20              |20      |20         |28                  |



2. A list of articles that were retrieved by the application but were not in the `.xlsx` records, one per antibody.

## Usage

### Setup

Usual Python package setup:

``` sh

pip install -r requirements.txt
pip install .
```

### Execution

To evaluate all antibody records and produce result records.
Files will be created in the current directory, which can be any.

``` sh
pmcab -a
```



