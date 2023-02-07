import openai
import json
import requests
import configparser

import datetime

config = configparser.ConfigParser()
config.read('config.ini')

api_key = config['DEFAULT']['api_key']
openai.api_key = api_key

# Define the text to be analyzed
prompt = """请理解下面给出的信息，并给出各条内容的title、URL和summary。结果以json显示，key用英文，value尽量使用中文。信息："""

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
root.geometry("400x200")

label = tk.Label(root, text="Enter text:")
label.pack()

text = tk.Text(root, height=10, width=40)
text.pack()

def on_button_click():
    contents = text.get("1.0", "end")
    print(contents)
    response = openai.Completion.create(
              model="text-davinci-003",
              prompt=prompt+contents,
              max_tokens=500,
              temperature=0
            )

    print(response)


    result_json = response["choices"][0]["text"]


    with open("temp.txt","w") as f:
        f.write(result_json)

    # with open("temp.txt","r") as f:
    #     result_json = f.read()

    result = json.loads(result_json)
    print(result)

    #notion row
    today = datetime.datetime.today()
    date_str = today.strftime("%Y-%m-%d")
    new_row = {
        "Title": {"title": [{"text": {"content": result["title"]}}]},
        "URL": {"url": result["URL"]},
        "Summary":{"rich_text": [{"text": {"content": result["summary"]}}]},
        "Found_date": {'id': 'uj%7Dj', 'type': 'date', 'date': {'start': date_str}},
        "Tags": {'multi_select': [{ 'name': 'TAG_ME'}]}, 

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
    else:
        print("Failed to insert row")
        print(f"response is {response.text}")

button = tk.Button(root, text="Submit", command=on_button_click)
button.pack()

root.mainloop()
