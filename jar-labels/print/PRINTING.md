# Printing the UCF sample-jar labels

Every label is **100 × 75 mm**. Each design (Options A, B and C) comes as two print-ready PDFs, with fonts embedded and colour running 3 mm past the cut line (bleed).

| File | Use it for |
|---|---|
| `ucf_labels_option_X_A4_home-printer.pdf` | Office or home printers. A4 landscape, 4 labels per page (2 pages), with crop marks. |
| `ucf_labels_option_X_print-shop_bleed.pdf` | Print shops and sticker printers. One label per page, 106 × 81 mm (100 × 75 mm label plus 3 mm bleed on each side). |

## Office / home printer
1. In the print dialog, set the scale to **100% / Actual size**. Turn off "Fit to page" and "Shrink oversized pages".
2. Set orientation to **Landscape** and paper to **A4**. Glossy or matte A4 sticker paper works best.
3. Cut along the lines joined by the crop marks. The extra 3 mm of colour outside the line is meant to be cut away.

## Print shop
Send `…_print-shop_bleed.pdf` and tell them: *"Finished size 100 × 75 mm, artwork includes 3 mm bleed, no crop marks."*
The colours are RGB. Ask the shop to convert them to CMYK, or to send a proof first, if colour matching matters.

Separate 300 dpi PNGs of each label (without bleed) are in `../png/`.

## Clear (see-through) labels — `clear/`
`clear/ucf_labels_option_X_CLEAR_…pdf` are the same designs with **no white background**, so the fertilizer shows through the label. Print them on **clear / transparent sticker film**.

- Text and logos that sit on the clear areas have a thin **white outline** so they stay readable over dark granules (e.g. Compound C and D). That outline needs **white ink**. Ask the print shop for *"clear vinyl/BOPP labels with white ink under the white areas"*.
- Office or home printers (inkjet or laser on clear film) **cannot print white**. The outline won't appear and navy text will be hard to read on dark products. For home printing, Option B or C works best: their text sits on solid blue panels.
- Use **laser** clear film for laser printers and **inkjet** clear film for inkjet printers. Using the wrong type smudges.
- Transparent PNGs (300 dpi) are in `../png/clear/`. `../clear_labels_preview.png` shows each option over dark and light granules.

## Adobe Express versions — `adobe-express/`
The three options are also editable **Adobe Express** documents in your Adobe account. Each option has a white version and a see-through version, with 6 pages each (one label per page) at exactly **100 × 75 mm**. Text, colours and shapes can all be edited in Express. The logo is an image.

`adobe-express/ucf_labels_option_X_ADOBE_100x75mm.pdf` and `…_SEE-THROUGH_ADOBE_…pdf` were exported by Adobe Express. They print at true size with fonts embedded, but they have **no bleed or crop marks**. Use them for quick prints or when you've edited the design in Express.
- For a print shop, the files in this folder (with 3 mm bleed) are still the better choice.
- Adobe Express always adds a white page background to its PDFs. For clear film, use the `clear/` PDFs here: they have no white anywhere.
- The thin white outline behind text in the see-through designs doesn't survive the move to Express. The logo keeps its outline.

`adobe-express/build_express.js` rebuilds the HTML that gets imported into Express (`node build_express.js white|clear`).
