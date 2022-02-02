import argparse

preview_pdfs = [
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958911.pdf", #1
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958912.pdf", #2
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958913.pdf", #3
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958914.pdf", #4
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958915.pdf", # 5
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958916.pdf", # 6
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958918.pdf", # 7
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958920.pdf", # 8
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958922.pdf", # 9
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958924.pdf", # 10
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958926.pdf", # 11
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958929.pdf", # 12
    "https://cs.stanford.edu/~jjacobs3/pdb/DOC_0005958931.pdf", # 13
]

tab_index_str = """
<div id="page-wrap">
    <a name="tabs"></a>

    <div id="tabs">
        <div id="hiddenbatchid" style="display: none;">${batch_id}</div>

        <div id="hiddennumtasks" style="display: none;">${additional_tasks}</div>

        <div id="hiddenwage" style="display: none;">${offer_amt}</div>

        <div id="hiddendiv" style="display: none;">
            <ul>
                !li_list!
            </ul>
        </div>
"""

def gen_tab_index(first_tasks, second_tasks):
    html_str = tab_index_str
    # Start page num counter
    page_num = 1
    # Start li list
    li_list = ""
    # Page 1: Consent Form
    li_list += f"<li><a href=\"#tabs-{page_num}\">Consent Form</a></li>\n"
    page_num += 1
    # Page 2: Demographic Survey
    li_list += f"<li><a href=\"#tabs-{page_num}\">Demographic Survey</a></li>\n"
    page_num += 1
    # Start task num counter
    task_num = 1
    while task_num <= first_tasks:
        li_list += f"<li><a href=\"#tabs-{page_num}\">Page {page_num} (Task {task_num})</a></li>\n"
        page_num += 1
        task_num += 1
    # Now the Offer
    li_list += f"<li><a href=\"#tabs-{page_num}\">Additional Tasks Offer</a></li>\n"
    page_num += 1
    # And the second round tasks
    while task_num <= (first_tasks + second_tasks):
        li_list += f"<li><a href=\"#tabs-{page_num}\">Page {page_num} (Task {task_num})</a></li>\n"
        page_num += 1
        task_num += 1
    # Finished page
    li_list += f"<li><a href=\"#tabs-{page_num}\">Finished</a></li>\n"
    # Now replace the template
    html_str = html_str.replace("!li_list!", li_list)
    return html_str

def fill_header_template(template, total_pages, total_tasks):
    """
    Fill the template for a header, where we need to know the total number of
    pages and total number of tasks
    """
    html_str = template
    html_str = html_str.replace("!num_pages!", str(total_pages))
    html_str = html_str.replace("!num_tasks!", str(total_tasks))
    return html_str

def fill_static_template(template, page_num):
    """
    Template for a "static" page (like the demographic survey)
    """
    html_str = template
    html_str = html_str.replace("!page_num!",str(page_num))
    html_str = html_str.replace("!next_page!",str(page_num + 1))
    return html_str

def fill_task_template(template, page_num, task_num):
    """
    Template for a "dynamically-generated" page (like one of the task pages)
    """
    html_str = template
    html_str = html_str.replace("!page_num!",str(page_num))
    html_str = html_str.replace("!task_num!",str(task_num))
    html_str = html_str.replace("!next_page!",str(page_num + 1))
    return html_str

#def gen_one_stage(num_pages, task_name, task_template):
#    print(f"One stage with {num_pages} pages")
#    one_stage_html = ""
#    # IRB page
#    # page 1
#    one_stage_html += gen_task_html(page_num=1,tab_num=3,next_tab=4,last_tab=num_pages)
#    # second stage offer
#    one_stage_html += gen_offer_html(page_num=1,tab_num=4,next_tab=5)
#    # finished page
#    one_stage_html += gen_finished_html(tab_num=27)
#    # Save to .txt file
#    output_fpath = f"1stage_{num_pages}.html"
#    with open(output_fpath, "w", encoding='utf-8') as g:
#        g.write(one_stage_html)
#    return output_fpath

def load_template(task_name, template_name):
    with open(f"./templates/{task_name}/{template_name}.html", 'r', encoding='utf-8') as f:
        template_html = f.read()
    return template_html

def gen_preview_html(base_html):
    # Also a "preview" version, which just adds in <html>, <head>, etc.
    preview_start = """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Preview</title>
                <meta content="text/html;charset=utf-8" http-equiv="Content-Type">
                <meta content="utf-8" http-equiv="encoding">
            </head>
            <body>
            <script>
                var isPreview = true;
                //function turkGetParam(requestedVar, defaultVal) {
                //    if (requestedVar == "assignmentId") {
                //        return "previewassignment";
                //    } else {
                //        return "previewuser";
                //    }
                //}
            </script>
    """
    preview_end = """
            </body>
        </html>
    """
    preview_html = preview_start + base_html + preview_end
    # Also fill in the pdf urls
    for pdf_num in range(1,14):
        preview_html = preview_html.replace("${pdf" + str(pdf_num) + "}", preview_pdfs[pdf_num-1])
    return preview_html

def gen_two_stage(first_tasks, second_tasks, task_name, task_template):
    print(f"Two stage with {first_tasks} tasks in first round and {second_tasks} tasks in second round")
    total_tasks = first_tasks + second_tasks
    # 1 page for IRB, N pages for first round, offer page,
    # M pages for second round, then 1 final page telling them that they've completed the task
    # and with a submit button
    total_pages = 1 + first_tasks + 1 + second_tasks + 1
    two_stage_html = ""
    ### First, load the header and instructions sections
    # Header
    header_template = load_template(task_name, "header")
    two_stage_html += fill_header_template(header_template, total_pages, total_tasks)
    # Instructions
    # Since the instructions don't require any filling-in, we can just load the
    # "template" as regular html and not worry about calling any fill() functions
    instructions_html = load_template(task_name, "instructions")
    two_stage_html += instructions_html
    ### Main part: the tabs
    # Start with the tab index (necessary for the interface to work)
    two_stage_html += gen_tab_index(first_tasks, second_tasks)
    cur_page = 1
    cur_task_num = 1
    # IRB notice (page 1)
    irb_template = load_template(task_name, "irb")
    two_stage_html += fill_static_template(irb_template, cur_page)
    cur_page += 1
    # Demographic Survey (page 2)
    demographic_template = load_template(task_name, "demographic")
    two_stage_html += fill_static_template(demographic_template, cur_page)
    cur_page += 1
    # First stage of tasks (starting at page 3)
    last_page_first_stage = cur_page + first_tasks - 1
    while cur_page <= last_page_first_stage:
        cur_page_html = fill_task_template(task_template, cur_page, cur_task_num)
        two_stage_html += cur_page_html
        cur_page += 1
        cur_task_num += 1
    # second stage offer
    offer_template = load_template(task_name, "offer")
    two_stage_html += fill_static_template(offer_template, cur_page)
    cur_page += 1
    # Second stage tag panels
    last_page_second_stage = cur_page + second_tasks - 1
    while cur_page <= last_page_second_stage:
        cur_page_html = fill_task_template(task_template, cur_page, cur_task_num)
        two_stage_html += cur_page_html
        cur_page += 1
        cur_task_num += 1
    # finished page
    finished_template = load_template(task_name, "finished")
    two_stage_html += fill_static_template(finished_template, cur_page)
    # Quick 1-line script to differentiate production version from preview
    production_html = two_stage_html
    preview_html = two_stage_html
    production_html += "<script>\nvar isPreview = false;\n</script>\n"
    # And the footer, which (importantly!) needs to close any divs opened in the header
    # But also should be plain html, nothing to fill in
    footer_html = load_template(task_name, "footer")
    production_html += (footer_html + "\n")
    preview_html += (footer_html + "\n")
    # Save to .txt file
    output_fpath = f"{task_name}_2stage_{first_tasks}_{second_tasks}.html"
    with open(output_fpath, "w", encoding='utf-8') as g:
        g.write(production_html)
    # Also a preview version
    preview_html_final = gen_preview_html(preview_html)
    preview_fpath = output_fpath.replace(".html","_preview.html")
    with open(preview_fpath, 'w', encoding='utf-8') as g:
        g.write(preview_html_final)
    return output_fpath

def main():
    # Default setting, can be changed
    task_name = "pdb"
    # Parse command-line args
    parser = argparse.ArgumentParser(description='Generate html code for the monopsony tests.')
    parser.add_argument('--one', type=int, nargs=1, help='number of tasks')
    parser.add_argument('--two', type=int, nargs=2, help='number of tasks for first stage, then number of tasks for second stage')
    args = parser.parse_args()
    #print(args.accumulate(args.integers))
    with open(f"./templates/{task_name}/task.html", 'r', encoding='utf-8') as f:
        task_template = f.read()
    #if args.one:
    #    print(args.one[0])
    #    output_fpath = gen_one_stage(args.one[0], task_name, task_template)
    if args.two:
        print(args.two[0], args.two[1])
        output_fpath = gen_two_stage(args.two[0], args.two[1], task_name, task_template)
    print(f"Generated html saved to {output_fpath}")

if __name__ == "__main__":
    main()