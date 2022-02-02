import sys

import pyperclip

table_head = """<div class="comparison">
<table class="UserTable" id="offtable">
 <thead>
  <tr id="tableheader">
   <th class="tl tl2">&nbsp;</th>
   <th class="compare-heading"><strong>${e://Field/cur_prev_cap}: ${e://Field/entered_jobtitle}</strong></th>
   <th class="compare-heading"><strong>Offered Job: ${e://Field/generated_jobtitle_!task_num!}<br></strong></th>
  </tr>
 </thead>
 <tbody>
 """

row_template = """<tr class="r!row_num!">
   <td>&nbsp;</td>
   <td colspan="2"><b>${e://Field/name_!task_num!_!row_num!}</b></td>
  </tr>
  <tr class="compare-row r!row_num!">
   <td><b>${e://Field/name_!task_num!_!row_num!}<br></b></td>
   <td>${e://Field/cur_!task_num!_!row_num!}</td>
   <td>${e://Field/val_!task_num!_!row_num!}</td>
  </tr>
  """
table_end = """</tbody>
</table></div>"""

table_js = """Qualtrics.SurveyEngine.addOnload(function()
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
	jQuery("td:contains('wage')" ).text( "Hourly Wage (USD)" ); //row 1
	jQuery("td:contains('hrsweek')" ).text( "Hours Per Week" ); //2
	jQuery("td:contains('controlhrs')" ).text( "Control Over Hours?" ); //3
	jQuery("td:contains('paidsick')" ).text( "Paid Sick Leave?" ); //4
	jQuery("td:contains('friends')" ).text( "Work With Friends?" ); //5
	jQuery("td:contains('commute')" ).text( "Daily Commute Time" ); //6
	jQuery("td:contains('physical')" ).text( "Intense Physical Activity?" ); //7
	jQuery("td:contains('skills')" ).text( "Learn Transferable Skills?" ); //8
    jQuery("td:contains('vaccine')").text( "Requires Vaccine?" ); //9
	jQuery("td:contains('express')" ).text( "Opportunities for Expression?" ); //10
	jQuery("td:contains('coworkers')" ).text( "Reliable Coworkers?" ); //11
	jQuery("td:contains('suprespect')" ).text( "Supervisor Treats You With Respect?" ); //12
	jQuery("td:contains('supfair')" ).text( "Supervisor Treats Everyone Fairly?" ); //13

});

Qualtrics.SurveyEngine.addOnUnload(function()
{
    /*Place your JavaScript here to run when the page is unloaded*/

});"""

def main():
    """
    Takes in two command-line args: the number of tasks, then the number of rows
    (i.e., number of characteristics to generate for each task)
    """
    num_tasks = int(sys.argv[1])
    num_rows = int(sys.argv[2])
    for task_num in range(1,num_tasks+1):
        cur_html = ""
        # Pad the task num
        task_num_str = str(task_num).zfill(2)
        cur_head = table_head.replace("!task_num!",task_num_str)
        cur_html = cur_html + cur_head
        # Generate the rows
        for row_num in range(1,num_rows + 1):
            row_num_str = str(row_num).zfill(2)
            cur_row_html = row_template.replace("!task_num!",task_num_str)
            cur_row_html = cur_row_html.replace("!row_num!",row_num_str)
            cur_html = cur_html + cur_row_html
        # And the tail (closing the html tags)
        cur_html = cur_html + table_end
        # Put it on the clipboard
        pyperclip.copy(cur_html)
        input(f"HTML code for Table {task_num} copied to clipboard. Press Enter to continue...")
        pyperclip.copy(table_js)
        input("Table JS code copied to clipboard. Press Enter to continue...")

if __name__ == "__main__":
    main()