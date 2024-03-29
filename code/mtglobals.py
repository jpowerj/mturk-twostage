# Python imports
import datetime
import os
import pathlib

# 3rd-party imports
import boto3
import dotenv
import joblib
import pandas as pd
import numpy as np
import pytz
import xmltodict
rng = np.random.default_rng()

# Global constants

# The fpath for the .env file containing e.g. AWS access + secret keys
dotenv_fpath = ".env"

# The timezone used to localize timestamps
local_tz = pytz.timezone('US/Pacific')

# The file where the most-recently-created qualification info is stored
qual_info_fpath = os.path.join("..", "results_2stage", "current_qual.txt")

# Date cutoff: any hits before this date won't get downloaded by download_all_hits()
default_start_cutoff = datetime.datetime(2021, 10, 30, 0, 0, 0, 0, pytz.UTC)

# fpath for the list of workers who submitted stage 1. Generated by 01_MonitorStage1
stage1_submit_list_fpath = os.path.join("..", "results_2stage", "stage1_submit_list.pkl")
# fpath for the .csv containing the *results* of the stage 1 HIT (as in, including
# their responses to the 3 demographic questions)
stage1_results_fpath = os.path.join("..", "results_2stage", "stage1_results.csv")
# fpath for the .csv where each row is a launched stage 2 HIT
stage2_launched_fpath = os.path.join("..", "results_2stage", "stage2_launched_workers.csv")
# fpath for the .pkl containing the list of workers who *submitted* their custom
# stage 2 HIT
stage2_submitted_fpath = os.path.join("..", "results_2stage", "stage2_submitted_workers.pkl")

# The filepath to the log written to when `write_log()` is called
log_fpath = './mtlog.txt'

# The `pytz` object representing the Pacific timezone, for datetime localization
pacific = pytz.timezone('US/Pacific')

# Global functions


def add_posted_worker(cur_worker_id, cur_offer_amt, cur_qual_name, cur_qual_id,
                      cur_qual_num, cur_hit_id, cur_hit_type_id, custom_url,
                      launched_time):
    """
    Once a worker's custom stage-2 HIT has been posted, add their info (and the
    HIT info) to the .csv at `stage2_launched_fpath` (the global constant above)
    
    Returns the fpath of the newly-updated .csv file
    """
    # And add to list of already-launched workers
    launched_fpath = stage2_launched_fpath
    df_cols = ['worker_id', 'offer_amt', 'qual_name', 'qual_id', 'qual_num',
               'hit_id', 'hit_type_id', 'url', 'launched_time', 'notified_time']
    if not os.path.isfile(launched_fpath):
        # Generate an empty df, to be filled below
        empty_df_data = {col: [] for col in df_cols}
        df = pd.DataFrame(empty_df_data)
        df.to_csv(launched_fpath, index=False)
    launch_df = pd.read_csv(launched_fpath)
    # The data we're serializing
    new_data = pd.DataFrame({
        'worker_id': [cur_worker_id],
        'offer_amt': [cur_offer_amt],
        'qual_name': [cur_qual_name],
        'qual_id': [cur_qual_id],
        'qual_num': [cur_qual_num],
        'hit_id': [cur_hit_id],
        'hit_type_id': [cur_hit_type_id],
        'url': [custom_url],
        'launched_time': [launched_time],
        # This one gets filled in by NotifyStage2
        'notified_time': [None],
    })
    updated_df = pd.concat([launch_df, new_data])
    updated_df.to_csv(launched_fpath, index=False)
    return launched_fpath

def check_launched(launched_df, worker_id):
    """
    Checks `launched_df` to see if the 2nd-stage hit has already been launched
    for this worker. If so, return the qual_name, qual_num and offer_amt they
    were assigned, otherwise return "",-1,-1
    """
    if launched_df is None:
        return "", -1, -1
    result_df = launched_df[launched_df['worker_id'] == worker_id].copy()
    if len(result_df) > 0:
        first_row = result_df.iloc[0]
        qual_name = first_row['qual_name']
        qual_num = int(first_row['qual_num'])
        offer_amt = first_row['offer_amt']
        return qual_name, qual_num, offer_amt
    return "", -1, -1


def draw_random_wage():
    """
    Draws an element, uniformly at random, from the global wage distribution
    """
    dotenv.load_dotenv(dotenv_fpath)
    wage_str = os.getenv("STAGE2_REWARDS")
    # Split on comma to get the list
    wage_dist = wage_str.split(",")
    return rng.choice(wage_dist)


def gen_custom_hit(xml_fpath, survey_url, cur_worker_id, cur_offer_amt,
                   cur_audio_id):
    """
    Construct custom stage-2 HIT for worker `cur_worker_id`, with offer amount
    `cur_offer_amt`.
    
    Roughly based on the example xml given in this tutorial:
    https://github.com/aws-samples/mturk-code-samples/blob/master/Python/my_question.xml
    """
    with open(xml_fpath, "r", encoding='utf-8') as f:
        stage2_question = f.read()
    # Fill in the custom data
    stage2_question = stage2_question.replace("!survey_url!", survey_url)
    stage2_question = stage2_question.replace("!worker_id!", cur_worker_id)
    stage2_question = stage2_question.replace("!offer_amt!", cur_offer_amt)
    stage2_question = stage2_question.replace("!audio_id!", cur_audio_id)
    return stage2_question


def gen_custom_msg(hit_type_id):
    custom_msg = ("Hello, you have qualified for a custom HIT based on your completion of the "
                  "initial workplace survey HIT. Please visit the following URL to access your "
                  "custom HIT (if the link does not work, please email us at columbiatextlab@gmail.com): "
                  f"https://worker.mturk.com/projects/{hit_type_id}/tasks\n\nIf "
                  "this link does not work, please try searching for \"Columbia TextLab\" on the "
                  "web UI, or by visiting this URL: "
                  "https://worker.mturk.com/projects?filters%5Bsearch_term%5D=textlab&page_size=20&page_number=1")
    return custom_msg


def gen_qual_restriction(cur_qual_id, cur_qual_num):
    """
    Generates the object (dict) specifying the restriction specific to this user's stage-2 HIT (that they
    have the current-run qual with id `cur_qual_id`, and the specific qual
    num specified by `cur_qual_num`. Returns list of requirements that can
    be directly passed to the API's post HIT function
    
    Roughly based on this example of using qualification to restrict responses
    to Workers who have had at least 80% of their assignments approved:
    http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
    """
    stage2_requirements = [
        # {
        #     'QualificationTypeId': '000000000000000000L0',
        #     'Comparator': 'GreaterThanOrEqualTo',
        #     'IntegerValues': [80],
        #     'RequiredToPreview': True,
        # },
        # {
        #     # WorkplaceSurveyCustom ID in *Sandbox*
        #     #'QualificationTypeId': '3Y0FER3934AFGRF24YM9Q00LF2OXKO',
        #     # WorkplaceSurveyCustom ID in *Dev*
        #     'QualificationTypeId': survey_qual_id,
        #     'Comparator': 'Exists',
        #     'ActionsGuarded': 'DiscoverPreviewAndAccept',
        # },
        {
            'QualificationTypeId': cur_qual_id,
            'Comparator': "In",
            'IntegerValues': [cur_qual_num],
            'ActionsGuarded': 'DiscoverPreviewAndAccept',
        }
    ]
    return stage2_requirements


def gen_timestamp():
    """
    Helper function, generates a (string) timestamp string with format YMD_hms, just so
    the timestamps are uniform across the pipeline.
    """
    timestamp = str(datetime.datetime.now()).split(".")[0].replace(" ","_").replace("-","").replace(":","")
    return timestamp


xml_template = """<HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
  <HTMLContent><![CDATA[
{html}
]]>
  </HTMLContent>
  <FrameHeight>{frame_height}</FrameHeight>
</HTMLQuestion>
"""


def gen_xml(html_fpath, frame_height=450):
    with open(html_fpath, 'r', encoding='utf-8') as infile:
        raw_html = infile.read()
    # Use the template to wrap the html
    xml_str = xml_template.format(html=raw_html, frame_height=frame_height)
    # And save
    xml_fpath = html_fpath.replace(".html", ".xml")
    with open(xml_fpath, 'w', encoding='utf-8') as outfile:
        outfile.write(xml_str)
    return xml_fpath


def get_current_qual():
    """
    Gets the info for the qual being used for the current run
    """
    if not os.path.isfile(qual_info_fpath):
        print(f"No qual info found at {qual_info_fpath}")
        return None
    with open(qual_info_fpath, 'r', encoding='utf-8') as f:
        qual_info = f.read()
    qual_elts = qual_info.strip().split(",")
    # First is qual name, second is qual id, third is qual_num of the last launched HIT,
    # fourth is last offer_amt
    qual_name = qual_elts[0]
    qual_id = qual_elts[1]
    last_qual_num = int(qual_elts[2])
    last_offer_amt = qual_elts[3]
    return {'qual_name': qual_name, 'qual_id': qual_id,
            'last_qual_num': last_qual_num, 'last_offer_amt': last_offer_amt}


def get_hit_for_worker(all_hits, worker_id, verbose=False):
    """
    Looks in the list `all_hits` and returns the entry representing the custom HIT created for the worker with id `worker_id`
    """
    vprint = print if verbose else lambda x: None
    # The HIT only has the worker_id in its title, so we have to extract
    # using mtglobals.worker_id_from_title()
    #vprint([h['Title'] for h in all_hits])
    results = [h for h in all_hits if worker_id_from_title(h['Title']) == worker_id]
    if len(results) == 0:
        raise Exception(f"No HIT found for worker {worker_id}")
    return results[0]


def localize_datetime(dt_obj):
    """
    Uses pytz to just put the time into the globally-defined timezone
    """
    return dt_obj.replace(tzinfo=local_tz)


def parse_stage1_answer(answer_xml):
    """
    Parses MTurk's answer XML format and converts the worker's answers to a
    standard Python dict
    """
    parse_result = xmltodict.parse(answer_xml)
    answer_data = parse_result['QuestionFormAnswers']
    answers = answer_data['Answer']
    #print(answers)
    answer_dict = {d['QuestionIdentifier']: d['FreeText'] for d in answers}
    # But make sure that empty responses just get the empty string
    for qid in ['age','onlinehrs','reason']:
        if qid not in answer_dict:
            answer_dict[qid] = ''
    return answer_dict


def update_current_qual(new_qual_name, new_qual_id, new_qual_num, new_offer_amt):
    info_str = f"{new_qual_name},{new_qual_id},{new_qual_num},{new_offer_amt}"
    if not os.path.isfile(qual_info_fpath):
        # Create the file
        fpath_elts = os.path.split(qual_info_fpath)
        path = fpath_elts[0]
        # Create the necessary dirs
        os.makedirs(path)
        # And touch the .txt file
        pathlib.Path(qual_info_fpath).touch()
    with open(qual_info_fpath, 'w', encoding='utf-8') as outfile:
        outfile.write(info_str)
    print(f"Current qual info in {qual_info_fpath} updated to be: {info_str}")


def update_launched_worker(cur_worker_id, notified_time):
    """
    Updates the .csv containing launch info to have the `notified_time` for
    worker `cur_worker_id`. Returns the fpath of the newly-updated .csv
    """
    # And add to list of already-launched workers
    launched_df = pd.read_csv(stage2_launched_fpath)
    # Find the row for this worker and set the notified_time
    launched_df.loc[launched_df['worker_id'] == cur_worker_id, 'notified_time'] = notified_time
    launched_df.to_csv(stage2_launched_fpath, index=False)
    return stage2_launched_fpath


def worker_id_from_title(hit_title):
    """
    Helper function, takes the full title of a custom stage-2 HIT and extracts
    just the worker id for this HIT
    """
    title_elts = hit_title.split(" ")
    worker_id = title_elts[-1]
    return worker_id


def write_log(msg):
    """
    Writes `msg` out to the log file specified by `log_fpath` (described above)
    """
    stamp = datetime.datetime.now().isoformat()
    with open(log_fpath, 'a', encoding='utf-8') as outfile:
        outfile.write(f"[{stamp}] {msg}\n")

