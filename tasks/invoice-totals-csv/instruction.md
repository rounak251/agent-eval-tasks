Finance says the totals from our invoice tool don't match their spreadsheet. For March the tool came out a few thousand lower, and nobody noticed for weeks because it never complained.

You run it as `python -m invoicing <file.csv>`, and it prints the grand total. The export comes from the sales system with the columns `sku,description,quantity,unit_price`. Prices are formatted for people, so you will see things like `"1,200.50"` and `$15.00`, and the sales team leaves quantity blank for single items. Credit lines have a negative price.

What finance needs:
- the total must match the spreadsheet to the cent. Each line is quantity × unit price, and the grand total is rounded half-up to 2 decimals and printed like `12345.67`.
- if a row can't be understood, don't guess and don't skip it. Exit with a non-zero status and print an error to stderr that includes the line number in the file (header is line 1), so they can fix the export.

The code is in `/app/invoicing/`. There's a sample export in `/app/samples/march.csv`.
