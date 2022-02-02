Qualtrics.SurveyEngine.addOnload(function()
{
    console.log("embedded data setting");
    /*Place your JavaScript here to run when the page loads*/
    // First, we "unpack" the array vars we have, creating individual
    // vars for each row rather than a comma-separated string of all the data
    var names_list_str = "${e://Field/names_o1}";
    console.log("names_list: " + names_list_str);
    var orig_list_str = "${e://Field/orig_o1}";
    var vals_list_str = "${e://Field/vals_o1}";
    var disp_list_str = "${e://Field/disp_o1}";
    // Separate them into individual vals
    var names_list = names_list_str.split(",");
    var orig_list = orig_list_str.split(",");
    var vals_list = vals_list_str.split(",");
    var disp_list = disp_list_str.split(",");
    // And create new embedded data for them
    for (var row_index = 0; row_index < names_list.length; row_index++) {
        // Get the padded version of the row num
        var row_num = row_index + 1;
        var row_str = String(row_num).padStart(2, '0');
        var name_varname = "name_o1_r" + row_str;
        var name_value = names_list[row_index];
        Qualtrics.SurveyEngine.setEmbeddedData(name_varname, name_value);
        var orig_varname = "orig_o1_r" + row_str;
        var orig_value = orig_list[row_index];
        Qualtrics.SurveyEngine.setEmbeddedData(orig_varname, orig_value);
        var val_varname = "val_o1_r" + row_str;
        var val_value = vals_list[row_index];
        Qualtrics.SurveyEngine.setEmbeddedData(val_varname, val_value);
        var disp_varname = "disp_o1_r" + row_str;
        var disp_value = disp_list[row_index];
        Qualtrics.SurveyEngine.setEmbeddedData(disp_varname, disp_value);
    }
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

});

Qualtrics.SurveyEngine.addOnUnload(function()
{
    /*Place your JavaScript here to run when the page is unloaded*/

});