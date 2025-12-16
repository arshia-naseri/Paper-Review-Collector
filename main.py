import openreview.api as openreview_api
import os, shutil, json, openreview

'''. ONLY set TRUE When not on your LOCAL machine (MASSIVE FILE SIZES), 
also check the function to remove the railguard  '''
wantPDFs = False

venue_invitations_url = {
  'iclr_2016': 'ICLR.cc/2016/workshop/-/submission',
  'iclr_2017': 'ICLR.cc/2017/conference/-/submission',
  'iclr_2018': 'ICLR.cc/2018/Conference/-/Blind_Submission',
  'iclr_2019': 'ICLR.cc/2019/Conference/-/Blind_Submission',
  'iclr_2020': 'ICLR.cc/2020/Conference/-/Blind_Submission',
  'iclr_2021': 'ICLR.cc/2021/Conference/-/Blind_Submission',
  'iclr_2022': 'ICLR.cc/2022/Conference/-/Blind_Submission',
  'iclr_2023': 'ICLR.cc/2023/Conference/-/Blind_Submission',
  'iclr_2024': 'ICLR.cc/2024/Conference/-/Submission',
  'iclr_2025': 'ICLR.cc/2025/Conference/-/Submission',
  'neurips_2019': 'NeurIPS.cc/2019/Reproducibility_Challenge/-/Blind_Report',
  'neurips_2021': 'NeurIPS.cc/2021/Conference/-/Blind_Submission',
  'neurips_2022': 'NeurIPS.cc/2022/Conference/-/Blind_Submission',
  'neurips_2023': 'NeurIPS.cc/2023/Conference/-/Submission',
  'neurips_2024': 'NeurIPS.cc/2024/Conference/-/Submission',
  'neurips_2025': 'NeurIPS.cc/2025/Conference/-/Submission'
}

def get_pdf_markdown(pdf_url):
    ''' 
        !!! This is a SAFTEY return, DO NOT Run this function
        I REPEAT, DO NOT run this function on local 
    '''
    # return 
    from markitdown import MarkItDown
    from io import BytesIO
    import requests

    if not(pdf_url): return
    response = requests.get(pdf_url)
    pdf_bytes = response.content

    md = MarkItDown()

    result = md.convert(BytesIO(pdf_bytes), mime="application/pdf")

    return result.text_content
def getAttr(paper,**attrs:str):
    def go_deep(node,paths):
        if not(node): return node
        if len(paths) == 1:
            return node.get(paths[0])
        return go_deep(node.get(paths[0]), paths[1:])

    results = {}
    for key, values in attrs.items():
        paths = values.split(":")
        results[key] = go_deep(paper, paths)
    return results
def paperCleaner(paper, specialCase = '',doCleanString = True):
    # Since some might have style in text 
    def cleanString(s):
        return ''.join(c for c in s if c.isascii() and c != '\n')

    cp_paper = paper.copy()

    # Reviews
    reviews = []
    decision = None
    for reviewItem in paper.get("reviews"):
        ''' 
            Some have "invitations" and others have "invitation" 
            ==> make everything "invitation" for easier conditions
        '''
        puralVal = reviewItem.get("invitations")
        if puralVal: reviewItem["invitation"] = puralVal

        # Decisions
        if not decision:
            if specialCase == "iclr_2019":
                decision = getAttr(reviewItem, decision = "content:recommendation")["decision"]
            elif specialCase in ["iclr_2024", "iclr_2025", "neurips_2023", "neurips_2024", "neurips_2025"]:
                decision = getAttr(reviewItem, decision = "content:decision:value")["decision"]
            else:      
                decision = getAttr(reviewItem, decision = "content:decision")["decision"]
        
        # Reviews
        if specialCase in ["iclr_2024", "iclr_2025", "neurips_2023", "neurips_2024", "neurips_2025"]:
            if "meta" in ",".join(i.lower() for i in reviewItem["invitation"]):
                continue
            if "review" in ",".join(i.lower() for i in reviewItem["invitation"]):
                
                result = "\n".join(
                (
                    # v is a list of objects
                    f"{k}:{cleanString(','.join(str(item['value']) for item in v))}"
                    if (doCleanString and isinstance(v, list))
                    else f"{k}:{', '.join(str(item['value']) for item in v)}"
                ) if isinstance(v, list)
                else (
                    # v is a single object
                    f"{k}:{cleanString(str(v['value']))}"
                    if doCleanString
                    else f"{k}:{str(v['value'])}"
                )
                for k, v in reviewItem["content"].items())
                
                date = reviewItem["cdate"] if reviewItem.get("cdate") else reviewItem.get("tcdate")
                reviewObj = {"date": date,"review": result}
                reviews.append(reviewObj)

        elif "review" in reviewItem["invitation"].lower():
            if specialCase in ["iclr_2019","neurips_2022"] and ("meta" in reviewItem["invitation"].lower()):
                continue
            result = "\n".join(
                f"{k}:{cleanString(','.join(v)) if (doCleanString and isinstance(v, list)) else cleanString(v) if doCleanString else v}"
                for k, v in reviewItem["content"].items()
            )

            date = reviewItem["cdate"] if reviewItem.get("cdate") else reviewItem.get("tcdate")
            reviewObj = {"date": date,"review": result}
            reviews.append(reviewObj)
        
    del cp_paper["reviews"]

    cp_paper["reviews"] = reviews
    cp_paper["decision"] = decision
    cp_paper["has_revisions"] = True if cp_paper["original_paper_id"] else False
    if cp_paper.get("pdf_url"):
        cp_paper["pdf_url"] = "https://openreview.net" + cp_paper["pdf_url"]
    else:
        cp_paper["pdf_url"] = None
    return cp_paper
# def print_results(directory_path):
#     # Check if directory exists
#     if not os.path.isdir(directory_path):
#         print(f"Error: '{directory_path}' is not a valid directory.")
#         return

#     for filename in os.listdir(directory_path):
#         file_path = os.path.join(directory_path, filename)
        
#         if os.path.isfile(file_path):
#             size_bytes = os.path.getsize(file_path)

#             if size_bytes < 1024:
#                 readable = f"{size_bytes} B"
#             elif size_bytes < (1024 ** 2):
#                 readable = f"{size_bytes / 1024:.2f} KB"
#             elif size_bytes < (1024 ** 3):
#                 readable = f"{size_bytes / (1024 ** 2):.2f} MB"
#             else:
#                 readable = f"{size_bytes / (1024 ** 3):.2f} GB"

#             print(f"{filename} — {readable}")
from tabulate import tabulate
import os

def print_results(directory_path):
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a valid directory.")
        return

    table = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                readable = f"{size_bytes} B"
            elif size_bytes < (1024 ** 2):
                readable = f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < (1024 ** 3):
                readable = f"{size_bytes / (1024 ** 2):.2f} MB"
            else:
                readable = f"{size_bytes / (1024 ** 3):.2f} GB"
            table.append([filename, readable])

    print(tabulate(table, headers=["File", "Size"], tablefmt="fancy_grid"))

def save_json(data, file_name: str, convert: bool = True) -> None:
    serializable = convert_2_json(data) if convert else data
    with open(f"{file_name}.json", "w") as fh:
        json.dump(serializable, fh, indent=4)
def convert_2_json(item):
    if hasattr(item, "to_json"):
        payload = dict(item.to_json())
        if getattr(item, "details", None) is not None:
            payload["details"] = item.details
        return payload
    if isinstance(item, list):
        return [convert_2_json(x) for x in item]
    if isinstance(item, dict):
        return {k: convert_2_json(v) for k, v in item.items()}
    return item

if os.path.exists("out") and os.path.isdir("out"):
    shutil.rmtree("out")
os.makedirs("out")

for venueName, invite_url in venue_invitations_url.items():
    [venue_name , venue_year] = venueName.split("_")
    print(f"> Retriving papers from venue {venue_name.upper()} year {venue_year}")
    # API 2
    client = openreview_api.OpenReviewClient(baseurl="https://api2.openreview.net")
    notes = client.get_all_notes(invitation = invite_url, details="directReplies,revisions")
    if len(notes) == 0:
        # API 1
        client = openreview.Client(baseurl="https://api.openreview.net")
        notes = client.get_all_notes(invitation = invite_url, details="directReplies,revisions")
    papers = convert_2_json(notes)

    with open(f"out/{venueName.upper()}.jsonl","w") as f:
      for paper in papers:
          if venueName in ["iclr_2024","iclr_2025","neurips_2023","neurips_2024","neurips_2025"]:
            new_paper = getAttr(paper, id = "id" , 
                                title = "content:title:value", pdf_url = "content:pdf:value", has_revisions= "details:revisions",
                                authors = "content:authors:value", created_date = "cdate", original_paper_id = "original", 
                                reviews = "details:directReplies", invitation = "invitations"
                                )
          else:
            new_paper = getAttr(paper, id = "id" , 
                                title = "content:title" , pdf_url = "content:pdf", has_revisions= "details:revisions", 
                                authors = "content:authors", created_date = "cdate" , original_paper_id = "original",
                                reviews = "details:directReplies", invitation = "invitation"
                                )

          new_paper = paperCleaner(new_paper,venueName)

        #   To get markdown of pdfs
          if wantPDFs:
              new_paper["pdf"] = get_pdf_markdown(new_paper.get("pdf_url"))
          f.write(json.dumps(new_paper) + "\n")
          break
          
print("---------------------")
print("\n✓ All Jobs Done ✓")
print("=========== File Sizes Generated =========")
print_results("out")