# User Guide for LLM-LCT-sequencing

This is a non-comprehensive user guide for the LLM-LCT-sequencing annotator

1. Visit the link to the Binder instance. This can be found on the [GitHub repository](https://github.com/Sydney-Informatics-Hub/LLM-LCT-sequencing) under the subheading 'Web version'. Currently, the link is https://binderhub.atap-binder.cloud.edu.au/v2/gh/Sydney-Informatics-Hub/LLM-LCT-sequencing/v1.2.6?labpath=annotation-tool.ipynb but this will change when the version changes (note the 'v1.2.6')
2. Wait for the instance to spin-up. This will usually take several minutes. You will know when this is complete when the display changes from a spinning wheel to a static Jupyter notebook page
3. Run the cell. This can be done by: a. Clicking 'Run' and then 'Run all cells', b. Clicking the 'play' button, c. Using the keyboard shortcut. On Mac, it is Command+Return and on Windows it is Control+Enter.
4. At this point the annotator interface should appear. Select 'Unprocessed mode' for first-time usage or 'Preprocessed mode' if you have a sequence file exported from previous use.
5. Upload the files not labelled 'Optional'
6. If in unprocessed mode, enter the OpenAI API key
7. Click load to read the files and construct the clause pairings
8. If in unprocessed mode, click 'Process with LLM' to send the sequences to the OpenAI LLM for analysis
9. Optionally perform manual annotation using the controls on the right
10. Optionally export the data using 'Show export options'. The file downloaded from this option can be re-uploaded later to resume progress in the preprocessed mode
11. Once analysis has been done, data visualisations can be seen below the text/controls display. Hover over the graphs to see customisation options and a screenshot button.

## LLM prompt files

For step 5 of the above instructions, you may optionally upload files configuring the prompt for the LLM. The file paths for the default files can be found below. These files can be edited and uploaded, but their format must remain the same to function.

- LLM definitions default path: schemas/sequencing_types.xlsx
- LLM examples default path: tests/sequencing_examples.xlsx
- LLM prompt default path: schemas/instruction_multiprompt.txt