# Code for Two-Stage Monopsony Experiments on MTurk

## Pipeline Overview

1. [01a_CreateNewQual.ipynb](../../blob/main/code/01a_CreateNewQual.ipynb): Create a new qual for the current run
2. [01b_PostStage1.ipynb](../../blob/main/code/01b_PostStage1.ipynb): Launch N stage-1 HITs
3. [01c_MonitorStage1.ipynb](../../blob/main/code/01c_MonitorStage1.ipynb): Monitor the stage-1 HITs (eventually getting a list of the N respondents)
4. [02a_PostStage2.ipynb](../../blob/main/code/02a_PostStage2.ipynb): Launch N stage-2 HITs, customized for each stage-1 respondent
    a. Importantly, here we assign them both the current-run qual (from step 1) *and* the Workplace_Survey_Participant qual. The latter is given to *all* participants across all runs, to ensure that nobody does it more than once, while the former is given just to track the different "waves" of respondents from different runs.
5. [02b_NotifyStage2.ipynb](../../blob/main/code/02b_NotifyStage2.ipynb): Send notifications to the N workers with a link to their custom HIT
6. [02c_MonitorStage2.ipynb](../../blob/main/code/02c_MonitorStage2.ipynb): Monitor the stage-2 HITs, auto-accepting submissions as they come in.
7. [03a_CompileResults.ipynb](../../blob/main/code/03a_CompileResults.ipynb): Once all stage-2 HIT results are ready (24 hours after they've been launched), download all of the MTurk data via the MTurk API, then merge it with the Qualtrics data to produce the final dataset, ready for regression analysis.