Qualtrics.SurveyEngine.addOnload(function()
{
    console.log("embedded data setting");
    /*Place your JavaScript here to run when the page loads*/
    // Loop over table rows, highlighting them if the values differ
    console.log("table js");
    var table = document.getElementById("offtable");
    var trows = table.getElementsByTagName("tr");
    //console.dir(trows);
    for (var i = 0; i < trows.length; i++) {
        var cur_row = trows[i];
        if (cur_row.id != "tableheader") {
            // Now see if its a mobile or non-mobile formatted row
            if (cur_row.classList[0] == "compare-row") {
                // This is the only type of row we care about -- the other
                // type (without the compare-row class) is just the potential
                // expanded header if they have a mobile device.
                // (For these rows, the first child is the
                // var name, and the next 2 are the actual values)
                var cur_col_text = cur_row.children[1].textContent;
                var off_col_text = cur_row.children[2].textContent;
                if (cur_col_text != off_col_text) {
                    // The values are different, so highlight the row
                    cur_row.style.backgroundColor = "#FFFF00";
                } // End highlight row
            } // End check if "compare-row" in classes
        } // End check if id is not "tableheader"
    } // End loop over table rows
});

Qualtrics.SurveyEngine.addOnReady(function()
{
    /*Place your JavaScript here to run when the page is fully displayed*/
    jQuery("td:contains('jobtitle')" ).text( "Job Title" );
    jQuery("td:contains('wage')" ).text( "Hourly Wage (USD)" );
    jQuery("td:contains('hrs')" ).text( "Hours Per Week" );
    jQuery("td:contains('controlhrs')" ).text( "Control Over Hours?" );
    jQuery("td:contains('paidsick')" ).text( "Paid Sick Leave?" );
    jQuery("td:contains('friends')" ).text( "Work With Friends?" );
    jQuery("td:contains('commute')" ).text( "Daily Commute Time" );
    jQuery("td:contains('physical')" ).text( "Intense Physical Activity?" );
    jQuery("td:contains('skills')" ).text( "Learn Transferable Skills?" );
    jQuery("td:contains('express')" ).text( "Opportunities for Expression?" );
    jQuery("td:contains('coworkers')" ).text( "Reliable Coworkers?" );
    jQuery("td:contains('suprespect')" ).text( "Supervisor Treats You With Respect?" );
    jQuery("td:contains('supfair')" ).text( "Supervisor Treats Everyone Fairly?" );

});

Qualtrics.SurveyEngine.addOnUnload(function()
{
    /*Place your JavaScript here to run when the page is unloaded*/

});