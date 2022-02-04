# Code for Two-Stage Monopsony Experiments on MTurk

## Pipeline Overview

### Part 1: First-Stage HIT

* **[01a_CreateNewQual.ipynb](../../blob/main/code/01a_CreateNewQual.ipynb)**: Create a new qual for the current run
   1. Get info for the previous (most recent) custom qual
   2. Enter the info for the new qual to be created
   3. Create the new qual via MTurk API
   4. And update the locally-stored info on the current qual

* **[01b_PostStage1.ipynb](../../blob/main/code/01b_PostStage1.ipynb)**: Launch N stage-1 HITs
   1. Load the stage-1 task XML data
   2. Set up the two requirements for the stage-1 task
      1. (The first is that they're in the US, the second that they have not been assigned the Workplace_Survey_Participant qual before)
   3. Create and launch the HIT via the API
   4. Get the links to the stage-1 HIT (for verification, if need be)
   5. Save the HIT id for the newly-created stage-1 HIT

* **[01c_MonitorStage1.ipynb](../../blob/main/code/01c_MonitorStage1.ipynb)**: Monitor the stage-1 HITs (eventually getting a list of the N respondents)
   1. Get all HITs since start_cutoff
   2. Print out info on all stage-1 HITs (subset of HITs scraped in prev step) and specify which one(s) to monitor
   3. Check + approve all submissions, and record the worker ids for stage-2 step

### Part 2: Second-Stage (Custom) HITs

* **[02a_PostStage2.ipynb](../../blob/main/code/02a_PostStage2.ipynb)**: Launch N stage-2 HITs, customized for each stage-1 respondent. Importantly, here we assign them both the current-run qual (from step 1) *and* the Workplace_Survey_Participant qual. The latter is given to *all* participants across all runs, to ensure that nobody does it more than once, while the former is given just to track the different "waves" of respondents from different runs.
   1. Get all hits since `date_cutoff`
   2. Get subset of HITs for all workers who submitted the stage 1 hit(s) specified above
   3. For each stage-1 submitter, create, launch, and record info for their custom stage-2 HIT

* **[02b_NotifyStage2.ipynb](../../blob/main/code/02b_NotifyStage2.ipynb)**: Send notifications to the N workers with a link to their custom HIT
   1. Load the .csv containing all launch info from the previous step
   2. Send notifications for all not-already-notified workers
   3. Create a dataset recording notification success/failure and notification time for each worker
   4. Export notification data to Stata format

* **[02c_MonitorStage2.ipynb](../../blob/main/code/02c_MonitorStage2.ipynb)**: Monitor the stage-2 HITs, auto-accepting submissions as they come in.
   1. Get all hits since date_cutoff
   2. Get all workers with the qual for the current run
   3. Get the HITs for each worker id
   4. Get info about + approve the submissions (if any) for these HITs
   5. Transform the downloaded data into a DataFrame for regression, and export in Stata format
   6. But also run the regression via Python here (for Jeff)
   7. And compute the elasticity

### Part 3: Data Merging and Cleaning

* **[03a_CompileResults.ipynb](../../blob/main/code/03a_CompileResults.ipynb)**: Once all stage-2 HIT results are ready (24 hours after they've been launched), download all of the MTurk data via the MTurk API, then merge it with the Qualtrics data to produce the final dataset, ready for regression analysis.
   1. Get all HITs since date_cutoff
   2. Specify the quals for each run you want to include in the compiled results
   3. Get the HITs for each worker across the quals from the previous step
   4. Transform the downloaded data into a DataFrame for regression, and export in Stata format
   5. Check and record any workers who are suspended (As indicated by the API failing to notify them)
   6. Export the dataset, including the suspended user indicator, in Stata format along with current timestamp

* **[03b_MergeQualtrics.ipynb](../../blob/main/code/03b_MergeQualtrics.ipynb)**: Merge the downloaded Qualtrics data (in .xlsx format) into the MTurk results

* **[03c_GenDurationVars.ipynb](../../blob/main/code/03c_GenDurationVars.ipynb)**: Compute additional vars specifying the time gap between HIT acceptance and HIT submission for each user

*  **[03d_LabelVars.ipynb](../../blob/main/code/03d_LabelVars.ipynb)**: Adds labels to the MTurk-Qualtrics merged dataset (with the duration vars), and exports in Stata format with these labels
