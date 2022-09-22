import datetime
import os

import boto3
import dotenv
import joblib
import pandas as pd
import numpy as np

import mtglobals


class MTClient:
    def __init__(self, dotenv_fpath=mtglobals.dotenv_fpath):
        """
        By default, HITs are created in the free-to-use Sandbox. Change the top line
        of code to set it to create the HITs in the real production version of MTurk.

        `dotenv_fpath` defaults to ".env", but you can pass a custom fpath if
        running on Colab, for example
        """
        dotenv.load_dotenv(dotenv_fpath)
        self.stage1_reward = os.getenv("STAGE1_REWARD")
        environments = {
            "live": {
                "endpoint_url": "https://mturk-requester.us-east-1.amazonaws.com",
                "preview_url": "https://www.mturk.com/mturk/preview",
                "manage_url": "https://requester.mturk.com/mturk/manageHITs",
                "reward": self.stage1_reward
            },
            "sandbox": {
                "endpoint_url": "https://mturk-requester-sandbox.us-east-1.amazonaws.com",
                "preview_url": "https://workersandbox.mturk.com/mturk/preview",
                "manage_url": "https://requestersandbox.mturk.com/mturk/manageHITs",
                "reward": self.stage1_reward
            },
        }
        self.use_sandbox = os.getenv("SANDBOX")
        self.mturk_environment = environments["live"] if self.use_sandbox else environments["sandbox"]
        # Load access+secret keys
        access_key = os.getenv("AWS_ACCESS_KEY")
        secret_key = os.getenv("AWS_SECRET_KEY")
        self.boto_session = boto3.Session()
        self.boto_client = self.boto_session.client(
            service_name='mturk',
            region_name='us-east-1',
            # dev endpoint
            #endpoint_url="https://mturk-requester.us-east-1.amazonaws.com",
            # sandbox endpoint
            #endpoint_url="https://mturk-requester-sandbox.us-east-1.amazonaws.com",
            endpoint_url=self.mturk_environment['endpoint_url'],
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        # And load params from .env
        self.participation_qual_id = os.getenv("PARTICIPATION_QUAL_ID")
        # Test that you can connect to the API by checking your account balance
        user_balance = self.get_account_balance()
        # In Sandbox this always returns $10,000. In live, it will be your acutal balance.
        print("Your account balance is {}".format(user_balance['AvailableBalance']))

    def assign_qual_safe(self, worker_id, qual_id, qual_num=0, notify=False):
        """
        Assigns the qualification "safely", meaning that it just returns without
        doing anything if the worker already has the qual
        """
        try:
            response = self.boto_client.get_qualification_score(
                QualificationTypeId=qual_id,
                WorkerId=worker_id
            )
            # If we're here, that means the worker already has the qual. So we don't
            # do anything
            return f"Worker {worker_id} already has qual {qual_id}"
        except self.boto_client.exceptions.RequestError as e:
            # If we're here, that means the worker does *not* have the qual.
            # So assign it
            #print(e)
            # Assign this worker the participant qual
            response = self.boto_client.associate_qualification_with_worker(
                QualificationTypeId=qual_id,
                WorkerId=worker_id,
                IntegerValue=qual_num,
                SendNotification=notify
            )
            return f"Worker {worker_id} successfully given qual {qual_id}"

    def assign_stage2_quals(self, cur_worker_id, cur_qual_name, cur_qual_id,
                            cur_qual_num, cur_offer_amt):
        """
        Assigns the stage-2-specific quals. The first is the custom qual for this
        run, with the worker's specifical qual num. The second is the *participation*
        qual, given to every participant across all runs (to ensure nobody does it
        twice, across different runs)

        Returns the raw API response to the `associate_qualification_with_worker()`
        call (and thus ignores the response to the participation qual assignment! So
        be careful if something goes wrong with the participation quals -- you can
        change this to return that API response instead, or both responses in a tuple)
        """
        # Now assign the custom qualification
        print(f"Associating num {cur_qual_num} with worker {cur_worker_id}")
        response = self.boto_client.associate_qualification_with_worker(
            # sandbox id
            #QualificationTypeId='3Y0FER3934AFGRF24YM9Q00LF2OXKO',
            # production id, no suffix
            #QualificationTypeId='3QTU8Z4SHN84U5KCFOM3OI2TK3WGK7',
            QualificationTypeId=cur_qual_id,
            WorkerId=cur_worker_id,
            IntegerValue=cur_qual_num,
            SendNotification=True
        )
        # And update the info in current_qual.txt
        mtglobals.update_current_qual(cur_qual_name, cur_qual_id, cur_qual_num, cur_offer_amt)
        # And finally the participation qual (that everybody gets, regardless of which
        # custom qual)
        response_participation = self.boto_client.associate_qualification_with_worker(
            # (this is the id for the participation qual)
            QualificationTypeId=self.participation_qual_id,
            WorkerId=cur_worker_id,
            IntegerValue=0,
            SendNotification=False
        )
        return response

    def create_new_qual(self, new_qual_name,
                        new_qual_desc='Participation in the Columbia TextLab workplace survey',
                        new_qual_keywords='workplace,survey,custom'):
        """
        Create a qual with name `new_qual_name`, and return a
        (new qual name, new qual id) tuple
        """
        response = self.boto_client.create_qualification_type(
            Name=new_qual_name,
            Description=new_qual_desc,
            Keywords=new_qual_keywords,
            QualificationTypeStatus='Active'
        )
        # Get the new qual info (as opposed to the request metadata)
        qual_info = response['QualificationType']
        # Extract the info we need
        qual_name = qual_info['Name']
        qual_id = qual_info['QualificationTypeId']
        # qual_creation = qual_info['CreationTime']
        return {'qual_name': qual_name, 'qual_id': qual_id}

    def create_hit(self, num_hits, reward, title, keywords, description,
                   question, requirements):
        return self.boto_client.create_hit(
            MaxAssignments=mtglobals.num_hits,
            LifetimeInSeconds=86400, # 24 hours
            AssignmentDurationInSeconds=3600, # 1 hour
            Reward=reward,
            Title=title,
            Description=description,
            Keywords=keywords,
            Question=question,
            QualificationRequirements=requirements,
        )

    def download_all_hits(self, start_cutoff=mtglobals.default_start_cutoff,
                          end_cutoff=None, save_to_file=True):
        """
        Sets end_cutoff to be (localized) datetime.datetime.now() if None
        """
        if end_cutoff is None:
            end_cutoff = mtglobals.localize_datetime(datetime.datetime.now())
        download_fpath = "../results_2stage/all_hit_data.pkl"
        print(f"Downloading list of hits from {start_cutoff} to {end_cutoff}")
        all_hit_data = []
        all_scraped = False
        cur_next_token = None
        while not all_scraped:
            # This returns 'NextToken', 'NumResults', and 'HITs'
            if cur_next_token is None:
                response = self.boto_client.list_hits(
                    # NextToken='string',
                    MaxResults=100
                )
            else:
                response = self.boto_client.list_hits(
                    NextToken=cur_next_token,
                    MaxResults=100
                )
            if 'NextToken' in response:
                cur_next_token = response['NextToken']
                print(cur_next_token)
            else:
                # No next token, so we're at the final page
                all_scraped = True
            # We can stop if creation time is before August
            all_hits = response['HITs']
            if len(all_hits) > 0:
                # Loop through them, stopping if we hit one with creationtime outside
                # the cutoff
                for cur_hit in all_hits:
                    creation = cur_hit['CreationTime']
                    try:
                        creation_before_cutoff = creation < start_cutoff
                    except TypeError as e:
                        # Need to localize the cutoff
                        start_cutoff = mtglobals.localize_datetime(start_cutoff)
                    if creation < start_cutoff:
                        print(f"Creation {creation} before start_cutoff")
                        # This means we've gotten them all, since they download
                        # in reverse chronological order
                        all_scraped = True
                        break
                    try:
                        creation_after_cutoff = creation > end_cutoff
                    except TypeError as e:
                        end_cutoff = mtglobals.localize_datetime(end_cutoff)
                    if creation > end_cutoff:
                        #print(f"Creation {creation} after end_cutoff")
                        # This means we just skip this one, but have to
                        # keep going
                        continue
                    else:
                        all_hit_data.append(cur_hit)
            else:
                all_scraped = True
        if save_to_file:
            print(f"Saving downloaded HIT data to {download_fpath}")
            joblib.dump(all_hit_data, download_fpath)
        return all_hit_data

    def get_account_balance(self):
        return self.boto_client.get_account_balance()

    def get_all_quals(self):
        """
        Syntax for boto:

        ```
        response = client.list_qualification_types(
            Query='string',
            MustBeRequestable=True|False,
            MustBeOwnedByCaller=True|False,
            NextToken='string',
            MaxResults=123
        )
        ```

        See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html#MTurk.Client.list_qualification_types
        """
        qual_response = self.boto_client.list_qualification_types(
            MustBeRequestable=False,
            MustBeOwnedByCaller=True,
            MaxResults=100
        )
        # The actual list is in 'QualificationTypes'
        qual_list = qual_response['QualificationTypes']
        return qual_list

    def get_hit_submissions(self, hit_id):
        """
        Returns a list where each element is MTurk's info about a particular submission of the HIT with id `hit_id`
        """
        all_submissions = []
        all_scraped = False
        # Start with a single call
        response = self.boto_client.list_assignments_for_hit(HITId=hit_id)
        all_submissions.extend(response['Assignments'])
        if 'NextToken' in response:
            cur_next_token = response['NextToken']
            # cur_num_results = response['NumResults']
            while not all_scraped:
                response = self.boto_client.list_assignments_for_hit(HITId=hit_id, NextToken=cur_next_token)
                cur_submissions = response['Assignments']
                all_submissions.extend(cur_submissions)
                if 'NextToken' in response:
                    cur_next_token = response['NextToken']
                else:
                    all_scraped = True
        return all_submissions

    def get_qual_id(self, qual_name):
        """
        Gets the MTurk-assigned id for the qualification type with name `qual_name`
        """
        all_quals = self.get_all_quals()
        matching_quals = [info for info in all_quals if info['Name'] == qual_name]
        if len(matching_quals) == 0:
            raise Exception("No matching quals found!")
        else:
            qual_info = matching_quals[0]
        qual_id = qual_info['QualificationTypeId']
        return qual_id

    def get_stage1_submissions(self, hit_id):
        submission_list = []
        stage1_hit_response = self.boto_client.get_hit(HITId=hit_id)
        stage1_hit = stage1_hit_response['HIT']
        info_vars = ['HITId','HITTypeId','HITGroupId','HITLayoutId','Title','Description',
                     'Reward','QualificationRequirements','NumberOfAssignmentsCompleted','MaxAssignments']
        # Uncomment for info about the stage 1 HIT
        #for cur_var in info_vars:
        #    print(cur_var)
        #    if cur_var in stage1_hit:
        #        print(stage1_hit[cur_var])
        print(f"=====[ Launched Stage 1 HIT: ]=====")
        print(f"HIT launched {stage1_hit['CreationTime']}")
        print(f"Status: {stage1_hit['HITStatus']}")
        print(f"MaxAssignments: {stage1_hit['MaxAssignments']}")
        # Get assignments for this HIT
        assignments = self.get_hit_submissions(stage1_hit['HITId'])
        print(f"Num submissions: {len(assignments)}")
        #print("=====[ Assignment Data: ]=====")
        #print(assignments)

        # Approve all remaining Stage1 submissions
        print("=====[ Approving any remaining assignments ]=====")
        for anum, cur_assignment in enumerate(assignments):
            print(f"Assignment #{anum}")
            worker_id = cur_assignment['WorkerId']
            assignment_id = cur_assignment['AssignmentId']
            # Check if not approved yet
            status = cur_assignment['AssignmentStatus']
            if status != 'Approved':
                print(f"Approving {assignment_id}, for worker {worker_id}")
                response = self.boto_client.approve_assignment(
                    AssignmentId=assignment_id,
                    OverrideRejection=True
                )
                print(response)
            # Now get their response
            worker_answer = mtglobals.parse_stage1_answer(cur_assignment['Answer'])
            submission_list.append({'worker_id': worker_id, 'answer': worker_answer})
        # And save the new worker list to a .pkl (for easy loading in next step)
        joblib.dump(submission_list, mtglobals.stage1_submit_list_fpath)
        # And the full data, with responses, to a .csv
        ids = [d['worker_id'] for d in submission_list]
        ages = [d['answer']['age'] for d in submission_list]
        onlinehrs = [d['answer']['onlinehrs'] for d in submission_list]
        reasons = [d['answer']['reason'] for d in submission_list]
        stage1_df = pd.DataFrame({
            'worker_id': ids,
            'age': ages,
            'onlinehrs': onlinehrs,
            'reason': reasons}
        )
        csv_fpath = mtglobals.stage1_results_fpath
        stage1_df.to_csv(csv_fpath, index=False)
        print(f"Worker list saved to {mtglobals.stage1_submit_list_fpath}")
        print(f"csv saved to {csv_fpath}.")

    def get_workers_with_qual(self, qual_name):
        """
        Returns (after getting the id for the given qual name via `get_qual_id()`)
        a list of all worker_ids who have been granted the qualification with name
        `qual_name`
        """
        # First get the id for this qual
        qual_id = self.get_qual_id(qual_name)
        all_quals = []
        all_worker_ids = []
        cur_next_token = None
        response = self.boto_client.list_workers_with_qualification_type(
            QualificationTypeId=qual_id,
            Status='Granted',
            MaxResults=100,
        )
        cur_quals = response['Qualifications']
        cur_worker_ids = [q['WorkerId'] for q in cur_quals]
        all_worker_ids.extend(cur_worker_ids)
        all_quals.extend(cur_quals)
        all_quals.extend(response['Qualifications'])
        while 'NextToken' in response:
            cur_next_token = response['NextToken']
            response = self.boto_client.list_workers_with_qualification_type(
                QualificationTypeId=qual_id,
                Status='Granted',
                MaxResults=100,
                NextToken=cur_next_token
            )
            cur_quals = response['Qualifications']
            cur_worker_ids = [q['WorkerId'] for q in cur_quals]
            all_worker_ids.extend(cur_worker_ids)
            all_quals.extend(cur_quals)
        return all_worker_ids

    def launch_custom_hit(self, cur_worker_id, cur_offer_amt, cur_hit_title,
                          cur_hit_description, cur_hit_keywords, stage2_question,
                          stage2_requirements):
        """
        Launch the custom stage-2 HIT via MTurk API. Returns the raw API response data.
        """
        response = self.boto_client.create_hit(
            # 1 assignment bc single custom stage 2 hit
            MaxAssignments=1,
            LifetimeInSeconds=86400, # 24 hours
            AssignmentDurationInSeconds=3600, # 1 hour
            Reward=cur_offer_amt,
            Title=cur_hit_title,
            Description=cur_hit_description,
            Keywords=cur_hit_keywords,
            Question=stage2_question,
            QualificationRequirements=stage2_requirements,
        )
        return response

    def notify_worker(self, cur_worker_id, custom_msg):
        """
        Uses MTurk's `notify_workers()` API function to send `custom_msg` as an
        email to worker `cur_worker_id`. Returns the raw API response.
        """
        response = self.boto_client.notify_workers(
            Subject='Custom Workplace Survey 2nd-Stage HIT',
            MessageText=custom_msg,
            WorkerIds=[
                cur_worker_id
            ]
        )
        return response

    def qual_exists(self, qual_name):
        """
        Returns True if a qual already exists with name `qual_name`, False otherwise
        """
        all_quals = self.get_all_quals()
        matching_quals = [info for info in all_quals if info['Name'] == qual_name]
        if len(matching_quals) == 0:
            return False
        return True
