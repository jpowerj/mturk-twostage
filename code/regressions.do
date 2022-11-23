clear
set more off
pause on

local fname = "accepted_df_20221017_181143.dta"
local fpath = "../results_2stage/`fname'"

use "`fpath'"

gen jump = (lwage >= 0)

reg accepted lwage jump, robust

reg accepted lwage jump if sophisticated ==1, robust
