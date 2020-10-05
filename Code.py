# -*- coding: utf-8 -*-
"""
Created on Sat Oct  3 21:01:07 2020

@author: Akalank
"""

### Importing necessary modules

import pandas as pd
import re
import datetime
from matplotlib import pyplot as plt
import string
import pickle

### Making the database

## Reading data
chath = open("Data.txt", encoding = 'utf8')
chat = chath.read()


df = pd.DataFrame()


## Going through each message and storing it as a row in the dataframe "df"
while True:
    
    # Matching the timestamp and storing it
    temp = re.search("[0-9][0-9]/[0-9][0-9]/[0-9][0-9],\s[0-9]+:[0-9][0-9]\s[ap]m", chat)
    timestamp = temp[0]
    timestamp = timestamp.replace("pm", "PM")
    timestamp = datetime.datetime.strptime(timestamp, "%d/%m/%y, %I:%M %p")
    chat = chat[temp.span()[1]+3:] # "Moving" past the extracted string 
    
        
    # Some messages contain subject change information, of the form:
    # x changed the subject from " " to " "
    # we don't need these messages; they mess up data extraction since 
    # they have no sender id
    
    temp = chat[:35]
    if temp.find(":") == -1:
            temp = re.search("[0-9][0-9]/[0-9][0-9]/[0-9][0-9],\s[0-9]+:[0-9][0-9]\s[ap]m", chat)
            temp = temp.span()[0]
            chat = chat[temp:]
            continue

    # Matching the sender and storing it
    temp = chat.find(":")
    sender = chat[:temp]
    chat = chat[temp+2:]
    
    
    # We want the contents of the message
    # The contents start from the beginning of the updated chat variable
    # ... and end at the beginning of the next timestamp
    
    # Finding the next timestamp
    temp = re.search("[0-9][0-9]/[0-9][0-9]/[0-9][0-9],\s[0-9]+:[0-9][0-9]\s[ap]m", chat)
    
    
    # If we're at the last message, we won't find a timestamp
    if temp == None:
        message = chat
    else:
        temp = temp.span()[0]
        message = chat[:temp]
        chat = chat[temp:]
    
    # Stripping whitespace
    message = message.strip()
    
    # Making a dictionary, and then using it to create a temporary dataframe
    temp_dict = {"Time" : timestamp, "Sender": sender, "Message": message}
    temp_df = pd.DataFrame(temp_dict, index = [0]) #Removing index = [0] will throw "If using all scalar values, you must pass an index" ValueError
    
    # Appending
    df = df.append(temp_df, ignore_index = True)
    
    # If the last temp = re.search(...) was "None", then we've reached the..
    # ..end of the .txt file
    if temp == None: 
        break

# We have a bunch of variables we don't need; let's get rid of them.
del chat, chath, message, sender, temp, temp_df, temp_dict, timestamp


# Let's strip off punctation from messages
punct = string.punctuation
punctma = punct.translate(punct.maketrans('','',"'")) #punctation minus apostrophe
df["Message2"] = df["Message"].apply(lambda x: x.translate(x.maketrans('','',punctma)))
df["Message2"] = df["Message2"].apply(lambda x: x.lower())

# Let's remove rows that have no alphabets (a-z)
# Before that let's define a function that returns True if a string contains alphabets
def anyalpha(string):
    for e in string:
        if e.isalpha():
            return True
    return False
        

i = 0
while i < len(df):
    print("Row:", i)
    if not anyalpha(df.iloc[i].Message2):
        df = df.drop(df.index[i])
        continue
    i = i + 1

df = df.reset_index(drop = True)        


# Media messages come up as "Media Omitted" - let's remove them too.

i = 0
while i < len(df):
    print("Row:", i)
    if not df.iloc[i].Message2.find("<media omitted>") == -1:
        df = df.drop(df.index[i])
        continue
    i = i + 1

df = df.reset_index(drop = True)        

    
# Let's remove all emojis and special characters except apostrophes (') which
# can occur in a word (Shan't.)

df["Message2"] = df["Message2"].apply(lambda x: re.sub("[^a-z'\s]", '', x))

# Cleaning done! Let's merge Message with Message2 and remove the redundant column

df["Message"] = df["Message2"]
del df["Message2"]

# Let's count each occurence of a word in every message and add store the
# information in a dictionary -- we'll use this to plot the most frequent words later

list_of_words = []
i = 0
while i < len(df):
    messages = df.iloc[i].Message.split()
    
    # Let us first remove apostrophes that are used as quotation marks - we didn't remove this earlier
    j = 0 
    while j < len(messages):
        apostrophe = messages[j].find("'")
        if apostrophe != -1:
            if apostrophe == len(messages[j]) - 1 or apostrophe == 0:
                messages[j] = messages[j].translate(messages[j].maketrans('','',"'"))
            
            else:
                if not (messages[j][apostrophe+1].isalpha() and messages[j][apostrophe-1].isalpha()):
                    messages[j] = messages[j].translate(messages[j].maketrans('','',"'"))
        j = j + 1
    
    list_of_words = list_of_words + messages
    i = i + 1 
    
# We have 159,131 words to count! But we'll have several words that are articles, prepositions, conjunctions etc.
# Let's remove them
trivial_words = ['to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'up', 'about', 'into','over','after','the','and','a','that','i','it','not','he','as','you','this','but','his','they','her','she','or','an','will','my','one','all','would','there','their', " ", "is", "have", "the", "no", "so", "me", "it's", "don't", "was", "yes", "are", "i'm", "we", "your", "media", "omitted", "be", "i", "now", "know", "why", "yeah", "am", "because", "did", "can", "na"]

i = 0 
while i < len(list_of_words):
    if list_of_words[i] in trivial_words:
        del list_of_words[i]
    i = i + 1

# We now have 124,479 words. Let's count them!

dictionary = dict()
for word in list_of_words:
    dictionary[word] = dictionary.get(word, 0) + 1

    
                
wordcount = pd.DataFrame(dictionary, index = [0])
wordcount = wordcount.transpose()
wordcount = wordcount.reset_index()
wordcount = wordcount.rename(columns = {'index':'Word', 0:'Count'})

# That's great -- but there's still a lot of trivial words that we haven't accounted for
# It may be better to specify our words of interest

wordsOfInterest = ["hahahahhaha", "yaar", "buddy", "class", "ugh", "hain", "face", "haina", "woohoo"]

dictionary = dict()
for word in list_of_words:
    if word in wordsOfInterest:
        dictionary[word] = dictionary.get(word, 0) + 1
   
                
wordcount = pd.DataFrame(dictionary, index = [0])
wordcount = wordcount.transpose()
wordcount = wordcount.reset_index()
wordcount = wordcount.rename(columns = {'index':'Word', 0:'Count'})



## Plots

# Great! We can use this dataframe to plot 
# Rename: Akalank - Mammoth, Haripriya - Gorilla, Ketaki - PolarBear, Vibhu - Panda


df.loc[df["Sender"] == "Akalank","Sender"] = "Mammoth"
df.loc[df["Sender"] == "Buddy!","Sender"] = "Gorilla"
df.loc[df["Sender"] == "Ketaki Sardeshpande","Sender"] = "Bear"
df.loc[df["Sender"] == "Vibhu Jain","Sender"] = "Panda"

plt.style.use("seaborn")

# Most frequent texter
ax = df.value_counts("Sender").plot(kind = "bar", rot = 45)
ax.set_ylabel("Message Count")
plt.tight_layout()
plt.savefig("Most Frequent Texter.png", dpi = 1200)

# Messages by day
bydate = df["Time"].apply(lambda x: x.date())
ax = bydate.value_counts().plot()
ax.set_ylabel("No. of messages sent")
ax.set_xlabel("Date")
plt.tight_layout()
plt.savefig("Messages sent by date.png", dpi = 1200)

# Messages by hour of the day
byhour = df["Time"].apply(lambda x: x.hour)
byhour = byhour.value_counts()
byhour = byhour.sort_index()
plt.plot(byhour)
plt.ylabel("No. of messages sent")
plt.xlabel("Hour")
plt.tight_layout()
plt.savefig("Messages sent by hour of day.png", dpi = 1200)

# Most used words
plt.barh(wordcount["Word"],wordcount["Count"])
plt.xlabel("Count")
plt.ylabel("Words")
plt.tight_layout()
plt.savefig("Most used words.png", dpi = 1200)