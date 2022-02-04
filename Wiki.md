**See [README.md](../) for overview of the important global vars and pipeline steps. This wiki documents all of the functions in `mtglobals.py`, in all their gory detail.**

## Global Functions in `mtglobals.py`

### `add_posted_worker()`

* *Arguments:* cur_worker_id, cur_offer_amt, cur_qual_name, cur_qual_id, cur_qual_num, custom_url, launched_time)`
* Once a worker's custom stage-2 HIT has been posted, add their info (and the
    HIT info) to the .csv at `stage2_launched_fpath` (the global constant above)
* Returns the fpath of the newly-updated .csv file

### `assign_qual_safe()`

* *Arguments:*
    * client, worker_id, qual_id, qual_num=0, notify=False
* Assigns the qualification "safely", meaning that it just returns without doing anything if the worker already has the qual

### `assign_stage2_quals()`

* *Arguments:* (client, cur_worker_id, cur_qual_name, cur_qual_id, cur_qual_num, cur_offer_amt):
* Assigns the stage-2-specific quals. The first is the custom qual for this run, with the worker's specifical qual num. The second is the *participation* qual, given to every participant across all runs (to ensure nobody does it
    twice, across different runs)
* Returns the raw API response to the `associate_qualification_with_worker()`
    call (and thus ignores the response to the participation qual assignment! So
    be careful if something goes wrong with the participation quals -- you can
    change this to return that API response instead, or both responses in a tuple)

### `check_launched()`

* *Arguments:* launched_df, worker_id):
* Checks `launched_df` to see if the 2nd-stage hit has already been launched
    for this worker. If so, return the qual_name, qual_num and offer_amt they
    were assigned, otherwise return "",-1,-1

### `create_new_qual()`

* *Arguments:* client, new_qual_name
* Creates a qual with name `new_qual_name`, and returns a (new qual name, new qual id) tuple

### `download_all_hits()`

* *Arguments:* client, start_cutoff=date_cutoff, end_cutoff=None, save_to_file=True):
* Sets end_cutoff to be (localized) datetime.datetime.now() if None.

### `gen_client()`

* *Arguments:*
  * `keys_fpath`: defaults to the global constant `default_keys_fpath` defined above, but can pass a custom fpath if running on Colab, for example
* By default, HITs are created in the free-to-use Sandbox. Change the top line of code to set it to create the HITs in the real production version of MTurk.

### `gen_custom_hit()`

* *Arguments:* (cur_worker_id, cur_offer_amt):
* Construct custom stage-2 HIT for worker `cur_worker_id`, with offer amount
    `cur_offer_amt`.
* Roughly based on the example xml given in this tutorial:
    https://github.com/aws-samples/mturk-code-samples/blob/master/Python/my_question.xml

### `gen_timestamp()`

* *Arguments:* None
* Helper function, generates a (string) timestamp string with format YMD_hms, just so
    the timestamps are uniform across the pipeline.

### `gen_qual_restriction()`

* *Arguments:* cur_qual_id, cur_qual_num
* Generates the object (dict) specifying the restriction specific to this user's stage-2 HIT (that they have the current-run qual with id `cur_qual_id`, and the specific qual num specified by `cur_qual_num`. Returns list of requirements that can be directly passed to the API's post HIT function.
* Roughly based on this example of using qualification to restrict responses to Workers who have had at least 80% of their assignments approved: http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs

### `get_all_quals()`

* *Arguments:* client
* API syntax for listing the existing quals:
  ```
    response = client.list_qualification_types(
        Query='string',
        MustBeRequestable=True|False,
        MustBeOwnedByCaller=True|False,
        NextToken='string',
        MaxResults=123
    )
    ```
* Documentation here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html#MTurk.Client.list_qualification_types

### `get_current_qual()`

* *Arguments:* None
* Gets the info for the qual being used for the current run

### `get_hit_for_worker()`

* *Arguments:* all_hits, worker_id, verbose=False
* Looks in the list `all_hits` and returns the entry representing the custom HIT created for the worker with id `worker_id`

### `get_hit_submissions()`

* *Arguments:* client, hit_id
* Returns a list where each element is MTurk's info about a particular submission of the HIT with id `hit_id`

### `get_qual_id()`

* *Arguments:* (client, qual_name):
* Gets the MTurk-assigned id for the qualification type with name `qual_name`

### `get_workers_with_qual()`

* *Arguments:* client, qual_name
* Returns (after getting the id for the given qual name via `get_qual_id()`) a list of all worker_ids who have been granted the qualification with name `qual_name`

### `launch_custom_hit()`

* *Arguments:* (client, cur_worker_id, cur_offer_amt, stage2_question,
                      stage2_requirements):
* Launch the custom stage-2 HIT with the specified parameters via MTurk API. Returns the raw API response data.

### `localize_datetime()`

* *Arguments:* `dt_obj`: The `datetime` object we want to localize into Pacific time
* Uses pytz to just put the time into Pacific timezone

### `notify_worker()`

* *Arguments:* `client`, `cur_worker_id`, `custom_msg`
* Uses MTurk's `notify_workers()` API function to send `custom_msg` as an
    email to worker `cur_worker_id`. Returns the raw API response.

### `parse_stage1_answer()`

* *Arguments:* (answer_xml
* Parses MTurk's answer XML format and converts the worker's answers to a
    standard Python dict

### `qual_exists()`

* *Arguments:* (client, qual_name):
* Returns True if a qual already exists with name `qual_name`, False otherwise

### `random_wage()`

* Draws an element, uniformly at random, from the global var `wage_dist` (described above)

### `update_current_qual()`

* *Arguments:* (new_qual_name, new_qual_id, new_qual_num, new_offer_amt):
* Updates the .txt file containing info on the current run (its qual name and id, last-used qual num, and last-used reward amount)

### `update_launched_worker()`

* *Arguments:* (cur_worker_id, notified_time):
* Updates the .csv containing launch info to have the `notified_time` for worker `cur_worker_id`. Returns the fpath of the newly-updated .csv

### `worker_id_from_title()`

* *Arguments:* (hit_title
* Helper function, takes the full title of a custom stage-2 HIT and extracts
    just the worker id for this HIT

### `write_log()`

* *Arguments:* `msg`
* Writes `msg` out to the log file specified by `log_fpath` (described above)
