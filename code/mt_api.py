# This program basically circumvents all the shitty "official" mturk APIs,
# which are all terrible, by computing the authentication codes "in house" and
# then just sending the requests over HTTPS directly.

import configparser
# For generating the timestamp
from datetime import datetime
# For generating the signature
import hashlib
import hmac
import os
import base64
import urllib
# For sending the query
import requests
# For parsing the results
import xml.etree.ElementTree as ET

service = "AWSMechanicalTurkRequester"
request_template = "https://mechanicalturk.amazonaws.com/?Service={service}&AWSAccessKeyId={access_key}&Version=2014-08-15&Signature={request_sig}&Timestamp={cur_timestamp}"

# These are loaded from a config file via the load_keys() function
mturk_access_key = None
secret_access_key = None

def assign_qualification(qual_id, worker_id, score):
    """
    Assigns the qualification with id `qual_id' to the worker with id `worker_id',
    with the qualification's "score" param set to `score'.
    """
    check_keys()
    # Construct the param string
    operation_name = "AssignQualification"
    params_dict = {}
    params_dict['Operation'] = operation_name
    params_dict['QualificationTypeId'] = qual_id
    params_dict['WorkerId'] = worker_id
    params_dict['IntegerValue'] = str(score)

    # Issue the request
    result = issue_request(params_dict)
    #print(result)

    # Parse the XML
    xml_root = ET.fromstring(result)
    # (Check if it's a valid assignment, or if the qualification has already
    # been assigned, or if there's some other error)
    qual_result = xml_root.findall("AssignQualificationResult")[0]
    request_node = qual_result.findall("Request")[0]
    is_valid = request_node.findall("IsValid")[0].text
    if is_valid == "True":
        return ("Success: Assigned qualification " + qual_id + 
                " to worker " + worker_id)
    else:
        return_str = ("Failure: Could not assign qualification " + qual_id +
                      " to worker " + worker_id + ". Error message: ")
        errors_node = request_node.findall("Errors")[0]
        error_node = errors_node.findall("Error")[0]
        error_message = error_node.findall("Message")[0].text
        return return_str + error_message

def check_keys():
    global mturk_access_key, secret_access_key
    if (mturk_access_key is None) or (secret_access_key is None):
        raise AttributeError("No AMT key data available: load_keys() must be " +
          "called before using any other functions.")

def compute_signature(operation, timestamp):
    """ 
    Long story short, the Signature field sent to Amazon's servers is the Service,
    Operation, and Timestamp params concatenated together, hashed, and then
    converted into base64
    """
    global secret_access_key, service
    check_keys()
    #print("Computing signature for service=[" + service + "], operation=[" + operation + "], timestamp=[" + timestamp + "]") 
    signature_data = service + operation + timestamp
    signature_key = secret_access_key.encode("utf-8")
    
    hmac_object = hmac.new(key=signature_key,msg=signature_data.encode("utf-8"),
                           digestmod=hashlib.sha1)
    signature = hmac_object.digest()
    # Need to encode the signature as base64
    sig_base64 = base64.b64encode(signature)
    sig_str = sig_base64.decode("utf-8")
    sig_str = urllib.parse.quote_plus(sig_str)
    return sig_str

def format_usd(dollar_amt):
    """
    Takes in a float and returns a currency string in the format accepted by MTurk
    """
    if isinstance(dollar_amt,str):
        # Amount is already a string, just return
        return dollar_amt
    return "{:4.2f}".format(dollar_amt)

def get_balance():
    """
    Calls the GetAccountBalance service and parses the resulting XML
    """
    check_keys()
    operation_name = "GetAccountBalance"
    params_dict = {}
    params_dict['Operation'] = operation_name
    result = issue_request(params_dict)
    #print(result)
    # Parse the balance amount out of the XML
    xml_root = ET.fromstring(result)
    balance_result_node = xml_root[1][1][0]
    return format_usd(float(balance_result_node.text))

def get_hit(hit_id):
    """
    Returns the information AMT provides for the HIT with id `hit_id`
    """
    check_keys()
    # Construct the param string
    operation_name = "GetHIT"
    param_dict = {}
    param_dict["Operation"] = operation_name
    param_dict["HITId"] = hit_id
    # Issue the request
    result = issue_request(param_dict)
    # TODO: parse the xml :/
    #xml_root = ET.fromstring(result)
    return result

def get_timestamp():
    """
    Constructs an ISO 8601-compliant timestamp for the current time
    """
    cur_time = datetime.utcnow()
    timestamp = "{:%Y-%m-%dT%H:%M:%SZ}".format(cur_time)
    return timestamp

def grant_bonus(worker_id, assignment_id, amount, reason):
    """
    Awards a bonus with amount `amount` (a float value) to the worker with id
    `worker_id`, for their work on the assignment with id `assignment_id`, and
    with a string explaining the award, `reason'. Note that this function does
    NOT raise any Exceptions if something goes wrong, it just returns False. I
    wrote it this way so that if one bonus fails it doesn't derail an entire
    loop, or whatever external script called the function.
    """
    check_keys()
    # Construct the param string
    operation_name = "GrantBonus"
    param_dict = {}
    param_dict["Operation"] = operation_name
    param_dict["WorkerId"] = worker_id
    param_dict["AssignmentId"] = assignment_id
    # Parse the amount into a string
    amount_str = format_usd(amount)
    param_dict["Reward.1.Amount"] = amount_str
    param_dict["Reward.1.CurrencyCode"] = "USD"
    # URL encode the reason
    reason_urlized = urllib.parse.quote_plus(reason)
    param_dict["Reason"] = reason_urlized
  
    # Issue the request
    result = issue_request(param_dict)
    
    # Parse the XML
    xmlroot = ET.fromstring(result)
    result_node = xmlroot.findall("GrantBonusResult")[0]
    request_node = result_node.findall("Request")[0]
    is_valid = request_node.findall("IsValid")[0].text
    if is_valid == "True":
        success_str = ("Success: paid " + amount_str +
                       " to worker " + str(worker_id))
        return success_str
    else:
        failure_str = ("Failure: could not pay " + amount_str +
                       " to worker " + str(worker_id))
        return failure_str

def issue_request(params):
    """
    Helper function, used by all the others to send the request once all the
    user-modifiable params have been formatted correctly
    """
    global service, mturk_access_key, request_template
    check_keys()
    # Get operation
    operation = params['Operation']
    # Compute timestamp
    timestamp = get_timestamp()
    # Compute signature
    sig = compute_signature(operation, timestamp)
    
    # Construct the params string
    params_str = ""
    for key in params:
        params_str = params_str + "&" + key + "=" + params[key]
    
    # Send the http request
    request_url = request_template.format(service=service,
                                          access_key=mturk_access_key,
                                          request_sig=sig,
                                          cur_timestamp=timestamp)
    request_url = request_url + params_str
    #print("Issuing request:")
    #print(request_url)
  
    request = requests.get(request_url)
    return request.content

def load_keys(config_filepath):
    """
    Loads mturk_access_key and secret_access_key from a config file. This
    function must be called before any others will work.
    """
    global mturk_access_key, secret_access_key
    if not os.path.isfile(config_filepath):
        raise AttributeError("No config file found. " +
            str(config_filepath) +
            " is not a valid access_keys configuration file.")
    config = configparser.ConfigParser()
    config.read(config_filepath)
    if "AMT_Keys" not in config:
        message = ("Configuration file has no [AMT_Keys] section. " +
          "The first line of the config file needs to be \"[AMT_Keys]\".")
        raise AttributeError(message)
    key_data = config["AMT_Keys"]
    if "ACCESS_KEY" not in key_data:
        message = ("Configuration file has no ACCESS_KEY value. " +
          "The format is \"ACCESS_KEY=[your access key here]\".")
        raise AttributeError(message)
    if "SECRET_KEY" not in key_data:
        message = ("Configuration file has no SECRET_KEY value. " +
          "The format is \"SECRET_KEY=[your secret key here]\".")
        raise AttributeError(message)
    # We made it
    mturk_access_key = key_data["ACCESS_KEY"]
    secret_access_key = key_data["SECRET_KEY"]
    
def revoke_qualification(qual_id, worker_id):
    """
    Removes the qualification with id `qual_id` from the worker with id `worker_id`.
    """
    check_keys()
    # Construct the param string
    operation_name = "RevokeQualification"
    param_dict = {}
    param_dict["Operation"] = operation_name
    param_dict["SubjectId"] = worker_id
    param_dict["QualificationTypeId"] = qual_id
    
    # Issue the request
    result = issue_request(param_dict)
    
    # Parse the XML
    xmlroot = ET.fromstring(result)
    revoke_result_node = xmlroot.findall("RevokeQualificationResult")[0]
    request_node = revoke_result_node.findall("Request")[0]
    is_valid = request_node.findall("IsValid")[0].text
    if is_valid == "True":
        return ("Success: Revoked qualification " + qual_id +
                " from worker " + worker_id)
    else:
        return ("Failure: Could not revoke qualification " + qual_id +
                " from worker " + worker_id)
  
if __name__ == "__main__":
    """ 
    Uncomment this part if you want to test the API on your worker account before
    using it "in the wild".
    """
    ## Test the API by issuing a GetAccountBalance request
    #print("-----GetBalance test-----")
    #print(get_balance())
    ## And by assigning a qualification to myself
    #recipe_qual_id = "33JPJJ9N305Q0XXKPYY8R4F3AQKLXM"
    #test_worker_id = "<YOUR WORKER ID HERE>"
    #score = 100
    ## First, *remove* the qualification from myself
    #print("-----RevokeQualification test-----")
    #print(revoke_qualification(recipe_qual_id, test_worker_id))
    #print("-----AssignQualiciation test-----")
    #print(assign_qualification(recipe_qual_id, test_worker_id, score))
    ## Grant a 1-cent bonus to test_worker
    #print("-----GrantBonus test-----")
    #test_assignment_id = "33C7UALJVMZXVL3UN5SH3ZZG7L9817"
    #print(grant_bonus(test_worker_id, test_assignment_id, 0.01, "Testing"))
    
    ## Testing the GetHIT operation
    #test_hit = "3YZ7A3YHR6UBF3LSCOVWZWHDB1Y5SG"
    #get_hit(test_hit)

  