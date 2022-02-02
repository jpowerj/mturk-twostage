clear
set more off
pause on

local result_dir = "../results"

*** Combine qualtrics data
local qualtrics1 = "Job+Quality+NonWM+3.0_August+1,+2021_14.25.xlsx"
local qualtrics2 = "Job+Quality+NonWM+8.0_August+19,+2021_15.22.xlsx"
local num_qualtrics = 2
* Convert to dta
forvalues cur_index = 1/`num_qualtrics' {
    local cur_fname = "`qualtrics`cur_index''"
	disp "`cur_fname'"
	import excel "`result_dir'/`cur_fname'", first
	* Drop first observation (it contains the variable labels from Qualtrics)
    drop in 1
	* Drop extraneous vars
	drop *_tense
	drop name_*
	drop cur_*
	drop val_*
	gen source = "`cur_fname'"
	local dta_fname = subinstr("`cur_fname'","xlsx","dta",.)
	save "`result_dir'/tmp/`dta_fname'", replace
	local qualtrics_dta`cur_index' = "`dta_fname'"
	clear
}
* Load the first
use "`result_dir'/tmp/`qualtrics_dta1'"
* Append the remainder
forvalues cur_index = 2/`num_qualtrics' {
    local cur_dta_fname = "`result_dir'/tmp/`qualtrics_dta`cur_index''"
    append using "`cur_dta_fname'"
}
* And save combined file
save "`result_dir'/qualtrics_combined.dta", replace
clear

*** MTurk data
local mturk1 = "pilot2_Batch_4517898_batch_results.csv"
local mturk2 = "pilot3_Batch_4534737_batch_results.csv"
local num_mturk = 2
* Convert to dta
forvalues cur_index = 1/`num_mturk' {
    local cur_fname = "`mturk`cur_index''"
	disp "`cur_fname'"
	import delimited "`result_dir'/`cur_fname'"
	gen source = "`cur_fname'"
	* Clean the survey code (convert to string)
	rename answersurveycode mturk_code
	tostring mturk_code, replace
	local dta_fname = subinstr("`cur_fname'","csv","dta",.)
	save "`result_dir'/tmp/`dta_fname'", replace
	local mturk_dta`cur_index' = "`dta_fname'"
	clear
}
* Load the first
use "`result_dir'/tmp/`mturk_dta1'"
* And append the remainder
forvalues cur_index = 2/`num_mturk' {
    local cur_dta_fname = "`mturk_dta`cur_index''"
	append using "`result_dir'/tmp/`cur_dta_fname'"
}
* Save combined file
save "`result_dir'/mturk_combined.dta", replace
clear

* RestDB files
local restdb1 = "restdb_2021-08-19_1403.csv"
local num_restdb = 1
* Convert to dta
forvalues cur_index = 1/`num_restdb' {
    local cur_fname = "`restdb`cur_index''"
	disp "`cur_fname'"
	import delimited "`result_dir'/`cur_fname'"
	gen source = "`cur_fname'"
	local dta_fname = subinstr("`cur_fname'","csv","dta",.)
	save "`result_dir'/tmp/`dta_fname'", replace
	local restdb_dta`cur_index' = "`dta_fname'"
	clear
}
* Load the first
use "`result_dir'/tmp/`restdb_dta1'"
* Append the remainder
forvalues cur_index = 2/`num_restdb' {
    local cur_dta_fname = "`restdb_dta`cur_index''"
	append using "`result_dir'/tmp/`cur_dta_fname'"
}
* Save combined file
save "`result_dir'/restdb_combined.dta", replace
clear

* Clean the combined mturk data
use "`result_dir'/mturk_combined.dta"
duplicates drop mturk_code, force
rename answeracceptoffer accepted_offer
replace accepted_offer = "yes" if accepted_offer == ""
*gen accepted_offer = 1
*replace accepted_offer = 0 if mturk_code == "{}"
save "`result_dir'/mturk_clean.dta", replace
clear

* Process restdb file (get wage amount from id num)
use "`result_dir'/restdb_combined.dta"
drop if id == "[Functions]"
destring id, replace
gen id_mod = mod(id, 11)
gen offer = ""
replace offer = "$0.50" if id_mod == 0
replace offer = "$0.90" if id_mod == 1
replace offer = "$0.95" if id_mod == 2
replace offer = "$0.98" if id_mod == 3
replace offer = "$0.99" if id_mod == 4
replace offer = "$1.00" if id_mod == 5
replace offer = "$1.01" if id_mod == 6
replace offer = "$1.02" if id_mod == 7
replace offer = "$1.05" if id_mod == 8
replace offer = "$1.10" if id_mod == 9
replace offer = "$1.50" if id_mod == 10
rename mtid mt_id
duplicates drop mt_id, force
save "`result_dir'/restdb_clean.dta", replace
clear

* Load Qualtrics results file
use "`result_dir'/qualtrics_combined.dta"

* Now merge with MTurk data, on the randomly-generated survey completion code
merge 1:1 mturk_code using "`result_dir'/mturk_clean.dta"
keep if accepted_offer != ""

* Here _merge == 1 means they started the survey but didn't complete it, so
* never submitted the HIT. _merge == 3 means they finished the survey (though
* this may mean they accepted the offer, rejected the offer, or were never given
* tasks in the first place bc they indicated that they've never been employed)
drop _merge

duplicates drop mt_id, force
merge 1:1 mt_id using "`result_dir'/restdb_clean.dta"
keep if accepted_offer != ""

* For old Qualtrics files (pre-Version 8.0)
* Q10 = first task, and so on. This is fixed in the newest version of the survey,
* so that the responses come pre-set as response1, response2, ...
* So, this if statement makes sure that it only does this weird renaming if
* we have the old version of the variable names
*local rnum = 1
*foreach cur_var of varlist Q10 Q155 AV Q161 Q164 Q167 Q170 BA Q179 Q182 Q185 {
*    capture confirm variable `cur_var', exact
*    if !_rc {
*        *display "`cur_var' exists"
*		rename `cur_var' response`rnum'
*		local rnum = `rnum' + 1
*   }
*}

save "`result_dir'/results_clean.dta", replace
