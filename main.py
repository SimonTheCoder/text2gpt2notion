# -*- coding: utf-8 -*-

import openai
import json
import requests
import configparser
import pyperclip
import datetime

#for installing packages
#pip install -r requirements.txt

USING_MODEL="gpt-3.5-turbo"

config = configparser.ConfigParser()
config.read('config.ini')

api_key = config['DEFAULT']['api_key']
openai.api_key = api_key

# Define the text to be analyzed
prompt = """根据信息给出各条内容的title、url和summary，title尽量简洁。结果以json给出，所有key用英文，summary的value尽量使用中文。如有多个结果放进array。忽略json以外内容。信息："""

# test_text = """• oss-security - double-free vulnerability in OpenSSH server 9.1:
# https://www.openwall.com/lists/oss-security/2023/02/02/2

#    ・ OpenSSH server 9.1中存在一个无需身份认证的double free漏洞，但考虑到权限限制和沙箱保护等因素其可利用性较差。 – keenan"""


#notion config
config = configparser.ConfigParser()
config.read('config.ini')

notion_api_key = config['DEFAULT']['notion_api_key']

# Replace YOUR_DATABASE_ID with the actual ID of your Notion database
database_id = config['DEFAULT']['notion_database_id']



import tkinter as tk

root = tk.Tk()
root.geometry("400x250")

label = tk.Label(root, text="Enter text:")
label.pack()

text = tk.Text(root, height=10, width=40)
text.pack()

def extract_json_objects(text):
    json_objects = []
    pos = 0
    while True:
        start = text.find('{', pos)
        if start == -1:
            break
        try:
            end = json.JSONDecoder().raw_decode(text[start:])[1] + start
            json_objects.append(json.loads(text[start:end]))
        except json.JSONDecodeError:
            pass
        pos = start + 1
    return json_objects

def remove_duplicates(lst):
    seen = set()
    result = []
    for d in lst:
        t = tuple(sorted(d.items()))
        if t not in seen:
            seen.add(t)
            result.append(d)
    return result


def on_button_click():
    contents = text.get("1.0", "end")
    print(contents)

    # prompt = """Summarize given content, output a json string like '[{"title":"title","url":"url1","summary":"summary1","tag":["tag1","tag2"]},{"title":"title2","url":"url2","summary":"summary2"}]'
    # And try to use Chinese in the summary object.
    # content:
    # """
    prompt = """Summarize given content, output a json string like '[{"title":"title","url":"url1","summary":"summary1","tag":["tag1","tag2"]},]'
    Try to use Chinese in the summary object. 
    Try to tag with this list of tags:[AI, vulnerable, tool, pager, reverse engineering, pentesting, web, binary ].
    content:
    """
    label.config(text="Calling openai...")

    if USING_MODEL == "gpt-3.5-turbo":
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt+contents}
            ]
        )

        print(response)
        result_json = response["choices"][0]["message"]["content"]

        
        with open("temp.txt","wb") as f:
            f.write(result_json.encode("utf-8"))

        # with open("temp.txt","rb") as f:
        #     result_json = f.read()

        result_list = extract_json_objects(result_json)
        #result_list = remove_duplicates(result_list)
    else:
        response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt+contents,
                max_tokens=2000,
                temperature=0
                )

        print(response)


        result_json = response["choices"][0]["text"]


        with open("temp.txt","wb") as f:
            f.write(result_json.encode("utf-8"))

        # with open("temp.txt","rb") as f:
        #     result_json = f.read()

        result_list = extract_json_objects(result_json)
        result_list = remove_duplicates(result_list)

    for result in result_list:
        print(result)

        #notion row
        today = datetime.datetime.today()
        date_str = today.strftime("%Y-%m-%d")

        tags = [{ 'name': 'TAG_ME'}]
        if result.get("tag") is not None:
            for tag in result.get("tag"):
                tags.append({'name':tag})

        new_row = {
            "Title": {"title": [{"text": {"content": result["title"]}}]},
            "URL": {"url": result["url"]},
            "Summary":{"rich_text": [{"text": {"content": result["summary"]}}]},
            "Found_date": {'id': 'uj%7Dj', 'type': 'date', 'date': {'start': date_str}},
            "Tags": {'multi_select': tags}, 

        }

        row_page_body = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": contents,
                            }
                        }
                    ]
                }
            }

        ]
        #print(json.dumps(new_row))
        label.config(text="Calling notion...")
        response = requests.post(
        "https://api.notion.com/v1/pages",
        headers={"Authorization": f"Bearer {notion_api_key}",'Notion-Version': '2022-06-28'},
        json={"parent": { "database_id": database_id },
            "properties": new_row,
            "children":row_page_body,
            }
        )

        # Check the response status code to see if the request was successful
        print(f"response is {response.status_code}")
        if response.status_code == 200:
            print("Row inserted successfully")
            label.config(text="OK. Enter new content:")
            #text.delete("1.0", tk.END)
        else:
            print("Failed to insert row")
            print(f"response is {response.text}")
            label.config(text=f"Failed: {response.text}")

button = tk.Button(root, text="Submit", command=on_button_click)
button.pack()

def paste_text():
    text_input = text
    content = pyperclip.paste()
    text_input.delete("1.0", tk.END)
    text_input.insert("1.0", content)
    on_button_click()

paste_button = tk.Button(root, text="Paste and Go", command=paste_text)
paste_button.pack()

root.mainloop()
