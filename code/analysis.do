clear
set more off
pause on

local result_dir = "../results"
*use "`result_dir'/restdb_combined.dta"

insheet using "`result_dir'/results_clean.csv", clear

destring offer_amt , replace ignore("$")
gen last = regexm(creationtime, "Aug 28")
gen last2 = regexm(creationtime, "Aug 18")|regexm(creationtime, "Aug 17")
gen all =1
gen last3 = last2|last
gen accept = accepted_offer =="True" if accepted_offer !=""
gen accept_any = accepted_offer =="True"

*keep if last==1
*keep if last==1|last2==1

gen jump = offer_amt>=1.00
gen logwage =log(offer_amt)
gen returned = accepted_offer  ==""


foreach s of varlist all last last2 last3{
	eststo clear
	eststo:reg accept logwage if `s'==1, robust
	eststo:reg accept logwage if `s'==1, a(creationtime) robust
	eststo:reg accept_any logwage if `s'==1, robust
	eststo:reg accept_any logwage jump if `s'==1, robust
	eststo:reg accept_any logwage jump if `s'==1, a(creationtime) robust
	eststo:reg returned logwage if `s'==1, robust
	eststo:reg returned logwage jump if `s'==1, robust
	esttab, drop(_cons)
}
stop

lincom _b[jump] - .01*_b[logwage]

/*test if jump > implied increase of 1 penny = .01/1.00 = 1% * beta 


/*daccept/d1cent/daccept/(dw/w) *.01


reg accept offer_amt, robust
*reg accept logwage if offer_amt<1.5, robust


stop
gen maxdid = 0
forvalues i=1/30{
	gen did`i' = response`i'=="0"
	replace maxdid =`i' if response`i'!="0"

}
