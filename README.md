# ODI Crossref Deposit Pipeline

This tool automates the generation of Crossref-compliant XML metadata for Open Data Institute (ODI) publications. It scrapes publication data directly from URLs provided, resolves author ORCIDs by visiting individual profile pages linked to those URLs, and compiles the data into a schema-validated XML file ready for batch upload.

## Features

* **Automated Scraper:** Extracts title, date, and author lists from ODI "Report" and "Insight" pages.
* **ORCID Resolution:** Follows author profile links to extract and validate ORCID iDs, correcting common formatting errors (e.g., trailing characters).
* **Schema Compliance:** Generates XML strictly adhering to Crossref Schema 5.3.1, ensuring correct element ordering for `contributors`, `titles`, and `affiliations`.
* **Audit Trail:** Produces a companion CSV file detailing exactly what data was scraped for internal records.

## Requirements

* Python 3.8+
* The following Python packages:

```bash
pip install requests beautifulsoup4 pandas

```

## Configuration

1. Open `main.py` in a text editor.
2. **Update Credentials:** Locate the configuration block at the top and ensure the `DEPOSITOR_EMAIL` matches your Crossref account email.
3. **Input Data:** Populate the `records_to_process` list with the URLs and DOIs you wish to process:

```python
records_to_process = [
    {
        "url": "https://theodi.org/insights/reports/example-report",
        "doi": "10.61557/EXAMPLESUFFIX"
    },
    # Add additional records here...
]

```

### User involvement
This requires a user to collect urls for reports they want to upload. However, it also requires them to provide a unique doi for each URL. They can find dois to use in `unused_dois.txt` and copy one doi from the file per url they have in `records_to_process`. However, to ensure sustainability and ease of use, the user is then required to delete from `unused_dois.txt` any dois they use.


## Usage

Run the script from your terminal:

```bash
python main.py

```

The script will process records sequentially. Note that there is a configured delay (0.5s) between requests to avoid overloading the web server.

## Outputs

The script generates two files in the working directory, stamped with the current batch ID (e.g., `ODI_Deposit_20251217`):

1. **`.xml` file:** The primary output. Upload this file directly to the [Crossref Admin Tool](https://doi.crossref.org) under the "Metadata Admin" tab.
2. **`_audit.csv` file:** A flat-file record of titles, DOIs, and resolved authors. Use this to spot-check metadata before uploading the XML.

### User involvement
The `.xml` file requires manual upload to crossref. Neil Majithia (neil.majithia@theodi.org) is currently responsible for this.

The ODI keeps a spreadsheet to track reports and their DOIs, accessible here: https://docs.google.com/spreadsheets/d/1yHVptdEF8--hTXjisNnzGQCMnLYuJjIUm1ochzZKeHU/edit?usp=sharing. Users should use `_audit.csv` to update this spreadsheet after an upload. 

## Troubleshooting

* **XML Validation Errors:** If the upload fails, check the Crossref error log emailed afterward. The script is tuned for the `5.3.1` schema; ensure you are not uploading to an endpoint expecting an older version.
* **Missing Authors:** If an author appears in the CSV but has no ORCID, verify that their profile link on the ODI website works and explicitly lists their ORCID.
* **Connection Errors:** If the script fails to load pages, ensure you are not being rate-limited by the server. Increase `time.sleep()` in the script if necessary.