# Code for Two-Stage Monopsony Experiments on MTurk

## Installation

1. Clone the git repository by executing `git clone https://github.com/jpowerj/mturk-twostage.git` on the command line
2. Move into the directory using `cd mturk-twostage`

## Setup

1. Using the MTurk web interface, [create a qualification](https://requester.mturk.com/qualification_types) for keeping track of *all* participatnts in the study (note that the code will also auto-generate separate qualifications for each *wave* of the study. This one is to make sure nobody participates more than once, even across waves).

![MTurk's create qualification interface](images/create_qual.png)
![Qualification details](images/create_qual_2.png)

2. After submitting the "Create New Qualification Type" form, refresh the page and it should show your newly-created qualification in the displayed list of qualifications:

![Qualification list](images/qual_list.png)

Copy the long alphanumeric ID given in the "ID" column, and paste it in the `.env` file like so (here using the ID given in the screenshot):

```
PARTICIPATION_QUAL_ID=3JNQJJEQY16FR7XUFO39M804EY0UJD
```

3. Following the instructions [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html), generate an Access ID/Secret Access Key pair for your AWS account and add those to the `.env` file as well, like so:

```
AWS_ACCESS_KEY= AKIAIOSFODNN7EXAMPLE
AWS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**IMPORTANT NOTE**: Anyone with this id/secret key pair will have full access to your AWS account, so make sure you DON'T share the `.env` file or commit it to GitHub. To ensure the latter, add `.env` to your [`.gitignore` file](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files) if you're using Git. In the example above I'm using the example access/secret keys from the previously-linked AWS documentation page.

4. Specify whether or not to use the Requester Sandbox via the `SANDBOX` setting in `.env` (`TRUE` to use the sandbox, for testing, or `FALSE` to use the live MTurk marketplace):

```
SANDBOX=TRUE
```

5. Specify a prefix for the per-wave qualifications:

```
WAVE_QUAL_PREFIX=Workplace_Survey
```

With this setting, for example, workers in the first wave will be assigned the qualification "Workplace_Survey_00", the second wave "Workplace_Survey_01", and so on.

6. Specify the number of HITs to be launched per wave [I *strongly* recommend not setting this above 100, since the MTurk API sometimes only returns the first 100 results from a call, even if you follow their instructions and use the continuation/pagination settings :/]:

```
WAVE_NUM_HITS=10
```

7. Specify the reward to be given to workers for completing the first-stage HIT (we don't specify a reward for the second stage, since this is randomly drawn from the wage distribution set in the next step):

```
STAGE1_REWARD=0.10
```

8. Specify the *set* of possible reward amounts to be drawn from when generating the stage-2 custom HIT. These should be comma-separated, without spaces. In our case, for example, the wages were drawn uniformly from among a set of 11 possible values centered around $1.00:

```
STAGE2_REWARDS=0.50,0.90,0.95,0.98,0.99,1.00,1.01,1.02,1.05,1.10,1.50
```

9. Finally, specify the filepaths for the stage-1 and stage-2 question HTML code. These will be converted to the .xml format required by MTurk, which is just a thin wrapper around standard HTML:

```
STAGE1_HTML_FPATH=question_stage1.html
STAGE2_HTML_FPATH=question_stage2.html
```

Note that, in the .html file for the *second* stage hit, you can (and most likely will want to) include "!worker_id!" and "!offer_amt!" placeholders in your code, which will then be filled with the appropriate values when the custom stage-2 HITs are generated. For example, if your `question_stage1.html` contains:
```
<p>Hello !worker_id!</p>
<p>You will receive a bonus of $!offer_amt! for completing our survey.</p>
```

Then the generated HTML for a worker with id `FAKEID123` and offer amount of $1.00 will be:
```
<p>Hello FAKEID123</p>
<p>You will receive a bonus of $1.00 for completing our survey.</p>
```
Though, in most cases, you'll just want to use these to store hidden inputs, so that they'll be included in the MTurk results data. For example, if your `question_stage2.html` is instead
```
<input type="hidden" name="worker_id" value="!worker_id!" />
<input type="hidden" name="offer_amt" value="!offer_amt!" />
```
then the results file generated by MTurk will contain `Input.worker_id` and `Input.offer_amt` columns, which you can use in your post-survey analysis.

Now you can start running the pipeline, starting with `01a_CreateNewQual.ipynb`, or change the default global constants in `mtglobals.py` before running:

* `date_cutoff`: Any hits before this date won't get downloaded by `download_all_hits()`
* `stage1_submit_list_fpath`: filepath for the list of workers who submitted stage 1. Generated by 01_MonitorStage1.ipynb
* `stage1_results_fpath`: filepath for the .csv containing the *results* of the stage 1 HIT (as in, including their responses to the 3 demographic questions we ask)
* `stage2_launched_fpath`: filepath for the .csv where each row is a launched stage 2 HIT
* `stage2_submitted_fpath`: filepath for the .pkl containing the list of workers who *submitted* their custom stage-2 HIT
* `local_tz`: The `pytz` object representing the local timezone (defaults to US/Pacific), for datetime localization

## The Pipeline

### Part 1: Generate and Launch First-Stage HIT

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
   1. Get all HITs since `start_cutoff`
   2. Print out info on all stage-1 HITs (subset of HITs scraped in prev step) and specify which one(s) to monitor
   3. Check + approve all submissions, and record the worker ids for stage-2 step

### Part 2: Generate and Launch Second_Stage (Custom) HITs

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
   1. Get all hits since `date_cutoff`
   2. Get all workers with the qual for the current run
   3. Get the HITs for each worker id
   4. Get info about + approve the submissions (if any) for these HITs
   5. Transform the downloaded data into a DataFrame for regression, and export in Stata format
   6. But also run the regression via Python here (for Jeff)
   7. And compute the elasticity

### Part 3: Data Merging and Cleaning

* **[03a_CompileResults.ipynb](../../blob/main/code/03a_CompileResults.ipynb)**: Once all stage-2 HIT results are ready (24 hours after they've been launched), download all of the MTurk data via the MTurk API, then merge it with the Qualtrics data to produce the final dataset, ready for regression analysis.
   1. Get all HITs since `date_cutoff`
   2. Specify the quals for each run you want to include in the compiled results
   3. Get the HITs for each worker across the quals from the previous step
   4. Transform the downloaded data into a DataFrame for regression, and export in Stata format
   5. Check and record any workers who are suspended (As indicated by the API failing to notify them)
   6. Export the dataset, including the suspended user indicator, in Stata format along with current timestamp

* **[03b_MergeQualtrics.ipynb](../../blob/main/code/03b_MergeQualtrics.ipynb)**: Merges the downloaded Qualtrics data (in .xlsx format) into the MTurk results

* **[03c_GenDurationVars.ipynb](../../blob/main/code/03c_GenDurationVars.ipynb)**: Computes additional vars specifying the time gap between HIT acceptance and HIT submission for each user

*  **[03d_LabelVars.ipynb](../../../../blob/main/code/03d_LabelVars.ipynb)**: Adds labels to the MTurk-Qualtrics merged dataset (with the duration vars), and exports in Stata format with these labels

## List of Client functions in `mtclient.py`

Here, and in the next section, we just list the *names* of each function, with links to their documentation entry in [the Wiki](../../wiki).

To use `mtclient.py`, place the following code at the top of your code file:
```
from mtclient import MTClient
```
and then create the client using
```
client = MTClient()
```
If you set the values in the `.env` file correctly (as described above), running this code will print out your AWS account's current balance.


* [`assign_qual_safe()`](../../wiki#assign_qual_safe)
* [`assign_stage2_quals()`](../../wiki#assign_stage2_quals)
* [`create_new_qual()`](../../wiki#create_new_qual)
* [`download_all_hits()`](../../wiki#download_all_hits)
* [`get_all_quals()`](../../wiki#get_all_quals)
* [`get_hit_submissions()`](../../wiki#get_hit_submissions)
* [`get_qual_id()`](../../wiki#get_qual_id)
* [`get_workers_with_qual()`](../../wiki#get_workers_with_qual)
* [`launch_custom_hit()`](../../wiki#launch_custom_hit)
* [`notify_worker()`:](../../wiki#notify_worker)
* [`qual_exists()`](../../wiki#qual_exists)

## List of Global Functions in `mtglobals.py`

* [`add_posted_worker()`](../../wiki#add_posted_worker)
* [`check_launched()`](../../wiki#check_launched)
* [`draw_random_wage()`](../../wiki#random_wage)
* [`gen_custom_hit()`](../../wiki#gen_custom_hit)
* [`gen_custom_msg()`](../../wiki#gen_custom_msg)
* [`gen_qual_restriction()`](../../wiki#gen_qual_restriction)
* [`gen_timestamp()`](../../wiki#gen_timestamp)
* [`gen_xml()`](../../wiki#gen_xml)
* [`get_current_qual()`:](../../wiki#get_current_qual)
* [`get_hit_for_worker()`](../../wiki#get_hit_for_worker)
* [`localize_datetime()`](../../wiki#localize_datetime)
* [`parse_stage1_answer()`](../../wiki#parse_stage1_answer)
* [`update_current_qual()`](../../wiki#update_current_qual)
* [`update_launched_worker()`](../../wiki#update_launched_worker)
* [`worker_id_from_title()`](../../wiki#worker_id_from_title)
* [`write_log(msg)`](../../wiki#write_log)
